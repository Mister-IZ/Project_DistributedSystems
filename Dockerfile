FROM python:3.12-alpine

# Installer nginx et dépendances
RUN apk add --no-cache nginx bash

# Installer ce qu'il faut 
RUN pip install flask pymongo redis

# Copier les fichiers Flask
WORKDIR /app
COPY app/app.py /app/app.py
COPY app/templates/index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Variables d'environnement par défaut
ENV MONGODB_URI="mongodb://mongo-mongos.dev.svc.cluster.local:27017/?directConnection=true"
ENV REDIS_HOST="redis-service.dev"
ENV ENVIRONMENT="dev"

# Exposer les ports Flask et NGINX
EXPOSE 80 5000

# Convertir les fins de ligne Windows en UNIX et corriger les droits
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
