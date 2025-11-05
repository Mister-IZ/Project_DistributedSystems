#!/bin/bash
echo "🚀 CONFIGURATION SHARDING MONGODB "

# Attendre que les services soient prêts
echo "⏳ Attente initiale pour la stabilité des services..."
sleep 30

# 1. VÉRIFICATION ET INITIALISATION DES CONFIG SERVERS
echo "🔍 Vérification des config servers..."
kubectl exec -n dev mongo-config-0 -- mongosh --eval "
try {
    var status = rs.status();
    print('✅ Config servers déjà initialisés - Status: ' + status.ok);
} catch (e) {
    if (e.codeName === 'NotYetInitialized') {
        print('⚙️ Initialisation des config servers...');
        rs.initiate({
            _id: 'rs-config',
            configsvr: true,
            members: [
                { _id: 0, host: 'mongo-config-0.mongo-config.dev.svc.cluster.local:27017' },
                { _id: 1, host: 'mongo-config-1.mongo-config.dev.svc.cluster.local:27017' },
                { _id: 2, host: 'mongo-config-2.mongo-config.dev.svc.cluster.local:27017' }
            ]
        });
        print('✅ Config servers initialisés avec succès');
    } else {
        print('❌ Erreur config servers: ' + e.message);
    }
}
" || echo "⚠️ Problème avec config servers"

# 2. VÉRIFICATION ET INITIALISATION DU SHARD
echo "🔧 Vérification du shard replica set..."
kubectl exec -n dev mongo-shard-0 -- mongosh --eval "
try {
    var status = rs.status();
    print('✅ Shard déjà initialisé - Status: ' + status.ok);
} catch (e) {
    if (e.codeName === 'NotYetInitialized') {
        print('⚙️ Initialisation du shard...');
        rs.initiate({
            _id: 'rs-shard',
            members: [
                { _id: 0, host: 'mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017' },
                { _id: 1, host: 'mongo-shard-1.mongo-shard.dev.svc.cluster.local:27017' },
                { _id: 2, host: 'mongo-shard-2.mongo-shard.dev.svc.cluster.local:27017' }
            ]
        });
        print('✅ Shard initialisé avec succès');
    } else {
        print('❌ Erreur shard: ' + e.message);
    }
}
" || echo "⚠️ Problème avec shard"

# 3. ATTENTE STABILISATION
echo "⏳ Attente de stabilisation des replica sets (30 secondes)..."
sleep 30

# 4. VÉRIFICATION QUE MONGOS EST OPÉRATIONNEL
echo "🎯 Vérification de mongos..."
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "🔄 Redémarrage de mongos (non opérationnel)..."
    kubectl rollout restart deployment/mongo-mongos -n dev
    echo "⏳ Attente du redémarrage de mongos (25 secondes)..."
    sleep 25
fi

# 5. CONFIGURATION DU SHARDING VIA MONGOS
echo "⚙️ Configuration du sharding via mongos..."

kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
print('🎯 Début configuration sharding...');

// Test de connexion aux config servers
try {
    var shards = db.adminCommand({ listShards: 1 });
    print('✅ Connecté aux config servers - ' + shards.shards.length + ' shard(s) listé(s)');
} catch (e) {
    print('❌ Impossible d\\'accéder aux config servers: ' + e.message);
    quit(1);
}

// 1. Ajouter le shard
try {
    sh.addShard('rs-shard/mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017');
    print('✅ Shard ajouté');
} catch(e) { 
    print('ℹ️ Shard: ' + e.message); 
}

// 2. Activer sharding sur demoDB
try {
    sh.enableSharding('demoDB');
    print('✅ Sharding activé sur demoDB');
} catch(e) { 
    print('ℹ️ Sharding: ' + e.message); 
}

// 3. Préparer la base
print('🗂️ Préparation des collections...');
db = db.getSiblingDB('demoDB');

try { 
    db.dropDatabase();
    print('✅ Base demoDB réinitialisée');
} catch(e) { 
    print('ℹ️ Base: ' + e.message); 
}

// Recréer les collections
db.createCollection('users');
db.createCollection('orders');
db.createCollection('hosts');
print('✅ Collections créées');

// 4. Sharder users
try {
    db.users.createIndex({ user_id: 'hashed' });
    sh.shardCollection('demoDB.users', { user_id: 'hashed' });
    print('✅ Users shardé sur user_id');
} catch(e) { 
    print('❌ Users: ' + e.message); 
}

// 5. Sharder orders
try {
    db.orders.createIndex({ order_id: 'hashed' });
    sh.shardCollection('demoDB.orders', { order_id: 'hashed' });
    print('✅ Orders shardé sur order_id');
} catch(e) { 
    print('❌ Orders: ' + e.message); 
}

// 6. Sharder hosts
try {
    db.hosts.createIndex({ _id: 'hashed' });
    sh.shardCollection('demoDB.hosts', { _id: 'hashed' });
    print('✅ Hosts shardé sur _id');
} catch(e) { 
    print('❌ Hosts: ' + e.message); 
}

print('🔍 Vérification finale...');
"

# 6. VÉRIFICATION DÉTAILLÉE
echo "🔍 Vérification détaillée..."
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
print('=== SHARDING STATUS ===');
sh.status();

print('\\\\n=== DÉTAILS demoDB ===');
var dbInfo = db.getSiblingDB('config').databases.findOne({_id: 'demoDB'});
if (dbInfo) {
    print('demoDB partitioned: ' + dbInfo.partitioned);
    print('demoDB primary: ' + dbInfo.primary);
} else {
    print('❌ demoDB non trouvée dans config');
}

print('\\\\n=== COLLECTIONS SHARDÉES ===');
db = db.getSiblingDB('demoDB');
var collections = db.getCollectionNames();
print('Collections: ' + JSON.stringify(collections));

collections.forEach(function(coll) {
    try {
        var stats = db[coll].stats();
        print('- ' + coll + ': sharded=' + stats.sharded + ', count=' + stats.count);
    } catch(e) {
        print('- ' + coll + ': erreur stats');
    }
});
"

# 7. TEST FINAL CRITIQUE
echo "🎯 Test final critique..."
kubectl exec -n dev deployment/mongo-mongos -- mongosh demoDB --eval "
try {
    var result = db.users.getShardDistribution();
    print('✅✅✅ SUCCÈS! Users shardé:');
    print(JSON.stringify(result, null, 2));
} catch(e) {
    print('❌❌❌ ÉCHEC - Users pas shardé: ' + e.message);
}

try {
    var result = db.orders.getShardDistribution();
    print('✅✅✅ SUCCÈS! Orders shardé:');
    print(JSON.stringify(result, null, 2));
} catch(e) {
    print('❌❌❌ ÉCHEC - Orders pas shardé: ' + e.message);
}
"

echo ""
echo "🎉 CONFIGURATION SHARDING TERMINÉE !"