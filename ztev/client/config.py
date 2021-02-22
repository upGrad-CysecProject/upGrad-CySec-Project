from flask import Flask, g, request
from flask_oidc_cognito import OpenIDConnect
from sqlitedict import SqliteDict
from flask_restful import Resource, Api
from flask import abort
from flask_bootstrap import Bootstrap
import logging
import os

app = Flask(__name__)
Bootstrap(app)
api = Api(app)

app.config.update({
    'SECRET_KEY': 'SomethingNotEntirelySecret',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'ztev-server',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_RESOURCE_SERVER_VALIDATION_MODE': 'offline',
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})

oidc = OpenIDConnect(app, credentials_store=SqliteDict('users.db', autocommit=True))


if os.environ.get('DEBUG', False):
    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1
    
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

logger = logging.getLogger('ztev_client')


