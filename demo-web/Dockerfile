FROM alpine:latest

# Installer nginx et bash
RUN apk add --no-cache nginx bash

# Copier les fichiers
COPY index.html /usr/share/nginx/html/index.html
COPY start.sh /start.sh
COPY nginx.conf /etc/nginx/nginx.conf


# Rendre start.sh exécutable
RUN chmod +x /start.sh

# Exposer le port
EXPOSE 80

# Démarrer le container
CMD ["/start.sh"]
