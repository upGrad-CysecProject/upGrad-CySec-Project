from flask import Flask, request, jsonify, redirect
from flask import abort
from itertools import chain
import datetime
import json


def json_abort(status_code, description='There was an error', data=None):
    response = jsonify(data or {'message': description})
    response.status_code = status_code
    abort(response)
