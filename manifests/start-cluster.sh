#!/bin/bash
set -e  # Stop à la première erreur

echo "=================================================="
echo "🚀  INITIALISATION CLUSTER KUBERNETES"
echo "📦  Distributed Systems Demo - ECAM"
echo "=================================================="

# 1. Vérifier que Kubernetes est disponible
echo "🔍  Vérification de Kubernetes..."
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌  ERREUR: Kubernetes n'est pas démarré"
    echo "💡  SOLUTION: Lance Docker Desktop et active Kubernetes"
    exit 1
fi
echo "✅  Kubernetes connecté"

# 2. NETTOYAGE AUTOMATIQUE des StatefulSets problématiques
echo "🧹  Nettoyage des StatefulSets MongoDB existants..."
kubectl delete statefulset mongo-config -n dev --ignore-not-found=true
kubectl delete statefulset mongo-shard -n dev --ignore-not-found=true
kubectl delete statefulset mongo -n test --ignore-not-found=true

# Nettoyage optionnel supplémentaire
if [ "$1" == "--clean" ]; then
    echo "🧹  Nettoyage complet de l'environnement..."
    kubectl delete --ignore-not-found=true -f . -A
    sleep 10
    echo "✅  Nettoyage terminé"
fi

# Attendre que les StatefulSets soient bien supprimés
echo "⏳  Attente de la suppression des pods MongoDB (15 secondes)..."
sleep 15

# 3. Déploiement des namespaces
echo "📁  Création des namespaces..."
kubectl apply -f namespaces.yaml
echo "✅  Namespaces dev/test créés"

# 4. Déploiement MongoDB (DANS L'ORDRE CRITIQUE) - TOUJOURS CRÉER, JAMAIS UPDATE
echo "🗄️  Déploiement de MongoDB..."
echo "   📦  Config Servers..."
kubectl apply -f mongodb-config.yaml -n dev

echo "   📦  Shard Servers..."  
kubectl apply -f mongodb-shard.yaml -n dev

echo "   📦  Mongos Routers..."
kubectl apply -f mongodb-mongos.yaml -n dev

echo "   📦  MongoDB Test (réplication simple)..."
kubectl apply -f mongodb-test.yaml -n test

# 5. Déploiement Redis
echo "🧠  Déploiement de Redis..."
kubectl apply -f redis-dev.yaml -n dev
kubectl apply -f redis-test.yaml -n test
echo "✅  Redis déployé"

# 6. Attente des pods critiques (PLUS LONGUE POUR LES STATEFULSETS)
echo "⏳  Attente des services MongoDB..."
echo "   ⏰  Patientez 45 secondes que les pods StatefulSets soient prêts..."
sleep 45

# Vérification manuelle des pods
echo "🔍  Vérification des pods MongoDB..."
kubectl get pods -n dev | grep mongo
kubectl get pods -n test | grep mongo

# 7. Configuration du sharding (SEULEMENT SI MONGOS EST PRÊT)
echo "⚙️  Configuration du sharding MongoDB..."
if [ -f "setup-sharding.sh" ]; then
    # Vérifier que mongos est en cours d'exécution
    if kubectl get pods -n dev | grep mongo-mongos | grep Running >/dev/null; then
        chmod +x setup-sharding.sh
        echo "🔄  Lancement de la configuration sharding..."
        ./setup-sharding.sh
        echo "✅  Sharding configuré"
    else
        echo "⚠️  Mongos n'est pas encore prêt, sharding reporté"
        echo "💡  Relancez manuellement plus tard: ./setup-sharding.sh"
    fi
else
    echo "⚠️  Script setup-sharding.sh non trouvé, configuration manuelle nécessaire"
fi

# 8. Déploiement des applications
echo "🌐  Déploiement des applications Flask..."
kubectl apply -f web-deployment.yaml -n dev
kubectl apply -f test-deployment.yaml -n test

# 9. Déploiement de l'auto-sync
echo "🔄  Déploiement de l'auto-sync..."
kubectl apply -f auto-sync-configmap.yaml -n test
kubectl apply -f auto-sync-rbac.yaml -n test  
kubectl apply -f auto-sync-cronjob.yaml -n test
echo "✅  Auto-sync configuré"

# 10. Vérification finale
echo "🔍  Vérification finale des services..."
echo ""
echo "📊  ÉTAT DES PODS :"
echo "=== ENVIRONNEMENT DEV ==="
kubectl get pods -n dev

echo ""
echo "=== ENVIRONNEMENT TEST ==="  
kubectl get pods -n test

echo ""
echo "=================================================="
echo "✅ ✅ ✅  CLUSTER PRÊT ! ✅ ✅ ✅"
echo "=================================================="
echo ""
echo "🌐  URLS D'ACCÈS :"
echo "   🖥️   Environnement DEV:  http://demo.local"
echo "   🧪  Environnement TEST: http://test.demo.local"
echo "   📊  Dashboard K8s:      kubectl proxy (puis http://localhost:8001)"
echo ""
echo "🔧  COMMANDES UTILES :"
echo "   📝  Voir tous les pods:    kubectl get pods -A"
echo "   🔍  Logs d'un pod:         kubectl logs -f <pod-name> -n <namespace>"
echo "   🗑️  Tout redémarrer:       ./start-cluster.sh --clean"
echo "   ⚙️  Config sharding:       ./setup-sharding.sh (si échoué)"
echo ""
echo "🚀  Cluster prêt ! Appuyez sur Entrée pour fermer..."
read -p ">>> " wait_for_user
echo "=================================================="