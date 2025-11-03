🧭 **Documentation du Projet Distributed Systems – Partie 1**

## 1. Pré-requis

Avant de démarrer :

- Avoir **Docker Desktop** installé sur votre machine.  
- Avoir **Kubernetes activé** dans Docker Desktop :  
  - Ouvrir `Settings > Kubernetes > Enable Kubernetes`.  
  - Choisir le moteur **Kubeadm** (et non Minikube).  

💡 Cela crée automatiquement un **cluster Kubernetes local** géré par Docker Desktop.

---

## 2. Création du Dossier de Projet

Créer un dossier de travail dans **Visual Studio Code** :

``mkdir Project_DistributedSystems``  
``cd Project_DistributedSystems``

C’est ici que tout le code et les manifests seront placés :

- ``manifests/`` → pour les fichiers YAML (Deployments, Services, Ingress)
- ``demo-web/`` → pour le code source de la mini application (HTML/CSS)
- ``Dockerfile`` → pour construire l’image

---

## 3. Vérification du Cluster

Une fois Kubernetes activé :

``kubectl get nodes``  
``kubectl get pods -A``

✅ Vous devriez voir un nœud **docker-desktop** dans l’état *Ready*.

---

## 4. Création des Namespaces (environnements Dev / Test / Prod)

Nous avons mis en place des namespaces pour séparer les environnements :

``kubectl create namespace dev``  
``kubectl create namespace test``  
``kubectl create namespace prod``

Vérifiez :

``kubectl get ns``

---

## 5. Installation de l’Ingress Controller (NGINX)

L’**Ingress Controller** permet d’exposer les services Kubernetes vers l’extérieur du cluster.  
Nous avons choisi **NGINX Ingress Controller**, que l’on installe via la commande suivante :

``kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml``

Vérification :

``kubectl get pods -n ingress-nginx``

Attendez que le pod **ingress-nginx-controller** soit en *Running*.

---

## 6. Vérification de l’installation

Commandes utiles pour vérifier que tout est bien installé :

``kubectl get all -n ingress-nginx``  
et  
``kubectl get pods -A | findstr ingress``

---

## 7. Configuration du Fichier Hosts (accès local au site)

Pour accéder à l’application via un **nom de domaine local**, nous avons ajouté une ligne dans le fichier hosts :

🗂️ **Chemin (Windows)** :
``C:\Windows\System32\drivers\etc\hosts``

Ajouter :
``127.0.0.1   demo.local``

⚠️ Cela permet d’accéder à l’application via l’URL :  
👉 **http://demo.local**

---

## 8. Vérification du Fonctionnement

Quand tout est configuré :

1. Lancer **Docker Desktop** (il démarre automatiquement Kubernetes).  
2. Vérifier les pods :
   ``kubectl get pods -n dev``  
3. Ouvrir votre navigateur :
   ``http://demo.local``

Vous devriez voir votre page HTML affichée depuis un pod du cluster Kubernetes.

---

## 9. Arrêt propre du système

À la fin de la journée :

- Fermer **Docker Desktop**  
  👉 Cela arrête Kubernetes et libère la mémoire.  
  👉 Aucun fichier ou configuration n’est perdu.

Au redémarrage :

- Rouvrez **Docker Desktop** → tout revient automatiquement (pods, déploiements, ingress, etc.).




# 📚 Documentation Projet Kubernetes - Distributed Systems

## 📋 Table des Matières
1. [Vue d'ensemble](#vue-densemble)
2. [Configuration du Cluster](#1-configuration-du-cluster)
3. [Pipeline CI/CD](#2-pipeline-cicd)
4. [Configuration de la Base de Données](#3-configuration-de-la-base-de-données)
5. [Monitoring et Scaling](#4-monitoring-et-scaling)
6. [Guide d'Onboarding](#5-guide-donboarding)

---

## 🎯 Vue d'ensemble

**Distributed Systems Demo** est une infrastructure Kubernetes professionnelle démontrant les concepts avancés de microservices, sharding MongoDB, cache Redis et pipeline CI/CD automatisé.

### 🌐 URLs d'Accès
- **Environnement DEV** : `http://demo.local`
- **Environnement TEST** : `http://test.demo.local`
- **Dashboard Kubernetes** : `http://localhost:8001` (après `kubectl proxy`)

### 🏗️ Architecture Technique
Namespace DEV :
- 🔧 MongoDB Sharding Cluster (8 pods)
  - Config Servers (3 pods - replica set rs-config)
  - Shard Servers (3 pods - replica set rs-shard)
  - Mongos Routers (2 pods)
- 🎯 Redis Cluster (2 pods répliqués)
- 🚀 Application Flask (3 pods)

Namespace TEST :
- 🗄️ MongoDB Réplication (3 pods - replica set rs0)
- 🎯 Redis (2 pods répliqués)
- 🚀 Application Flask (2 pods)
- ⚙️ CronJob Auto-Update (exécution toutes les 5 minutes)

### 🎯 Stack Technologique
- **Application** : Flask (Python) + HTML intégré
- **Base de données** : MongoDB (sharding/réplication) + Redis (cache)
- **Orchestration** : Kubernetes + Docker Desktop
- **CI/CD** : GitHub Actions + Docker Hub
- **Monitoring** : Kubernetes Dashboard + Metrics Server

---

## 1. 📦 Configuration du Cluster

### 1.1 Prérequis
- ✅ **Docker Desktop** avec Kubernetes activé
- ✅ **kubectl** configuré
- ✅ **Git** pour cloner le repository
- ✅ **Accès au fichier hosts** pour la configuration DNS locale

### 1.2 Installation - Environnement Local

#### Étape 1 : Installation de Docker Desktop
```
# Télécharger Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Activer Kubernetes
# Docker Desktop → Settings → Kubernetes → Enable Kubernetes

# Vérifier l'installation
kubectl cluster-info
kubectl get nodes
```

#### Étape 2 : Configuration DNS Locale
Éditer le fichier hosts :
- **Windows** : `C:\Windows\System32\drivers\etc\hosts`
- **Linux/Mac** : `/etc/hosts`

Ajouter les lignes suivantes :
```
127.0.0.1 demo.local
127.0.0.1 test.demo.local
```

#### Étape 3 : Installation du Cluster (Automatisée)
```
git clone <repository-url>
cd Project_DistributedSystems
./start-cluster.sh
```

#### Étape 4 : Installation Manuelle (Alternative)
```
kubectl apply -f manifests/namespaces.yaml
kubectl apply -f manifests/mongodb-config.yaml -n dev
kubectl apply -f manifests/mongodb-shard.yaml -n dev
kubectl apply -f manifests/mongodb-mongos.yaml -n dev
kubectl apply -f manifests/mongodb-test.yaml -n test
kubectl apply -f manifests/redis-dev.yaml -n dev
kubectl apply -f manifests/redis-test.yaml -n test
kubectl apply -f manifests/web-deployment.yaml -n dev
kubectl apply -f manifests/test-deployment.yaml -n test
./setup-sharding.sh
```

### 1.3 Installation Ingress Controller
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
kubectl get pods -n ingress-nginx
kubectl get services -n ingress-nginx
```

### 1.4 Vérification de l'Installation
```
kubectl get pods -A
curl -I http://demo.local
curl -I http://test.demo.local
kubectl get services -A
kubectl get ingress -A
```

### 1.5 Procédure de Redémarrage
```
./start-cluster.sh
./setup-sharding.sh
curl http://demo.local
curl http://test.demo.local
```

### 1.6 Arrêt Propre du Cluster
```
# Docker Desktop → Paramètres → Kubernetes → Stop
# Attendre l'arrêt complet
# Quitter Docker Desktop
```

---

## 2. 🔄 Pipeline CI/CD

### 2.1 Vue d'ensemble du Pipeline
Git Push → Tests Unitaires → Build Docker → Push Docker Hub → Auto-Deploy TEST

### 2.2 Configuration GitHub Actions
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  build-test-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
        env:
          PYTHONPATH: .
      - name: Run unit tests
        run: pytest -v
      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKER_HUB_USERNAME }}/demo-app:latest .
          docker build -t ${{ secrets.DOCKER_HUB_USERNAME }}/demo-app:${{ github.sha }} .
      - name: Push to Docker Hub
        run: |
          echo "${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}" | docker login -u "${{ secrets.DOCKER_HUB_USERNAME }}" --password-stdin
          docker push ${{ secrets.DOCKER_HUB_USERNAME }}/demo-app:latest
          docker push ${{ secrets.DOCKER_HUB_USERNAME }}/demo-app:${{ github.sha }}
```

### 2.3 Secrets GitHub Requis
- `DOCKER_HUB_USERNAME`
- `DOCKER_HUB_ACCESS_TOKEN`

### 2.4 Système d'Auto-Update TEST
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: auto-sync-demo-app
  namespace: test
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: auto-sync-sa
          containers:
          - name: auto-sync
            image: alpine/k8s:1.30.8
            command:
            - /bin/sh
            - -c
            - |
              bash /scripts/check-and-update.sh
          volumeMounts:
          - name: script
            mountPath: /scripts
          volumes:
          - name: script
            configMap:
              name: auto-sync-script
```

### 2.5 Tests Unitaires
```python
import pytest
from app.app import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
```

### 2.6 Déploiement Zero Downtime
```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

---

## 3. 🗄️ Configuration de la Base de Données

### 3.1 Architecture MongoDB
- DEV : Sharding avancé (Config Servers 3 pods, Shards 3 pods, Mongos 2 pods)
- TEST : Réplication simple (MongoDB 3 pods)

### 3.2 Configuration du Sharding
```bash
./setup-sharding.sh
```

### 3.3 Vérification du Sharding
```bash
kubectl exec -n dev deployment/mongo-mongos -- mongosh --eval "sh.status()"
kubectl exec -n dev deployment/mongo-mongos -- mongosh demoDB --eval "db.hosts.getShardDistribution()"
kubectl exec -n dev mongo-config-0 -- mongosh --eval "rs.status()"
kubectl exec -n dev mongo-shard-0 -- mongosh --eval "rs.status()"
kubectl exec -n test mongo-0 -- mongosh --eval "rs.status()"
```

### 3.4 Configuration Redis
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        ports:
        - containerPort: 6379
```

### 3.5 Stratégie de Migration
```bash
./refresh-test-db.sh
curl -X POST http://demo.local/api/run-migration
```

### 3.6 Persistent Volumes
```bash
kubectl get pvc -A
kubectl get pv
```

---

## 4. 📊 Monitoring et Scaling

### 4.1 Kubernetes Dashboard
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
kubectl apply -f manifests/dashboard-admin.yaml
kubectl proxy
```

### 4.2 Metrics Server
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl -n kube-system patch deployment metrics-server --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
kubectl top pods -A
kubectl top nodes
```

### 4.3 Commandes de Monitoring
```bash
kubectl get pods -A -w
kubectl top pods -A
kubectl logs -n dev -l app=demo-app --tail=20
kubectl logs -f deployment/demo-app -n dev
kubectl get events -A --sort-by='.lastTimestamp'
kubectl get deployments -A
```

### 4.4 Scaling Manuel
```bash
kubectl scale deployment/demo-app --replicas=5 -n dev
kubectl scale deployment/demo-app --replicas=3 -n test
kubectl get pods -n dev
kubectl get pods -n test
kubectl rollout status deployment/demo-app -n dev
```
Ou bien juste allez sur le dashboard Kubernetes et mettre à l'échelles les réplicas qu'on souhaite scaller.

---

## 5. 👨‍💻 Guide d'Onboarding

### 5.1 Installation Express (10 minutes)
```bash
git clone <repository-url>
cd Project_DistributedSystems
# Configurer hosts
./start-cluster.sh
kubectl get all -n dev
kubectl get all -n test
```

### 5.2 Environnements Disponibles
| Environnement | URL | Usage | Architecture DB | Auto-Update |
|---------------|-----|-------|-----------------|-------------|
| DEV           | demo.local | Développement | Sharding MongoDB | Non |
| TEST          | test.demo.local | Tests | Réplication MongoDB | Oui (5 min) |

### 5.3 Workflow de Développement
```bash
git checkout -b feature/ma-nouvelle-feature
# Développer, tester
pytest -v
docker build -t demo-app:test .
docker run -p 5000:5000 demo-app:test
git add .
git commit -m "feat: description de la fonctionnalité"
git push origin feature/ma-nouvelle-feature
```

### 5.4 Commandes de Développement Quotidiennes
```bash
docker build -t <username>/demo-app:v2 .
docker run -p 5000:5000 <username>/demo-app:v2
kubectl set image deployment/demo-app demo-app=<username>/demo-app:v2 -n dev
kubectl rollout restart deployment/demo-app -n dev
```

### 5.5 Endpoints API Disponibles
- GET /  
- GET /user-dashboard  
- GET /api/stats  
- GET /api/users  
- GET /api/orders  
- POST /api/load-sample-data  
- POST /api/random-user  
- POST /api/random-order  
- POST /api/run-migration  
- DELETE /api/clear-data  
- GET /cache/status  
- POST /cache/clear  
- GET /sharding-info  

### 5.6 Résolution de Problèmes Courants
- Application inaccessible : vérifier pods, services, ingress, logs, restart
- MongoDB inaccessible : reconfigurer sharding, logs, test ping
- Données corrompues : refresh TEST depuis DEV, reload sample, clear data
- Cache Redis non fonctionnel : vérifier, clear, status

### 5.7 Dépannage Rapide
```bash
./start-cluster.sh
./setup-sharding.sh
./refresh-test-db.sh
kubectl rollout restart deployment/demo-app -n dev
kubectl rollout restart deployment/demo-app -n test
```

### 5.8 Conventions de Développement
- Tests unitaires obligatoires
- Build Docker fonctionnel requis
- Messages de commit clairs
- Vérifier logs après chaque déploiement
- Utiliser endpoints existants

"""

