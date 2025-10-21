from flask import Flask, jsonify
from pymongo import MongoClient
import redis
import json
import os
import socket

app = Flask(__name__)

# Connexion à MongoDB (via le service dans Kubernetes)
mongo_uri = "mongodb://mongo-0.mongo.dev.svc.cluster.local:27017,mongo-1.mongo.dev.svc.cluster.local:27017,mongo-2.mongo.dev.svc.cluster.local:27017/?replicaSet=rs0"
client = MongoClient(mongo_uri)
db = client["demoDB"]

# Connexion à Redis - avec fallback si Redis n'est pas disponible
try:
    redis_client = redis.Redis(
        host='redis-service.dev', 
        port=6379, 
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    redis_client.ping()  # Test connection
    redis_available = True
    redis_status = "✅ Redis Connecté"
except redis.ConnectionError:
    redis_available = False
    redis_status = "❌ Redis Non Connecté"

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

        .cache-indicator {{
          display: inline-block;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.8rem;
          margin-left: 8px;
          background: #4caf50;
          color: white;
        }}

        .cache-miss {{
          background: #ff9800;
        }}

        .cache-error {{
          background: #f44336;
        }}
      </style>
    </head>
    <body>

    <header>
      <h1>Distributed Systems Demo <span class="badge">Flask + MongoDB + Redis</span></h1>
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
          <strong>ENVIRONMENT: DEV</strong> - {redis_status}
        </div>
      </div>

      <!-- MongoDB Hosts avec Cache -->
      <div class="frame">
        <h2>Hosts from MongoDB <span id="cache-indicator" class="cache-indicator">Chargement...</span></h2>
        <ul id="host-list"></ul>
        <div class="info-box">
          <strong>Architecture avec Cache Redis:</strong><br>
          • <strong>Redis</strong> (2 replicas) - Cache en mémoire pour performances<br>
          • <strong>MongoDB</strong> (3 replicas) - Stockage persistant des données<br>
          • <strong>Flask</strong> - Logique métier avec fallback intelligent<br><br>
          
          <strong>Stratégie de Cache:</strong><br>
          ✅ Première requête → MongoDB → Stocke dans Redis (5min)<br>
          🚀 Requêtes suivantes → Redis (ultra-rapide)<br>
          🛡️ Si Redis down → Fallback automatique sur MongoDB
        </div>
      </div>

      <!-- Cache Performance -->
      <div class="frame">
        <h2>Cache Performance</h2>
        <div class="info-box">
          <div id="performance-stats">
            <p><strong>Temps de réponse:</strong> <span id="response-time">-</span></p>
            <p><strong>Source données:</strong> <span id="data-source">-</span></p>
            <p><strong>Statut Redis:</strong> <span id="redis-status">{redis_status}</span></p>
          </div>
          <br>
          <button onclick="clearCache()" style="padding: 8px 16px; background: #ff5722; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🗑️ Vider le Cache
          </button>
          <button onclick="loadData()" style="padding: 8px 16px; background: #2196f3; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">
            🔄 Recharger
          </button>
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

      // Load MongoDB data via API avec monitoring cache
      async function loadData() {{
        try {{
          const startTime = performance.now();
          const response = await fetch('/hosts');
          const endTime = performance.now();
          
          const data = await response.json();
          const list = document.getElementById('host-list');
          list.innerHTML = '';
          
          // Afficher les métriques de performance
          const responseTime = (endTime - startTime).toFixed(2);
          const cacheStatus = response.headers.get('X-Cache');
          const dataSource = cacheStatus === 'HIT' ? '🚀 Redis Cache' : '💾 MongoDB';
          
          document.getElementById('response-time').textContent = `${{responseTime}}ms`;
          document.getElementById('data-source').textContent = dataSource;
          
          // Mettre à jour l'indicateur cache
          const cacheIndicator = document.getElementById('cache-indicator');
          cacheIndicator.textContent = cacheStatus === 'HIT' ? 'CACHE' : 'DATABASE';
          cacheIndicator.className = cacheStatus === 'HIT' ? 'cache-indicator' : 'cache-indicator cache-miss';
          
          // Afficher les données
          data.forEach(item => {{
            const li = document.createElement('li');
            li.textContent = `${{item.pod}} (${{item.info}})`;
            list.appendChild(li);
          }});
          
        }} catch (e) {{
          document.getElementById('host-list').textContent = 'Error loading data.';
          document.getElementById('cache-indicator').textContent = 'ERROR';
          document.getElementById('cache-indicator').className = 'cache-indicator cache-error';
        }}
      }}

      // Vider le cache
      async function clearCache() {{
        try {{
          await fetch('/cache/clear');
          alert('Cache vidé ! Prochain chargement viendra de MongoDB.');
          loadData();
        }} catch (e) {{
          alert('Erreur lors du vidage du cache');
        }}
      }}

      // Charger les données au démarrage
      loadData();
    </script>

    </body>
    </html>
    '''

@app.route("/hosts")
def get_hosts():
    from flask import Response
    import time
    
    cache_hit = False
    start_time = time.time()
    
    try:
        # Essayer Redis d'abord
        if redis_available:
            cached_data = redis_client.get('hosts_data')
            if cached_data:
                cache_hit = True
                response = Response(cached_data, mimetype='application/json')
                response.headers['X-Cache'] = 'HIT'
                response.headers['X-Response-Time'] = f"{(time.time() - start_time)*1000:.2f}ms"
                return response
        
        # Fallback sur MongoDB
        hosts = list(db.hosts.find({}, {"_id": 0}))
        response_data = json.dumps(hosts)
        
        # Mettre en cache pour 5 minutes
        if redis_available:
            redis_client.setex('hosts_data', 300, response_data)
        
        response = Response(response_data, mimetype='application/json')
        response.headers['X-Cache'] = 'MISS'
        response.headers['X-Response-Time'] = f"{(time.time() - start_time)*1000:.2f}ms"
        return response
        
    except Exception as e:
        # Fallback complet en cas d'erreur
        hosts = list(db.hosts.find({}, {"_id": 0}))
        response = Response(json.dumps(hosts), mimetype='application/json')
        response.headers['X-Cache'] = 'ERROR'
        return response

@app.route("/cache/clear")
def clear_cache():
    """Endpoint pour vider le cache (pour les tests)"""
    try:
        if redis_available:
            redis_client.delete('hosts_data')
            return "✅ Cache cleared"
        return "❌ Redis not available"
    except:
        return "❌ Error clearing cache"

@app.route("/cache/status")
def cache_status():
    """Endpoint pour voir le statut du cache"""
    try:
        status = {
            "redis_available": redis_available,
            "cache_entries": redis_client.dbsize() if redis_available else 0,
            "cache_ttl": redis_client.ttl('hosts_data') if redis_available and redis_client.exists('hosts_data') else -1
        }
        return jsonify(status)
    except:
        return jsonify({"redis_available": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)