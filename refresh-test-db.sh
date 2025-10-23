#!/bin/bash
# refresh-test-db.sh - VERSION AMÉLIORÉE

echo "🔄 Rafraîchissement DB TEST depuis DEV (partiel + anonymisé)"

# 1. Export PARTIEL depuis DEV (seulement les données récentes)
echo "📦 Export des données récentes depuis DEV..."
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "
use demoDB

// Exporter seulement les users avec commandes récentes
const recentUsers = db.users.aggregate([
    {
        \$lookup: {
            from: 'orders',
            localField: 'user_id',
            foreignField: 'user_id',
            as: 'user_orders'
        }
    },
    {
        \$match: {
            'user_orders': { \$ne: [] }
        }
    },
    {
        \$limit: 20  // ← SEULEMENT 20 users max pour TEST
    }
]).toArray()

// Exporter les commandes de ces users
const userIds = recentUsers.map(u => u.user_id)
const recentOrders = db.orders.find({ 
    user_id: { \$in: userIds } 
}).limit(50).toArray()  // ← SEULEMENT 50 commandes

print('Exporting ' + recentUsers.length + ' users and ' + recentOrders.length + ' orders')
db.temp_export.drop()
db.temp_export.insert({ 
    users: recentUsers, 
    orders: recentOrders,
    export_date: new Date()
})
" 

# 2. Dump de la collection temporaire
kubectl exec -n dev deployment/mongo-mongos -- mongodump --db demoDB --collection temp_export --archive > /tmp/dev_partial.archive

# 3. Nettoyage côté DEV
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "db.temp_export.drop()"

# 4. Restauration dans TEST
echo "📥 Import des données vers TEST..."
cat /tmp/dev_partial.archive | kubectl exec -n test mongo-0 -i -- mongorestore --archive --drop

# 5. Extraction et anonymisation dans TEST
echo "🎭 Reconstruction et anonymisation dans TEST..."
kubectl exec -n test mongo-0 -- mongosh --eval "
use demoDB

// Récupérer les données exportées
const exportData = db.temp_export.findOne()
if (!exportData) {
    print('❌ No data to import')
    exit(1)
}

// Vider les collections existantes
db.users.deleteMany({})
db.orders.deleteMany({})

// Réinsérer les users avec anonymisation
exportData.users.forEach(user => {
    db.users.insertOne({
        user_id: user.user_id,
        name: user.name.charAt(0) + 'XXXXX',  // Anonymiser le nom
        email: user.name.charAt(0).toLowerCase() + 'xxxxx@test.com',  // Email anonyme
        country: user.country,
        order_count: user.order_count,
        total_spent: user.total_spent,
        // Champs spécifiques TEST
        environment: 'test',
        source: 'dev_export',
        imported_date: new Date(),
        // Reproduire les migrations si nécessaire
        created_at: user.created_at || new Date(),
        schema_version: user.schema_version || 1
    })
})

// Réinsérer les orders avec randomisation
exportData.orders.forEach(order => {
    db.orders.insertOne({
        order_id: 'test_' + order.order_id,  // Préfixe TEST
        user_id: order.user_id,
        user_name: order.user_name.charAt(0) + 'XXXXX',  // Nom anonymisé
        amount: Math.round(order.amount * (0.5 + Math.random() * 0.5)),  // Montant aléatoire ±50%
        status: order.status,
        environment: 'test',
        source: 'dev_export',
        imported_date: new Date()
    })
})

// Nettoyer la collection temporaire
db.temp_export.drop()

// Stats finales
print('✅ Import TEST terminé:')
print('👥 Users: ' + db.users.countDocuments())
print('🛒 Orders: ' + db.orders.countDocuments())
print('🏷️ Tous les orders préfixés avec \"test_\"')
"

# 6. Nettoyage
rm -f /tmp/dev_partial.archive

echo "✅ Base TEST rafraîchie avec succès !"
echo "🌐 Accéder à: http://test.demo.local/user-dashboard"