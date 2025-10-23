#!/bin/bash
echo "🚀 Configuration du Sharding MongoDB..."

# Attendre que tous les services soient vraiment prêts
echo "⏳ Attente supplémentaire pour la stabilité des services..."
sleep 30

# 1. Vérifier que les config servers sont accessibles
echo "🔍 Vérification des config servers..."
kubectl exec -n dev mongo-config-0 -- mongosh --eval "
rs.initiate({
  _id: 'rs-config',
  configsvr: true,
  members: [
    { _id: 0, host: 'mongo-config-0.mongo-config.dev.svc.cluster.local:27017' },
    { _id: 1, host: 'mongo-config-1.mongo-config.dev.svc.cluster.local:27017' },
    { _id: 2, host: 'mongo-config-2.mongo-config.dev.svc.cluster.local:27017' }
  ]
})" || echo "⚠️ Config servers peut-être déjà initialisés"

# 2. Attendre que les config servers soient stables
sleep 15

# 3. Initialiser le shard
echo "🔧 Initialisation du shard replica set..."
kubectl exec -n dev mongo-shard-0 -- mongosh --eval "
rs.initiate({
  _id: 'rs-shard',
  members: [
    { _id: 0, host: 'mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017' },
    { _id: 1, host: 'mongo-shard-1.mongo-shard.dev.svc.cluster.local:27017' },
    { _id: 2, host: 'mongo-shard-2.mongo-shard.dev.svc.cluster.local:27017' }
  ]
})" || echo "⚠️ Shard peut-être déjà initialisé"

# 4. Attendre plus longtemps pour la stabilité
echo "⏳ Attente de stabilisation des replica sets (30 secondes)..."
sleep 30

# 5. REDÉMARRER mongos pour qu'il prenne en compte la config
echo "🔄 Redémarrage de mongos..."
kubectl rollout restart deployment/mongo-mongos -n dev

# Attendre que mongos redémarre
echo "⏳ Attente du redémarrage de mongos (20 secondes)..."
sleep 20

# 6. Maintenant configurer le sharding
echo "⚙️ Configuration du sharding via mongos..."

# Vérifier d'abord que mongos est connecté aux config servers
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
db.adminCommand({ listShards: 1 })
" || echo "❌ Mongos ne peut pas accéder aux config servers"

# Ajouter le shard
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
sh.addShard('rs-shard/mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017')
"

# Activer le sharding
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
sh.enableSharding('demoDB')
"

# Créer la collection shardée
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
use demoDB
db.createCollection('users')
db.users.createIndex({ _id: 'hashed' })
sh.shardCollection('demoDB.users', { _id: 'hashed' })
"

# Créer aussi la collection hosts pour l'app existante
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
use demoDB
db.createCollection('hosts') 
db.hosts.createIndex({ _id: 'hashed' })
sh.shardCollection('demoDB.hosts', { _id: 'hashed' })
"

echo "✅ Sharding MongoDB configuré avec succès !"