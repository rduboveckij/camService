__author__ = 'rduboveckij'
from datetime import timedelta
from flask import make_response, request, current_app, abort
from bson.json_util import dumps
from functools import update_wrapper


def DBPointer(collection, query, property=""):
    id = collection.find_one(query)
    if not property:
        property = collection.name
    return "{0}.$ref: {1}".format(property, collection.name), "{0}.$id: {1}".format(property, id['_id'])


def crossdomain(origin='*', methods="GET, POST, PUT, DELETE, OPTIONS",
                headers="origin, content-type, accept, x-requested-with, my-cool-header",
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                result = f(*args, **kwargs)
                if result is None:
                    result = {}
                    abort(404)
                resp = make_response(dumps(result))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator
