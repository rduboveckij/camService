__author__ = 'rduboveckij'

from flask import Flask, request, abort
from bson.objectid import ObjectId
from bson import DBRef
from flask.ext.pymongo import PyMongo
from utils import crossdomain
from random import randint
from datetime import datetime
from os import environ

app = Flask(__name__)
app.config['MONGO_HOST'] = 'ds063287.mongolab.com'
app.config['MONGO_PORT'] = 63287
app.config['MONGO_USERNAME'] = "rduboveckij"
app.config['MONGO_PASSWORD'] = "65538vy140"
app.config['MONGO_DBNAME'] = "cam"

mongo = PyMongo(app)
REST_GPO = ['GET', 'POST', 'OPTIONS']
REST_GDO = ['GET', 'DELETE', 'OPTIONS']


def checkRule(min, max, i, r1, r2, r3):
    if i <= min:
        return r1
    elif i > min and i < max:
        return r2
    elif i >= max:
        return r3
    return 0


def getDelOneBase(table_name, id):
    oid = ObjectId(id)
    if request.method == 'GET':
        return mongo.db[table_name].find_one(oid)
    elif request.method == 'DELETE':
        return mongo.db[table_name].remove(oid)


def getPostBase(table_name):
    if request.method == 'GET':
        return mongo.db[table_name].find()
    elif request.method == 'POST':
        return mongo.db[table_name].insert(request.json['content'])


@app.route("/list_precedents", methods=REST_GPO)
@crossdomain()
def listPrecedentController():
    return getPostBase("list_precedent")


@app.route("/list_precedents/<id>", methods=REST_GDO)
@crossdomain()
def listPrecedentControllerExtend(id):
    return getDelOneBase("list_precedent", id)


@app.route("/devices", methods=REST_GPO)
@crossdomain()
def deviceController():
    return getPostBase("device")


@app.route("/devices/<id>", methods=REST_GDO)
@crossdomain()
def deviceControllerExtend(id):
    return getDelOneBase("device", id)


@app.route("/platforms", methods=REST_GPO)
@crossdomain()
def platformController():
    return getPostBase("platform")


@app.route("/platforms/<id>", methods=REST_GDO)
@crossdomain()
def platformControllerExtend(id):
    return getDelOneBase("platforms", id)


@app.route("/type_parameters", methods=REST_GPO)
@crossdomain()
def typeParameterController():
    return getPostBase("type_parameter")


@app.route("/type_parameters/<id>", methods=REST_GDO)
@crossdomain()
def typeParameterControllerExtend(id):
    return getDelOneBase("type_parameters", id)


@app.route("/gen_test")
@crossdomain()
def test():
    cpuLoad = mongo.db.type_parameter.insert({"name": "CPULoad"})
    memoryLoad = mongo.db.type_parameter.insert({"name": "MemoryLoad"})
    energyLevel = mongo.db.type_parameter.insert({"name": "EnergyLevel"})
    device = mongo.db.device.insert({"name": "HTC ONE X"})
    platform = mongo.db.platform.insert({"name": 15})
    precedents = []
    for ic in range(0, 100, 15):
        date_update = datetime.utcnow()
        resC = checkRule(25, 75, ic, 2, randint(0, 1), -2)
        for im in range(50, 100, 10):
            resM = checkRule(70, 90, im, 1, randint(0, 2), -2)
            for ie in range(0, 100, 15):
                resE = checkRule(25, 75, ie, -3, randint(0, 1), 1)
                params = [ic / 100.0, im / 100.0, ie / 100.0]
                result = 1 if resC + resM + resE >= 0 else 0
                precedents.append({"_id": ObjectId(), "result": result, "params": params, "date": date_update})

    return mongo.db.list_precedent.insert(
        {"device": DBRef("device", device), "platform": DBRef("platform", platform), "date": date_update,
         "type_parameters": [DBRef("type_parameter", cpuLoad), DBRef("type_parameter", memoryLoad),
                             DBRef("type_parameter", energyLevel)], "precedents": precedents})


# CAM
@app.route("/precedents/<device_name>/<int:platform_name>/<last_update>")
@crossdomain()
def syncPrecedent(device_name, platform_name, last_update):
    device = mongo.db.device.find_one_or_404({"name": device_name})
    platform = mongo.db.platform.find_one_or_404({"name": platform_name})
    last_update_date = datetime.strptime(last_update, "%d%m%Y%H%M%S%f")

    result = mongo.db.list_precedent.aggregate([
        {"$match": {"platform.$id": platform["_id"], "device.$id": device["_id"],
                    "date": {"$gt": last_update_date}}},
        {"$unwind": "$precedents"},
        {"$project": {"_id": 0, "date": "$precedents.date", "result": "$precedents.result",
                      "parameters": "$precedents.params"}},
        {"$match": {"date": {"$gt": last_update_date}}}
    ])

    if result["result"].__len__() == 0:
        abort(404)
    return result


if __name__ == '__main__':
    port = int(environ.get("PORT", 5000))
    host = "127.0.0.1" if port == 5000 else "0.0.0.0"
    app.debug = True if port == 5000 else False
    app.run(host=host, port=port)
