FROM nginx:1.27-alpine

# 静的LP・関連ページ・アセットを配信
COPY index.html tokushoho.html privacy.html /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/

# IPv4/IPv6 両方で待受。ヘルスチェック互換のため [::]:80 も listen
RUN printf 'server {\n\
  listen 80;\n\
  listen [::]:80;\n\
  server_name _;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
  location / { try_files $uri $uri/ /index.html; }\n\
  add_header X-Robots-Tag "noindex, nofollow" always;\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
  CMD wget -q -O /dev/null http://127.0.0.1:80/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
