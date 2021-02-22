from flask_restful import Resource
from flask_restful import reqparse
from config import oidc, Session
from models import *
from flask import Flask, request, jsonify, redirect
from flask import abort
from itertools import chain
import datetime
from jose import jwt
from flask_restful import fields, marshal, url_for
from flask import render_template
import json
from config import api, CLIENT_URL, logger
from utils import json_abort
from dateutil.parser import parse

class TopicAPI(Resource):
  
  @oidc.require_login
  def get(self, id=None):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    vote = False
    if id is not None:
      if id == 0:
         if not oidc.is_api_request():
           editables = Topic.get_form_fields()
           url = url_for('api_topics')
           return render_template('topic.html', topic=None, colnames=editables, editables=editables, method="POST", url=url) 
      topic = session.query(Topic).get(id)
      if not topic:
        abort(404)
      grant = session.query(RoleGrant).filter(RoleGrant.topic_id == id).filter(RoleGrant.role.in_(roles)).all()
      now = datetime.datetime.now()
      if 'admin' not in roles and not grant and topic.user != username:
        invite = session.query(Invite).filter(Invite.topic_id == id).filter(Invite.role.in_(roles)).all()
        if not invite:
          abort(403, 'You do not have privilege to either vote or edit this topic')
        method = 'GET'
      elif now > topic.start_time:
        method = 'GET'
      else:
        method = 'PUT'
      url = url_for('api_topic', id=int(id))
      topic = session.query(Topic).get(id)
      logger.debug(topic.to_dict())
      if topic.start_time <= now and now <= topic.end_time:
        voted = session.query(Mapper).filter(Mapper.user==username).filter(Mapper.topic_id==id).all()
        if not voted:
          vote = True
      if not oidc.is_api_request():
        options = session.query(TopicOption).filter(TopicOption.topic_id == id).all()
        invites = session.query(Invite).filter(Invite.topic_id == id).all()
        columns = Topic.get_default_fields()
        optioncols = TopicOption.get_form_fields()
        invitecols = Invite.get_form_fields()
        editables = Topic.get_editable_fields()
        if now > topic.end_time:
          votes = session.query(Vote).filter(Vote.topic_id == id).all()
          optioncols.append('vote_count')
          for option in options:
            count = session.query(Vote).filter(Vote.topic_id == id).filter(Vote.option_id == option.id).count()
            logger.debug("Vote count for {}: {}".format(option.id, count))
            option.vote_count = count 
          votecols = Vote.get_form_fields()
          return render_template(
                          'topic.html', topic=topic, options=options, colnames=columns, invites=invites,
                           editables=editables, optioncols=optioncols, invitecols=invitecols, 
                           method=method, url=url, vote=vote, votes=votes, votecols=votecols, 
                           client_url=CLIENT_URL)
        return render_template(
                      'topic.html', topic=topic, options=options, colnames=columns, invites=invites,
                       editables=editables, optioncols=optioncols, invitecols=invitecols, method=method, 
                       url=url, vote=vote, client_url=CLIENT_URL)
      return jsonify(topics)
    else:
      result = {'owned': {}, 'vote': {}, 'manage': {}}
      now = datetime.datetime.now()
      if 'admins' in roles:
        topics = session.query(Topic).all()
        return topics
      topics = session.query(Topic).filter(Topic.user==username)
      for topic in topics:
      	result['owned'][topic.id] = topic
      rows = session.query(RoleGrant).join(Topic).filter(RoleGrant.role.in_(roles)).filter(Topic.end_time >= now).all()
      for row in rows:
        result['manage'][row.topic.id] = row.topic
      rows = session.query(Invite).join(Topic).filter(Invite.role.in_(roles)).filter(Topic.end_time >= now).all()
      for row in rows:
        result['vote'][row.topic.id] = row.topic
      topics = {'Topics owned': list(result['owned'].values()), 'Topics to vote': list(result['vote'].values()), 'Topics to manage': list(result['manage'].values())}
      url = url_for('api_topics')
      if not oidc.is_api_request():
         columns = Topic.get_default_fields()
         return render_template('topics.html', topics=topics, colnames=columns, url=url)
      return jsonify(topics)

  @oidc.require_login
  def post(self):
    session = Session()
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    logger.debug(kargs)
    topic = Topic(
      **kargs 
    )
    now = datetime.datetime.now()
    minimum = datetime.timedelta(minutes=5)
    if (parse(topic.start_time, yearfirst=True) - now) < minimum:
      json_abort(400, "You can only create a topic with minimum 5 minute in advance.")
    if topic.start_time >= topic.end_time:
      json_abort(400, "End time can not be less than Start time.")
    topic.user = username
    session.add(topic)
    session.commit()
    logger.debug(topic.to_dict())
    session = Session()
    if not oidc.is_api_request():
      url = url_for('api_topic', id=int(topic.id))
      data = { "url": url, "message": "Success. Redirecting to %s" % url }         
      return jsonify(data) 
    return jsonify(topic)

  @oidc.require_login
  def put(self, id):
    session = Session()
    username = oidc.user_getfield('username')
    topic = session.query(Topic).get(id)
    if topic:
      now = datetime.datetime.now()
      if topic.start_time <= now and now <= topic.end_time:
        json_abort(403)
      if topic.user != username:
        json_abort(403)
      kargs = request.get_json(silent=True)
      logger.debug(kargs)
      fields = Topic.get_form_fields()
      for field in fields:
         if kargs.get(field):
            setattr(topic, field, kargs[field])
      now = datetime.datetime.now()
      minimum = datetime.timedelta(minutes=5) 
      if kargs.get('start_time') and (parse(kargs.get('start_time'), yearfirst=True) - now) < minimum:
        json_abort(400, "You can't edit a topic 5 minutes before start.")
      if topic.start_time >= topic.end_time:
        json_abort(400, "End time can not be less than Start time.")
      session.commit()
      if not oidc.is_api_request():
        url = url_for('api_topic', id=int(id))
        data = { "url": url, "message": "Success. Redirecting to %s" % url }
        return jsonify(data) 
    return jsonify(topic)

  @oidc.require_login
  def delete(self, id):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    topic = session.query(Topic).get(id)
    if topic:
      now = datetime.datetime.now()
      if now > topic.start_time:
        json_abort(403, "Voting started. Can't delete")
      if 'admin' not in roles:
        json_abort(403)
    topic = session.query(Topic).get(id)
    session.delete(topic)
    session.commit()
    logger.debug(topic.to_dict())
    if not oidc.is_api_request():
      url = url_for('api_topic', id=int(id))
      data = { "url": url, "message": "Success. Redirecting to %s" % url }
    return jsonify(topic)

