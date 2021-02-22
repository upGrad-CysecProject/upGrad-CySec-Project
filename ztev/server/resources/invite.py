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


class InviteAPI(Resource):

  @oidc.require_login
  def get(self, topic_id, id=None):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    topic = session.query(Topic).get(topic_id)
    grant = session.query(RoleGrant).filter(RoleGrant.topic_id == topic_id).filter(RoleGrant.role.in_(roles)).all() 
    now = datetime.datetime.now()
    if not topic:
       abort(404, "Topic does not exist") 
    if 'admin' not in roles and not grant and topic.user != username:
        abort(403, 'You do not have privilege to either manage or edit this topic')
    else:
        if now < topic.start_time:
          method = "PUT"
        else:
          method = "GET"
    if id is not None:
      if id == 0:
        if not oidc.is_api_request():
          editables = Invite.get_form_fields()
          url = url_for('api_topic', id=topic_id)
          return render_template(
                            'invite.html', topic=topic, invite=None, colnames=editables, 
                            editables=editables, method="POST", url=url)
      invite = session.query(Invite).get(id)
      if not invite:
        abort(404, "Option not found")
      logger.debug(invite.to_dict())
      if not oidc.is_api_request():
         columns = Invite.get_default_fields()
         editables = Invite.get_editable_fields()
         url = url_for('api_invite', topic_id=int(topic_id), id=int(id))
         return render_template(
                      'invite.html', topic=topic, invite=invite, colnames=columns,
                       editables=editables,  url=url, method=method)
      return jsonify(invite)
    else:
      if 'admin' not in roles and not grant and topic.user != username:
        method = 'GET'
      else:
        method = 'PUT'
      topic = session.query(Topic).get(id)
      logger.debug(topic.to_dict())
      invites = session.query(Invite).filter(Invite.topic_id == topic_id)
      if not oidc.is_api_request():
         columns = Topic.get_default_fields()
         invitecols = Invite.get_default_fields()
         editables = Topic.get_editable_fields()
         url = url_for('api_topic', id=int(id))
         return render_template(
                      'topic.html', topic=topic, invites=invites, colnames=columns,
                       editables=editables, invitecols=invitecols, url=url,
                       method=method)
      return jsonify(topics)

  @oidc.require_login
  def post(self, topic_id):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    if not kargs.get('role'):
      json_abort(400, "role missing")
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
    invite = Invite(
      **kargs 
    )
    invite.topic_id = topic_id
    session.add(invite)
    session.commit()
    logger.debug(invite.to_dict())
    session = Session()
    if not oidc.is_api_request():
       url = url_for('api_topic', id=topic_id)
       data = { "url": url, "message": "Success. Redirecting to %s" % url }         
       return jsonify(data) 
    return jsonify(invite)

  @oidc.require_login
  def put(self, topic_id, id):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    if not kargs.get('role'):
      json_abort(400, "role missing")
    topic = session.query(Topic).get(topic_id)
    if not topic:
      json_abort(404, "Topic doesn't exist")
    now = datetime.datetime.now()
    if topic.start_time <= now:
      json_abort(403, "Voting already started. No changes allowed")
    grant = session.query(RoleGrant).filter(RoleGrant.topic_id == topic_id).filter(RoleGrant.role.in_(roles)).all() 
    if 'admin' not in roles and not grant:
      json_abort(403) 
    invite = session.query(Invite).get(id) 
    if kargs.get('role'):
      invite.role = kargs.get('role')
    session.add(invite)
    session.commit()
    logger.debug(invite.to_dict())
    session = Session()
    if not oidc.is_api_request():
       url = url_for('api_topic', id=topic_id)
       data = { "url": url, "message": "Success. Redirecting to %s" % url }         
       return jsonify(data) 
    return jsonify(invite)

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
    if 'admin' not in roles and not grant:
      json_abort(403) 
    invite = session.query(Invite).get(id) 
    session.delete(invite)
    session.commit()
    logger.debug(invite)
    return jsonify(invite)


