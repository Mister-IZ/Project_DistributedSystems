#!/bin/bash
# refresh-test-db.sh - VERSION ANONYMIZATION PARTIELLE

echo "🔄 Rafraîchissement DB TEST depuis DEV (noms anonymisés)"

# 1. VÉRIFIER que DEV a des données
echo "🔍 Vérification DEV..."
RESULT=$(kubectl exec -n dev deployment/mongo-mongos -- mongosh demoDB --eval "
try {
    const users = db.users.countDocuments()
    const orders = db.orders.countDocuments()
    
    if (users === 0) {
        print('ERROR:NO_USERS')
        quit(1)
    }
    
    print('SUCCESS:' + users + ' users, ' + orders + ' orders')
    
} catch (e) {
    print('ERROR:' + e.message)
    quit(1)
}
" --quiet)

echo "Résultat: $RESULT"
if [[ "$RESULT" == *"ERROR"* ]]; then
    echo "❌ Problème avec DEV: $RESULT"
    echo "💡 Chargez des données: http://demo.local/user-dashboard → Load Sample Data"
    exit 1
fi

echo "✅ DEV a des données"

# 2. TRANSFERT AVEC ANONYMIZATION PARTIELLE
echo "📦 Transfert DEV → TEST (noms anonymisés, emails conservés)..."

kubectl exec -n dev deployment/mongo-mongos -- mongosh demoDB --eval "
try {
    print('🔍 Récupération des données DEV...')
    
    // Prendre un échantillon de données
    const users = db.users.find().limit(10).toArray()
    const orders = db.orders.find().limit(15).toArray()
    
    print('📊 Données trouvées: ' + users.length + ' users, ' + orders.length + ' orders')
    
    // ANONYMIZATION PARTIELLE : Noms seulement
    const testUsers = users.map(u => ({
        user_id: u.user_id,
        name: 'User_' + u.user_id,  // ← NOM ANONYMISÉ
        email: u.email,             // ← EMAIL CONSERVÉ
        country: u.country,
        order_count: u.order_count,
        total_spent: u.total_spent,
        environment: 'test',
        source: 'dev_refresh_anon',
        original_name: u.name,      // ← POUR DÉMONSTRATION
        imported_date: new Date(),
        created_at: u.created_at,
        schema_version: u.schema_version || 1
    }))
    
    const testOrders = orders.map(o => ({
        order_id: o.order_id,
        user_id: o.user_id,
        user_name: 'User_' + o.user_id,  // ← NOM ANONYMISÉ
        amount: o.amount,
        status: o.status,
        environment: 'test',
        source: 'dev_refresh_anon',
        imported_date: new Date()
    }))
    
    print('🎯 Données préparées pour TEST:')
    print('   👤 ' + testUsers.length + ' users (noms anonymisés)')
    print('   📧 Emails conservés pour traçabilité')
    print('   🛒 ' + testOrders.length + ' orders')
    
    // Afficher quelques exemples
    print('   📝 Exemples:')
    testUsers.slice(0, 2).forEach(u => {
        print('      - ' + u.original_name + ' → ' + u.name + ' (' + u.email + ')')
    })
    
    // Convertir en JSON
    const usersJson = JSON.stringify(testUsers)
    const ordersJson = JSON.stringify(testOrders)
    
    // Script pour TEST
    const testScript = \`
        use demoDB
        
        // Vider les collections existantes
        db.users.deleteMany({})
        db.orders.deleteMany({})
        
        // Insérer les nouvelles données
        if (\${usersJson}.length > 0) {
            db.users.insertMany(\${usersJson})
        }
        if (\${ordersJson}.length > 0) {
            db.orders.insertMany(\${ordersJson})
        }
        
        // Résultat
        const finalUsers = db.users.countDocuments()
        const finalOrders = db.orders.countDocuments()
        print('🎉 RAFRAÎCHISSEMENT RÉUSSI: ' + finalUsers + ' users, ' + finalOrders + ' orders')
        
        if (finalUsers > 0) {
            const sample = db.users.findOne()
            print('📝 Exemple final:')
            print('   👤 Nom: ' + sample.name + ' (anonymisé)')
            print('   📧 Email: ' + sample.email + ' (original)')
            print('   🏷️ Source: ' + sample.source)
            print('   🔍 Original: ' + sample.original_name)
        }
    \`
    
    // Écrire et exécuter
    require('fs').writeFileSync('/tmp/refresh_script.js', testScript)
    
} catch (e) {
    print('❌ Erreur: ' + e.message)
    quit(1)
}
"

# 3. Exécuter dans TEST
echo "📥 Exécution dans TEST..."
kubectl exec -n dev deployment/mongo-mongos -- cat /tmp/refresh_script.js | kubectl exec -n test mongo-0 -i -- mongosh --quiet

# 4. Vérification finale
echo "✅ Vérification finale..."
kubectl exec -n test mongo-0 -- mongosh demoDB --eval "
print('')
print('📊 BASE TEST RAFRAÎCHIE:')
print('👥 Users: ' + db.users.countDocuments() + ' (noms anonymisés)')
print('🛒 Orders: ' + db.orders.countDocuments())
print('')
print('🔍 TRACABILITÉ:')
print('   📧 Emails conservés pour montrer la provenance')
print('   👤 Noms anonymisés (User_XXX)')
print('   🏷️ Source: dev_refresh_anon')
print('')
print('📝 Données exemple:')
db.users.find().limit(3).forEach(u => {
    print('   👤 ' + u.name + ' (' + u.email + ')')
    print('   🔍 Original: ' + u.original_name)
    print('   🏷️ ' + u.environment + ' | ' + u.source)
    print('')
})
print('🌐 Vérifiez: http://test.demo.local/user-dashboard')
"

echo ""
echo "✅ RAFRAÎCHISSEMENT TERMINÉ!"
echo "💡 Noms anonymisés mais emails conservés pour traçabilité"
echo "🎯 Parfait pour démontrer la provenance des données !"