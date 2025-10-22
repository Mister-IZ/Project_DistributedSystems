from flask import Flask, jsonify
from pymongo import MongoClient
import redis
import json
import os
import socket

app = Flask(__name__)

# Configuration via variables d'environnement
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://mongo-mongos.dev.svc.cluster.local:27017/?directConnection=true')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service.dev')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

print(f"🔧 Configuration chargée:")
print(f"   - ENV: {ENVIRONMENT}")
print(f"   - MongoDB: {MONGODB_URI}")
print(f"   - Redis: {REDIS_HOST}")

# Connexion à MongoDB
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client["demoDB"]
    # Test connection CORRIGÉ (sans serverSelectionTimeoutMS dans la commande)
    client.admin.command('ping')
    mongodb_status = "✅ MongoDB Connecté"
    mongodb_available = True
    
    # Test supplémentaire pour déterminer le type de connexion
    try:
        config_db = client["config"]
        list(config_db.list_collections())  # Cette DB n'existe que dans le sharding
        mongodb_status += " (Sharding)"
    except:
        mongodb_status += " (Réplication)"
        
except Exception as e:
    mongodb_status = f"❌ MongoDB Erreur: {str(e)}"
    mongodb_available = False

# Connexion à Redis
try:
    redis_client = redis.Redis(
        host=REDIS_HOST, 
        port=6379, 
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    redis_client.ping()
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
      <title>Distributed Systems Demo - {ENVIRONMENT.upper()}</title>
      <style>
        /* [GARDE TOUT TON CSS EXISTANT] */
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
        .info-box {{
          background: #e3f2fd;
          padding: 18px;
          border-radius: 10px;
          border-left: 5px solid #2196f3;
          margin-top: 10px;
          font-size: 0.95rem;
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
        .cache-miss {{ background: #ff9800; }}
        .cache-error {{ background: #f44336; }}
        
        /* Nouveaux styles pour sharding */
        .architecture {{
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 20px;
          margin-top: 20px;
        }}
        .component {{
          background: #f8f9fa;
          padding: 15px;
          border-radius: 10px;
          border: 2px solid #e9ecef;
        }}
        .component h3 {{
          color: #495057;
          margin-bottom: 10px;
        }}
        .shard-active {{
          background: #d4edda;
          border-color: #c3e6cb;
        }}
        .shard-inactive {{
          background: #f8d7da;
          border-color: #f5c6cb;
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
          <strong>ENVIRONMENT: {ENVIRONMENT.upper()}</strong><br>
          MongoDB: {mongodb_status}<br>
          Redis: {redis_status}
        </div>
      </div>

      <!-- MongoDB Architecture -->
      <div class="frame">
        <h2>MongoDB Architecture</h2>
        <div class="architecture">
          <div class="component {'' if ENVIRONMENT == 'dev' else 'shard-inactive'}">
            <h3>🔧 Config Servers</h3>
            <p>Métadonnées du sharding</p>
            <ul>
              <li>mongo-config-0</li>
              <li>mongo-config-1</li>
              <li>mongo-config-2</li>
            </ul>
            <small>{'✅ Actif' if ENVIRONMENT == 'dev' else '❌ Inactif'}</small>
          </div>
          
          <div class="component {'' if ENVIRONMENT == 'dev' else 'shard-inactive'}">
            <h3>🗄️ Shard Servers</h3>
            <p>Données partitionnées</p>
            <ul>
              <li>mongo-shard-0</li>
              <li>mongo-shard-1</li>
              <li>mongo-shard-2</li>
            </ul>
            <small>{'✅ Actif' if ENVIRONMENT == 'dev' else '❌ Inactif'}</small>
          </div>
          
          <div class="component {'' if ENVIRONMENT == 'dev' else 'shard-inactive'}">
            <h3>🎯 Mongos Routers</h3>
            <p>Routage intelligent</p>
            <ul>
              <li>mongo-mongos-xxxxx</li>
              <li>mongo-mongos-xxxxx</li>
            </ul>
            <small>{'✅ Actif' if ENVIRONMENT == 'dev' else '❌ Inactif'}</small>
          </div>
        </div>
        <div class="info-box">
          <strong>Mode: { '🚀 SHARDING AVANCÉ' if ENVIRONMENT == 'dev' else '🗄️ RÉPLICATION SIMPLE' }</strong><br>
          { 'Données partitionnées sur 3 shards + 2 routeurs + 3 config servers' if ENVIRONMENT == 'dev' else 'Réplication standard avec 3 pods MongoDB' }
        </div>
      </div>

      <!-- MongoDB Hosts avec Cache -->
      <div class="frame">
        <h2>Hosts from MongoDB <span id="cache-indicator" class="cache-indicator">Chargement...</span></h2>
        <ul id="host-list"></ul>
        <div class="info-box">
          <strong>Performance:</strong><br>
          • Redis Cache: {redis_status}<br>
          • MongoDB: {mongodb_status}<br>
          • Architecture: {ENVIRONMENT.upper()}
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
          <button onclick="showShardingInfo()" style="padding: 8px 16px; background: #4caf50; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">
            🗄️ Info Sharding
          </button>
        </div>
      </div>

    </div>

    <footer>
      &copy; 2025 Distributed Systems Demo Project - Environment: {ENVIRONMENT.upper()}
    </footer>

    <script>
      // Format hostname
      const span = document.getElementById('hostname');
      const text = span.textContent;
      if (text.length > 5) {{
        const firstPart = text.slice(0, -5);
        const last5 = text.slice(-5);
        span.innerHTML = `${{firstPart}}<span class="last5">${{last5}}</span>`;
      }}

      // Load data
      async function loadData() {{
        try {{
          const startTime = performance.now();
          const response = await fetch('/hosts');
          const endTime = performance.now();
          
          const data = await response.json();
          const list = document.getElementById('host-list');
          list.innerHTML = '';
          
          const responseTime = (endTime - startTime).toFixed(2);
          const cacheStatus = response.headers.get('X-Cache');
          const dataSource = cacheStatus === 'HIT' ? '🚀 Redis Cache' : '💾 MongoDB';
          
          document.getElementById('response-time').textContent = `${{responseTime}}ms`;
          document.getElementById('data-source').textContent = dataSource;
          
          const cacheIndicator = document.getElementById('cache-indicator');
          cacheIndicator.textContent = cacheStatus === 'HIT' ? 'CACHE' : 'DATABASE';
          cacheIndicator.className = cacheStatus === 'HIT' ? 'cache-indicator' : 'cache-indicator cache-miss';
          
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

      // Info sharding
      async function showShardingInfo() {{
        try {{
          const response = await fetch('/sharding-info');
          const data = await response.json();
          alert(`Info Sharding:\\n- Actif: ${{data.sharding_enabled}}\\n- Shards: ${{data.shards || 'N/A'}}\\n- Mode: ${{data.mode}}`);
        }} catch (e) {{
          alert('Erreur lors de la récupération des infos sharding');
        }}
      }}

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
        
        # Fallback sur MongoDB - STRUCTURE CORRIGÉE
        hosts = list(db.hosts.find({}, {"_id": 0}))
        
        # Transformer les données pour l'affichage
        formatted_hosts = []
        for host in hosts:
            # Les données sont maintenant stockées différemment avec le sharding
            pod_name = host.get('_id', 'Unknown')  # Maintenant _id est utilisé pour le sharding
            info = host.get('info', 'No info')
            formatted_hosts.append({
                "pod": pod_name,
                "info": info
            })
        
        response_data = json.dumps(formatted_hosts)
        
        # Mettre en cache pour 5 minutes
        if redis_available:
            redis_client.setex('hosts_data', 300, response_data)
        
        response = Response(response_data, mimetype='application/json')
        response.headers['X-Cache'] = 'MISS'
        response.headers['X-Response-Time'] = f"{(time.time() - start_time)*1000:.2f}ms"
        return response
        
    except Exception as e:
        # Fallback complet en cas d'erreur
        try:
            hosts = list(db.hosts.find({}, {"_id": 0}))
            formatted_hosts = [{"pod": h.get('_id', 'Unknown'), "info": h.get('info', 'No info')} for h in hosts]
            response = Response(json.dumps(formatted_hosts), mimetype='application/json')
        except:
            response = Response(json.dumps([{"pod": "Error", "info": "Cannot load data"}]), mimetype='application/json')
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

@app.route("/sharding-info")
def sharding_info():
    """Endpoint pour voir les infos de sharding"""
    try:
        if ENVIRONMENT == 'dev':
            # En dev, on teste si on est connecté à un mongos (sharding)
            try:
                # Cette commande ne fonctionne que sur mongos
                config_db = client["config"]
                shards_count = config_db.shards.count_documents({})
                
                return jsonify({
                    "sharding_enabled": True,
                    "shards": shards_count,
                    "mode": "sharding",
                    "environment": ENVIRONMENT,
                    "connected_to": "mongos"
                })
            except Exception as e:
                # Si on arrive ici, on est probablement connecté à un mongod normal
                return jsonify({
                    "sharding_enabled": False,
                    "mode": "replication",
                    "environment": ENVIRONMENT,
                    "connected_to": "mongod",
                    "info": "Connecté à un serveur MongoDB standard"
                })
        else:
            # En test, réplication simple
            return jsonify({
                "sharding_enabled": False,
                "mode": "replication", 
                "environment": ENVIRONMENT,
                "connected_to": "mongod"
            })
    except Exception as e:
        return jsonify({
            "sharding_enabled": False,
            "error": str(e),
            "environment": ENVIRONMENT
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)