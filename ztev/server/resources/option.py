from flask_restful import Resource
from flask_restful import reqparse
from config import oidc, Session, logger
from models import *
from flask import Flask, request, jsonify, redirect
from flask import abort
from itertools import chain
import datetime
from jose import jwt
from flask_restful import fields, marshal, url_for
from flask import render_template
import json
from config import api
from utils import json_abort

class TopicOptionAPI(Resource):

  @oidc.require_login
  def get(self, topic_id, id=None):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    topic = session.query(Topic).get(topic_id)
    grant = session.query(RoleGrant).filter(RoleGrant.topic_id == topic_id).filter(RoleGrant.role.in_(roles)).all() 
    invite = session.query(Invite).filter(Invite.topic_id == topic_id).filter(Invite.role.in_(roles)).all() 
    now = datetime.datetime.now()
    if not topic:
       abort(404, "Topic does not exist") 
    if 'admin' not in roles and not grant and topic.user != username:
      if not invite:
        abort(403, 'You do not have privilege to either vote or edit this topic')
      else:
        method = "GET"
    else:
        if now < topic.start_time:
          method = "PUT"
        else:
          method = "GET"
    if id is not None:
      if id == 0:
        if not oidc.is_api_request():
          editables = TopicOption.get_form_fields()
          url = url_for('api_topic', id=topic_id)
          return render_template(
                            'option.html', topic=topic, option=None, colnames=editables, 
                            editables=editables, method="POST", url=url)
      option = session.query(TopicOption).get(id)
      if not option:
        abort(404, "Option not found")
      logger.debug(option.to_dict())
      if not oidc.is_api_request():
         columns = TopicOption.get_default_fields()
         editables = TopicOption.get_editable_fields()
         url = url_for('api_option', topic_id=int(topic_id), id=int(id))
         return render_template(
                      'option.html', topic=topic, option=option, colnames=columns,
                       editables=editables,  url=url, method=method)
      return jsonify(option)
    else:
      if 'admin' not in roles and not grant and topic.user != username:
        method = 'GET'
      else:
        method = 'PUT'
      topic = session.query(Topic).get(id)
      logger.debug(topic.to_dict())
      options = session.query(TopicOption).filter(TopicOption.topic_id == topic_id)
      if not oidc.is_api_request():
         columns = Topic.get_default_fields()
         optioncols = TopicOption.get_default_fields()
         editables = Topic.get_editable_fields()
         url = url_for('api_topic', id=int(id))
         return render_template(
                      'topic.html', topic=topic, options=options, colnames=columns,
                       editables=editables, optioncols=optioncols, url=url,
                       method=method)
      return jsonify(topics)

  @oidc.require_login
  def post(self, topic_id):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    if not kargs.get('desc'):
      json_abort(400, "desc missing")
    topic = session.query(Topic).get(topic_id)
    if not topic:
      json_abort(404)
    now = datetime.datetime.now()
    if topic.start_time <= now:
      json_abort(403, "Voting already started. No changes allowed")
    grant = session.query(RoleGrant).filter(RoleGrant.topic_id == topic_id).filter(RoleGrant.role.in_(roles)).all()
    logger.debug("{}, {}, {}".format(topic.user, username, topic.user != username))
    if topic.user != username and 'admin' not in roles and not grant:
      json_abort(403) 
    option = TopicOption(
      **kargs 
    )
    option.topic_id = topic_id
    session.add(option)
    session.commit()
    logger.debug(option.to_dict())
    session = Session()
    if not oidc.is_api_request():
       url = url_for('api_topic', id=topic_id)
       data = { "url": url, "message": "Success. Redirecting to %s" % url }         
       return jsonify(data) 
    return jsonify(option)

  @oidc.require_login
  def put(self, topic_id, id):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    if not kargs.get('desc'):
      json_abort(400, "desc missing")
    topic = session.query(Topic).get(topic_id)
    if not topic:
      json_abort(404, "Topic doesn't exist")
    now = datetime.datetime.now()
    if topic.start_time <= now:
      json_abort(403, "Voting already started. No changes allowed")
    grant = session.query(RoleGrant).filter(RoleGrant.topic_id == topic_id).filter(RoleGrant.role.in_(roles)).all() 
    if 'admin' not in roles and not grant and topic.user != username:
      json_abort(403) 
    option = session.query(TopicOption).get(id) 
    if kargs.get('desc'):
      option.desc = kargs.get('desc')
    session.add(option)
    session.commit()
    logger.debug(option.to_dict())
    session = Session()
    if not oidc.is_api_request():
       url = url_for('api_topic', id=topic_id)
       data = { "url": url, "message": "Success. Redirecting to %s" % url }         
       return jsonify(data) 
    return jsonify(option)

  @oidc.require_login
  def delete(self, topic_id, id):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    topic = session.query(Topic).get(topic_id)
    if not topic:
      json_abort(404, "Topic doesn't exist")
    now = datetime.datetime.now()
    if topic.start_time <= now and now <= topic.end_time:
      json_abort(403, "Voting already started. No changes allowed")
    grant = session.query(RoleGrant).filter(RoleGrant.topic_id == topic_id).filter(RoleGrant.role.in_(roles)).all() 
    if 'admin' not in roles and not grant and topic.user != username:
      json_abort(403) 
    option = session.query(TopicOption).get(id) 
    session.delete(option)
    session.commit()
    logger.debug(option)
    return jsonify(option)


