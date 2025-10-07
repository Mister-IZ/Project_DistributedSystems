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
