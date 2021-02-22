#!/usr/bin/env python
from flask import Flask, g, request, redirect, render_template, url_for
from flask_oidc_cognito import OpenIDConnect
from config import *
from jose import jwk, jwt
from jose.utils import base64url_decode
import os
import json
import time
import requests
import secrets
import hmac
import hashlib
import binascii

vote_server = os.environ.get('VOTE_SERVER', 'https://localhost:9999')



@app.route('/')
def home():
    if oidc.user_loggedin:
        return ('Hello, {email}. This client is only for voting. To see topcis to vote visit <a href="{vote_server}">{vote_server}</a> '
                '<br/><br/><a href="/logout">Log out</a>').format(
                        email=oidc.user_getfield('email'), 
                        vote_server=os.path.join(vote_server, 'topic/')
                 )
    else:
        g.oidc_token_info = None
        return 'Welcome anonymous, <a href="/login">Log in</a>'

@app.route('/login')
@oidc.require_login
def dashboard():
    """Example for protected endpoint that extracts private information from the OpenID Connect id_token.
       Uses the accompanied access_token to access a backend service.
    """
    logger.debug("In private")
    #info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    info = oidc.user_getinfo(['email', 'sub','name','cognito:groups', 'cognito:roles'])
    logger.debug(info)
    username = info.get('email')
    email = info.get('email')
    user_id = info.get('sub')
    greeting = "Hello %s" % username
    access_token = oidc.get_access_token()
    logger.debug('access_token=<%s>' % access_token)
    try:
        headers = {'Authorization': 'Bearer %s' % (access_token)}
        logger.debug(headers)
        greeting = requests.get('https://localhost:9999/token', headers=headers, verify=False).text 
    except Exception as e:
        logger.debug(e)
    return ("""%s your email is %s and your user_id is %s!
               <ul>
                 <li><a href="/">Home</a></li>
                 <li><a href="/setup">API</a></li>
                 <li><a href="/polls">API</a></li>
                 <li><a href="/vote?topic_id=1&option_id=1">API</a></li>
                </ul>""" %
            (greeting, email, user_id))


def setup_keys():
    """OAuth 2.0 protected API endpoint accessible via AccessToken"""
    if os.path.isfile("key.txt"):
       message = "Key already generated"
    else:
       secret = secrets.token_urlsafe(64)
       message = "Secret generated and saved in key.txt"
       with open("key.txt", "w") as fd:
           fd.write(secret)
    return json.dumps({'message': message})



@app.route('/vote', methods=['GET','POST'])
@oidc.require_login
def vote():
   print(request.headers)
   args = request.args
   topic_id = args.get("topic_id", 1)
   option_id = args.get("option_id", 1)
   if not os.path.isfile("key.txt"):
      setup_keys()
   with open("key.txt") as fd:
      key = fd.read()
   payload = {"topic_id": topic_id, "option_id": option_id, }
   vote_token = hmac.new(bytes(key, 'UTF-8'), bytes(json.dumps(payload), "UTF-8"), hashlib.sha256)
   token = oidc.get_access_token()
   logger.debug(token)
   logger.debug(type(token))
   if not isinstance(token, str) :
      return token
   access_token = token.split('.')[-1]
   payload["token"] = vote_token.hexdigest()
   payload["voted_on"] = time.time()
   logger.debug(payload)
   vote = jwt.encode(payload, access_token, algorithm="HS256")
   logger.debug(vote)
   headers = {
       "content-type": "application/json",
       "Authorization": "Bearer {}".format(token)
   }
   body = {"vote": vote, }
   topic_url = "{}/topic/{}".format(vote_server, topic_id)
   with requests.post(os.path.join(vote_server, "vote/"), headers=headers, data=json.dumps(body), verify=False) as response:
     if response.status_code == 200:
        message = "Voting successfully completed"
     else:
        message = "Error occured: {}: {}".format(response.status_code, response.json().get("message"))
     return render_template('vote.html', message=message, url=topic_url)

@app.route('/logout')
def logout():
    """Performs local logout by removing the session cookie."""
    oidc.logout()
    return 'Hi, you have been logged out! <a href="/">Return</a>'


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=True, port=8000, ssl_context=('cert.pem', 'key.pem'))
