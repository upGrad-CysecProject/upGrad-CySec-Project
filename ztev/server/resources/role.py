from flask_restful import Resource
from flask_restful import reqparse
from config import oidc, Session, logger
from models import *
from flask import Flask, request, jsonify
from flask import abort
from itertools import chain
import datetime
from jose import jwt
from utils import json_abort

class RoleGrantAPI(Resource):

  @oidc.require_login
  def get(self, id=None):
    session = Session()
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    username = oidc.user_getfield('username')
    if id is not None:
      grant = session.query(RoleGrant).get(id)
      if grant:
        if 'admin' not in roles and grant.topic.user != username:
          abort(403)
      logger.debug(grant)
      return jsonify(grant)
    else:
      if 'admins' in roles:
        grants = session.query(RoleGrant).all()
        return jsonify(grants)
      grants = session.query(RoleGrant, Topic).filter(RoleGrant.topic_id == Topic.id).filter(Topic.user == username).all()
      grants = [id for id,_ in grants]
      return jsonify(grants)

  @oidc.require_login
  def post(self):
    session = Session()
    username = oidc.user_getfield('username')
    kargs = request.get_json(silent=True)
    logger.debug(kargs)
    if not kargs.get('topic_id'):
        json_abort(400)
    topic = session.query(Topic).get(kargs['topic_id'])
    if not topic:
       json_abort(400)
    if not topic.user == username:
       json_abort(403) 
    grant = RoleGrant(
      **kargs 
    )
    session.add(grant)
    session.commit()
    logger.debug(grant)
    return jsonify(grant)

  @oidc.require_login
  def put(self, id):
    session = Session()
    username = oidc.user_getfield('username')
    grant = session.query(RoleGrant).get(id)
    kargs = request.get_json(silent=True)
    if kargs.get('id'):
        topic = session.query(Topic).get(kargs['topic_id'])
        if not topic.user == username:
           json_abort(403)
        grant.topic = topic
    if kargs.get('role'):
        grant.role = kargs.get('role')
    session.commit()
    logger.debug(grant)
    return jsonify(grant)

  @oidc.require_login
  def delete(self, id):
    session = Session()
    username = oidc.user_getfield('username')
    grant = session.query(RoleGrant).get(id)
    if not grant:
        json_abort(404)
    if not grant.topic.user == username:
        json_abort(403)
    session.delete(grant)
    session.commit()
    logger.debug(grant)
    return jsonify(grant)


