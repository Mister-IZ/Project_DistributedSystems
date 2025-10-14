# app.py
from flask import Flask, jsonify
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
    hostname = socket.gethostname()
    
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <title>Distributed Systems Demo</title>
      <style>
        * {{margin: 0; padding: 0; box-sizing: border-box;}}
        body {{
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: linear-gradient(160deg, #e0f7fa, #ffffff);
          color: #333;
          line-height: 1.6;
        }}

        header {{
          background: linear-gradient(90deg, #2196f3, #21cbf3);
          color: white;
          text-align: center;
          padding: 30px 20px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.2);
          position: sticky;
          top: 0;
          z-index: 100;
        }}

        header h1 {{
          font-size: 2.2em;
          letter-spacing: 1px;
        }}

        .container {{
          width: 90%;
          max-width: 1100px;
          margin: 40px auto;
          display: flex;
          flex-direction: column;
          gap: 30px;
        }}

        .frame {{
          background: #ffffff;
          border-radius: 15px;
          padding: 25px;
          box-shadow: 0 8px 20px rgba(0,0,0,0.1);
          transition: transform 0.3s;
        }}

        .frame:hover {{
          transform: translateY(-5px);
        }}

        h2 {{
          color: #2196f3;
          margin-bottom: 15px;
        }}

        .hostname {{
          font-size: 2rem;
          font-weight: bold;
          color: #ff5722;
          display: inline-block;
          margin-bottom: 15px;
          transition: all 0.5s;
        }}

        .hostname .last5 {{
          color: green;
        }}

        .info-box {{
          background: #e3f2fd;
          padding: 18px;
          border-radius: 10px;
          border-left: 5px solid #2196f3;
          margin-top: 10px;
          font-size: 0.95rem;
        }}

        ul {{
          list-style: none;
          padding-left: 0;
        }}

        li {{
          padding: 10px;
          margin-bottom: 5px;
          border-radius: 5px;
          background: #f0f4f8;
          transition: background 0.3s;
        }}

        li:hover {{
          background: #d0e7ff;
        }}

        footer {{
          text-align: center;
          padding: 20px;
          background: #2196f3;
          color: white;
          margin-top: 50px;
        }}

        .badge {{
          display: inline-block;
          background: #4caf50;
          color: white;
          padding: 3px 8px;
          border-radius: 5px;
          font-size: 0.85rem;
          margin-left: 8px;
        }}
      </style>
    </head>
    <body>

    <header>
      <h1>Distributed Systems Demo <span class="badge">Flask + MongoDB</span></h1>
    </header>

    <div class="container">

      <!-- Pod Hostname -->
      <div class="frame">
        <h2>Pod Hostname</h2>
        <div class="hostname-container">
          <span class="hostname" id="hostname">{hostname}</span>
        </div>
        <div class="info-box">
          Chaque pod dans Kubernetes possède un <strong>hostname unique</strong>.  
          Cette démo utilise <strong>Flask</strong> directement pour servir le contenu.  
          Quand vous rafraîchissez la page, vous pouvez observer que le hostname change en fonction du pod qui répond, ce qui illustre la <strong>répartition de charge</strong> entre plusieurs replicas.
          <br><br>
          <strong>ENVIRONMENT: Ici on est en TEST</strong> - On rebuild à partir de docker hub ✅
        </div>
      </div>

      <!-- MongoDB Hosts -->
      <div class="frame">
        <h2>Hosts from MongoDB</h2>
        <ul id="host-list"></ul>
        <div class="info-box">
          La base de données utilisée est <strong>MongoDB</strong>, déployée en <strong>StatefulSet</strong> avec 3 pods pour assurer la réplication des données.  
          Flask communique avec MongoDB via une API pour récupérer et afficher les données.  
          Les modifications effectuées sur le pod primaire sont automatiquement répliquées sur les pods secondaires, garantissant la <strong>haute disponibilité</strong> et la <strong>durabilité des données</strong>.
        </div>
      </div>

      <!-- How it Works -->
      <div class="frame">
        <h2>How This Works</h2>
        <div class="info-box">
          <ul>
            <li>Flask sert le contenu web et fournit une API REST pour interagir avec MongoDB.</li>
            <li>MongoDB est déployé en <strong>StatefulSet</strong> pour garantir l'identité persistante de chaque pod et la réplication des données.</li>
            <li>Chaque pod a un <strong>hostname unique</strong> affiché dans la page, permettant de visualiser quel pod répond à la requête.</li>
            <li>Cette démo montre comment un cluster Kubernetes gère la <strong>réplication</strong>, la <strong>disponibilité</strong> et l'<strong>affichage dynamique</strong> des données.</li>
            <li><strong>Dans TEST il y a un SYSTÈME D'AUTO-UPDATE</strong> : Les nouvelles versions sont déployées automatiquement en TEST toutes les 5 minutes.</li>
          </ul>
        </div>
      </div>

    </div>

    <footer>
      &copy; 2025 Distributed Systems Demo Project
    </footer>

    <script>
      // Format hostname (last 5 chars en vert)
      const span = document.getElementById('hostname');
      const text = span.textContent;
      if (text.length > 5) {{
        const firstPart = text.slice(0, -5);
        const last5 = text.slice(-5);
        span.innerHTML = `${{firstPart}}<span class="last5">${{last5}}</span>`;
      }}

      // Load MongoDB data via API
      async function loadData() {{
        try {{
          const response = await fetch('/hosts');
          const data = await response.json();
          const list = document.getElementById('host-list');
          list.innerHTML = '';
          data.forEach(item => {{
            const li = document.createElement('li');
            li.textContent = `${{item.pod}} (${{item.info}})`;
            list.appendChild(li);
          }});
        }} catch (e) {{
          document.getElementById('host-list').textContent = 'Error loading data or MongoDB not connected.';
        }}
      }}

      loadData();
    </script>

    </body>
    </html>
    '''

@app.route("/hosts")
def get_hosts():
    try:
        hosts = list(db.hosts.find({}, {"_id": 0}))
        return jsonify(hosts)
    except Exception as e:
        return jsonify([{"pod": "Error", "info": f"MongoDB connection failed: {str(e)}"}])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)