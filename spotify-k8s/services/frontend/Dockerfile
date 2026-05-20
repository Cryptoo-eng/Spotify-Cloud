FROM nginx:alpine
LABEL service="spotify-frontend"
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s CMD wget -qO- http://localhost/health || exit 1
