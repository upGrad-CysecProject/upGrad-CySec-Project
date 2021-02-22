#!/usr/bin/env python
from flask import Flask, g, request, redirect, render_template, url_for
from flask_oidc_cognito import OpenIDConnect
from config import *
from models import *
from resources.topic import TopicAPI
from resources.role import RoleGrantAPI
from resources.invite import InviteAPI
from resources.vote import VoteAPI
from resources.option import TopicOptionAPI
from jose import jwk, jwt
from jose.utils import base64url_decode
import os
import json
import time
import requests
import logging


#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

@app.route('/')
def home():
    return render_template('base.html')

@app.route("/dashboard")
@oidc.require_login
def dashboard():
    return render_template("dashboard.html")


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for(".dashboard"))

@app.route('/logout')
def logout():
    """Performs local logout by removing the session cookie."""
    oidc.logout()
    return 'Hi, you have been logged out! <a href="/">Return</a>'


def register_api(view, endpoint, url, pk='id', pk_type='int', methods=None):
    view_func = view.as_view(endpoint)
    view_func_all = view.as_view(endpoint+'s')
    if not methods:
      methods = ['GETALL', 'GET', 'POST', 'PUT', 'DELETE']
    if 'POST' in methods: 
      app.add_url_rule(url, view_func=view_func_all, methods=['POST',])
    if 'GET' in methods:
      app.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                      methods=['GET'])
    if 'GETALL' in methods:
      app.add_url_rule(url, defaults={pk: None},
                     view_func=view_func_all, methods=['GET',])
    if all(list(map(lambda x: x in methods, ['PUT', 'DELETE']))):
      app.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                     methods=['PUT', 'DELETE'])


#app.add_url_rule(AdminAPI, 'admin_api', '/admin/')
register_api(TopicOptionAPI, 'api_option', '/topic/<int:topic_id>/option/')
register_api(InviteAPI, 'api_invite', '/topic/<int:topic_id>/invite/')
register_api(TopicAPI, 'api_topic', '/topic/')
register_api(RoleGrantAPI, 'api_role_grant', '/role/')
register_api(VoteAPI, 'api_vote', '/vote/', methods=['POST', 'GET'])
#api.add_resource(ZEVM, '/')

 

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999, ssl_context=('cert.pem', 'key.pem'))
