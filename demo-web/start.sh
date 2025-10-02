#!/bin/sh
# Remplace {{HOSTNAME}} par le hostname du pod
sed -i "s/{{HOSTNAME}}/$HOSTNAME/g" /usr/share/nginx/html/index.html
# Démarre Nginx en mode foreground
nginx -g "daemon off;"
