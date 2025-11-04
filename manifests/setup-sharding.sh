#!/bin/bash
echo "🚀 SHARDING - VERSION FINALE TESTÉE"

# Exécuter directement les commandes MongoDB
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
print('🎯 Début configuration sharding...');

// 1. Ajouter shard
try {
    sh.addShard('rs-shard/mongo-shard-0.mongo-shard.dev.svc.cluster.local:27017');
    print('✅ Shard ajouté');
} catch(e) { 
    print('ℹ️ Shard: ' + e.message); 
}

// 2. Activer sharding
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

# Vérification détaillée
echo "🔍 VÉRIFICATION DÉTAILLÉE..."
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
print('=== SHARDING STATUS ===');
sh.status();

print('\\\\n=== DÉTAILS demoDB ===');
var dbInfo = db.getSiblingDB('config').databases.findOne({_id: 'demoDB'});
if (dbInfo) {
    print('demoDB partitioned: ' + dbInfo.partitioned);
    print('demoDB primary: ' + dbInfo.primary);
} else {
    print('❌ demoDB non trouvée');
}

print('\\\\n=== COLLECTIONS ===');
db = db.getSiblingDB('demoDB');
var collections = db.getCollectionNames();
print('Collections: ' + JSON.stringify(collections));

collections.forEach(function(coll) {
    try {
        var stats = db[coll].stats();
        print('- ' + coll + ': sharded=' + stats.sharded + ', count=' + stats.count);
    } catch(e) {
        print('- ' + coll + ': erreur');
    }
});
"

# Test final CRITIQUE
echo "🎯 TEST FINAL CRITIQUE..."
kubectl exec -n dev deployment/mongo-mongos -- mongosh demoDB --eval "
try {
    var result = db.users.getShardDistribution();
    print('✅✅✅ SUCCÈS! Users shardé:');
    print(JSON.stringify(result, null, 2));
} catch(e) {
    print('❌❌❌ ÉCHEC - Users pas shardé: ' + e.message);
    print('Détail erreur: ' + e);
}
"

echo ""
echo "🎉 CONFIGURATION TERMINÉE!"