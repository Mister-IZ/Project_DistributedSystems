# app.py
from flask import Flask, jsonify, render_template
from pymongo import MongoClient
import os
import socket

app = Flask(__name__)

# Connexion à MongoDB (via le service dans Kubernetes)
mongo_uri = "mongodb://mongo-0.mongo.dev.svc.cluster.local:27017,mongo-1.mongo.dev.svc.cluster.local:27017,mongo-2.mongo.dev.svc.cluster.local:27017/?replicaSet=rs0"
client = MongoClient(mongo_uri)
db = client["demoDB"]

@app.route("/")
def home():
    return """
    <html>
    <body>
        <h1>🚀 TEST Environment - Auto-update WORKING!</h1>
        <p>Hostname: <strong>TEST-POD</strong></p>
        <p>✅ Auto-update system: <strong>OPERATIONAL</strong></p>
        <p>🎯 Ready for 14/10 demonstration!</p>
    </body>
    </html>
    """
    # return render_template("index.html")

@app.route("/hosts")
def get_hosts():
    hosts = list(db.hosts.find({}, {"_id": 0}))
    return jsonify(hosts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
