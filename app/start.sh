#!/bin/sh
# Démarrer Flask en arrière-plan
python /app/app.py &

# Remplace {{HOSTNAME}} par le hostname du pod
sed -i "s/{{HOSTNAME}}/$HOSTNAME/g" /usr/share/nginx/html/index.html

# Démarrer Nginx
nginx -g "daemon off;"
