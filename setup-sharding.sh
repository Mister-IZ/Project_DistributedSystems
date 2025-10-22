#!/bin/bash
echo "🚀 Configuration du Sharding MongoDB..."

# 1. Initialiser le Config Server Replica Set
kubectl exec -n dev mongo-config-0 -- mongosh --eval "
rs.initiate({
  _id: 'rs-config',
  configsvr: true,
  members: [
    { _id: 0, host: 'mongo-config-0.mongo-config.dev.svc.cluster.local:27017' },
    { _id: 1, host: 'mongo-config-1.mongo-config.dev.svc.cluster.local:27017' },
    { _id: 2, host: 'mongo-config-2.mongo-config.dev.svc.cluster.local:27017' }
  ]
})"

# 2. Initialiser le Shard Replica Set
kubectl exec -n dev mongo-shard-0 -- mongosh --eval "
rs.initiate({
  _id: 'rs-shard',
  members: [
    { _id: 0, host: 'mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017' },
    { _id: 1, host: 'mongo-shard-1.mongo-shard.dev.svc.cluster.local:27017' },
    { _id: 2, host: 'mongo-shard-2.mongo-shard.dev.svc.cluster.local:27017' }
  ]
})"

# 3. Attendre que les replica sets soient prêts
sleep 30

# 4. Ajouter le shard au cluster via mongos
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
sh.addShard('rs-shard/mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017')
"

# 5. Activer le sharding pour la database demoDB
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
sh.enableSharding('demoDB')
"

# 6. Créer un index de sharding sur la collection hosts
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
use demoDB
db.hosts.createIndex({ _id: 'hashed' })
sh.shardCollection('demoDB.hosts', { _id: 'hashed' })
"

echo "✅ Sharding MongoDB configuré avec succès !"