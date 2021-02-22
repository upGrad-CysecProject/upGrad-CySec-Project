from flask_restful import Resource
from flask_restful import reqparse
from config import oidc, Session, logger
from models import *
from flask import Flask, request, jsonify, redirect
from flask import abort
from itertools import chain
import datetime
from jose import jwt
from utils import json_abort


class VoteAPI(Resource):
   
  @oidc.require_login
  def post(self):
    session = Session()
    username = oidc.user_getfield('username')
    roles = oidc.user_getfield('cognito:groups') if oidc.user_getfield('cognito:groups') else []
    kargs = request.get_json(silent=True)
    logger.debug(kargs)
    vote_jwt = kargs.get('vote')
    if not vote_jwt:
      json_abort(400, "Vote missing")
    if not oidc.is_api_request():
      json_abort(403)
    secret = oidc.get_access_token().split('.')[-1] 
    payload = jwt.decode(vote_jwt, secret, algorithms=['HS256'])
    fields = ['token', 'topic_id', 'option_id']
    for field in fields:
      if not payload.get(field):
        json_abort(400, "%s missing in token" % field)
    topic_id = payload.get('topic_id')
    topic = session.query(Topic).get(topic_id)
    if not topic:
      json_abort(404, description="Topic not found")
    now = datetime.datetime.now()
    if topic.start_time > now and topic.end_time < now:
      json_abort(400, description="Voting not begun yet")
    mapper = session.query(Mapper).filter(Mapper.topic_id == topic_id).filter(Mapper.user == username).all()
    if mapper:
      json_abort(409)
    invite = session.query(Invite).filter(Invite.topic_id == topic_id).filter(Invite.role.in_(roles)).all()
    if not invite and topic.user != username:
      json_abort(403)
    vote = Vote(
       topic_id = payload['topic_id'],
       option_id = payload['option_id'],
       token = payload['token']
    )
    mapper = Mapper(
      user = username,
      topic_id = topic_id
    )
    session.add(vote)
    session.add(mapper)
    session.commit()
    logger.debug(vote)
    return jsonify(vote)


