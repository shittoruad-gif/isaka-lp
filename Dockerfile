FROM nginx:1.27-alpine

# 静的LPを配信
COPY index.html /usr/share/nginx/html/index.html

# SPA的な挙動は不要。シンプルに index.html を配信
RUN printf 'server {\n\
  listen 80;\n\
  server_name _;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
  location / { try_files $uri $uri/ /index.html; }\n\
  add_header X-Robots-Tag "noindex, nofollow" always;\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -q -O /dev/null http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
