#!/bin/bash

# ==============================
# 交互式 SSL 证书生成和部署脚本
# 支持 Nginx 自动检测和证书目录创建
# 加强 HTTPS 安全性配置
# ==============================

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

# 分隔线
SEPARATOR="============================================================"

# 欢迎信息
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}欢迎使用交互式 SSL 证书生成和部署脚本！${RESET}"
echo -e "${CYAN}请根据提示输入相关信息，所有文件将生成在 ./certs 目录中。${RESET}"
echo -e "${CYAN}${SEPARATOR}${RESET}"

# 1. 询问用户输入域名
read -p "$(echo -e ${BLUE}请输入域名（如 example.com）：${RESET} )" DOMAIN
if [[ -z "$DOMAIN" ]]; then
    echo -e "${RED}错误：域名不能为空！${RESET}"
    exit 1
fi

# 2. 询问证书有效期（天数）
read -p "$(echo -e ${BLUE}请输入证书有效期（默认 365 天）：${RESET} )" DAYS
DAYS=${DAYS:-365}  # 如果用户未输入，则默认 365 天

# 3. 询问私钥长度
read -p "$(echo -e ${BLUE}请输入私钥长度（默认 2048 位）：${RESET} )" KEY_SIZE
KEY_SIZE=${KEY_SIZE:-2048}  # 如果用户未输入，则默认 2048 位

# 4. 设置输出目录
OUTPUT_DIR="./certs"
mkdir -p "$OUTPUT_DIR"

# 开始生成证书
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}开始生成证书，请稍候...${RESET}"

# 5. 生成私钥
echo -e "${GREEN}生成私钥...${RESET}"
openssl genrsa -out "$OUTPUT_DIR/$DOMAIN.key" $KEY_SIZE

# 6. 生成证书签名请求 (CSR)
echo -e "${GREEN}生成证书签名请求 (CSR)...${RESET}"
openssl req -new -key "$OUTPUT_DIR/$DOMAIN.key" -out "$OUTPUT_DIR/$DOMAIN.csr" \
    -subj "/C=CN/ST=Default/L=Default/O=Default/OU=Default/CN=$DOMAIN"

# 7. 生成自签名证书
echo -e "${GREEN}生成自签名证书...${RESET}"
openssl x509 -req -days $DAYS -in "$OUTPUT_DIR/$DOMAIN.csr" -signkey "$OUTPUT_DIR/$DOMAIN.key" -out "$OUTPUT_DIR/$DOMAIN.crt"

# 8. 生成 PEM 格式的完整证书链
echo -e "${GREEN}生成 PEM 格式的完整证书链...${RESET}"
cat "$OUTPUT_DIR/$DOMAIN.crt" "$OUTPUT_DIR/$DOMAIN.key" > "$OUTPUT_DIR/$DOMAIN.pem"
# 检测是否安装 Nginx
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}检测 Nginx 是否已安装...${RESET}"
if command -v nginx >/dev/null 2>&1; then
    echo -e "${GREEN}检测到 Nginx 已安装！${RESET}"
    # 创建 Nginx 的证书目录
    NGINX_CERT_DIR="/etc/nginx/certs"
    echo -e "${GREEN}创建 Nginx 证书目录：$NGINX_CERT_DIR${RESET}"
    sudo mkdir -p "$NGINX_CERT_DIR"
    # 复制证书到 Nginx 目录
    echo -e "${GREEN}复制证书文件到 Nginx 目录...${RESET}"
    sudo cp "$OUTPUT_DIR/$DOMAIN.crt" "$NGINX_CERT_DIR/"
    sudo cp "$OUTPUT_DIR/$DOMAIN.key" "$NGINX_CERT_DIR/"
    sudo cp "$OUTPUT_DIR/$DOMAIN.pem" "$NGINX_CERT_DIR/"
    echo -e "${GREEN}证书已复制到 $NGINX_CERT_DIR${RESET}"
    # 提示用户如何配置 Nginx
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}以下是推荐的 Nginx 配置，请根据需要修改您的 Nginx 配置文件：${RESET}"
echo -e "${YELLOW}"
cat <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    ssl_certificate /etc/nginx/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/nginx/certs/$DOMAIN.key;
    # 启用 OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/certs/$DOMAIN.crt;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;
    # 启用 HSTS (强制 HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    # 禁用不安全的协议特性
    ssl_compression off;
    ssl_early_data off;
    # 安全头部配置
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "no-referrer-when-downgrade";
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()";
    # 内容安全策略 (CSP)
    add_header Content-Security-Policy "
        default-src 'self'; 
        script-src 'self' https://cdnjs.cloudflare.com https://ajax.googleapis.com https://cdn.jsdelivr.net https://code.jquery.com; 
        style-src 'self' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; 
        font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; 
        img-src 'self' data: https://cdn.example.com https://via.placeholder.com; 
        connect-src 'self'; 
        frame-ancestors 'none';
    ";
    # 静态文件缓存配置
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg|eot|otf|ttc)$ {
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }
    # 防止访问隐藏文件（以 . 开头的文件，如 .env）
    location ~ /\. {
        deny all;
    }
    # 防止访问备份文件
    location ~* \.(bak|old|backup|swp|tmp|dist)$ {
        deny all;
    }
    # 限制请求体大小
    client_max_body_size 10M;
    # 限制连接数和请求速率
    limit_req_zone \$binary_remote_addr zone=one:10m rate=10r/s;
    limit_conn_zone \$binary_remote_addr zone=addr:10m;
    location / {
        limit_req zone=one burst=20 nodelay;
        limit_conn addr 10;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    # 错误页面配置
    error_page 403 /403.html;
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location = /403.html {
        root /var/www/html;
    }
    location = /404.html {
        root /var/www/html;
    }
    location = /50x.html {
        root /var/www/html;
    }
    # 配置允许访问、读取、列出和下载的目录
    location /files/ {
        root /var/www/html;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
        types {
            text/plain txt;
            application/octet-stream bin;
        }
        allow all;
    }
}
server {
    listen 80;
    server_name $DOMAIN;
    # 自动跳转到 HTTPS
    return 301 https://\$host\$request_uri;
}
EOF
echo -e "${RESET}"
echo -e "${CYAN}完成后，请重启 Nginx 服务：${RESET}"
echo -e "${YELLOW}sudo systemctl restart nginx${RESET}"


# 提供查看证书内容的选项
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}是否需要查看生成的证书内容？${RESET}"
read -p "$(echo -e ${BLUE}输入 yes 或 no（默认 no）：${RESET}) " VIEW_CERT
VIEW_CERT=${VIEW_CERT:-no}

if [[ "$VIEW_CERT" == "yes" ]]; then
    echo -e "${CYAN}私钥内容：${RESET}"
    echo -e "${YELLOW}"
    cat "$OUTPUT_DIR/$DOMAIN.key"
    echo -e "${RESET}"

    echo -e "${CYAN}证书内容：${RESET}"
    echo -e "${YELLOW}"
    cat "$OUTPUT_DIR/$DOMAIN.crt"
    echo -e "${RESET}"
fi

# 输出结果和文件管理说明
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}证书生成完成，所有文件存储在目录：$OUTPUT_DIR${RESET}"
echo -e "${CYAN}生成的文件包括：${RESET}"
echo -e "${GREEN}  - 私钥：$OUTPUT_DIR/$DOMAIN.key${RESET}"
echo -e "${GREEN}  - 自签名证书：$OUTPUT_DIR/$DOMAIN.crt${RESET}"
echo -e "${GREEN}  - PEM 文件：$OUTPUT_DIR/$DOMAIN.pem${RESET}"
echo -e "${CYAN}${SEPARATOR}${RESET}"
echo -e "${CYAN}完成！请根据需要将证书文件部署到相应的服务器或系统中。${RESET}"










server {
    # 监听 443 端口，启用 SSL 和 HTTP/2
    listen 443 ssl http2;
    server_name example.com; # 将 example.com 替换为您的域名
    # SSL 证书路径
    ssl_certificate /etc/nginx/certs/example.com.crt;
    ssl_certificate_key /etc/nginx/certs/example.com.key;
    # 启用 OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/certs/example.com.crt;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;
    # 启用 HSTS (强制 HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    # 安全头部配置
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "no-referrer-when-downgrade";
    # 内容安全策略（允许常见外部 CDN）
    add_header Content-Security-Policy "
        default-src 'self'; 
        script-src 'self' https://cdnjs.cloudflare.com https://ajax.googleapis.com https://cdn.jsdelivr.net https://code.jquery.com; 
        style-src 'self' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; 
        font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; 
        img-src 'self' data: https://cdn.example.com https://via.placeholder.com; 
        connect-src 'self'; 
        frame-ancestors 'none';
    ";
    # 限制浏览器 API 的使用
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()";
    # 禁用不安全的协议特性
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_compression off;
    ssl_early_data off;
    # 反向代理配置
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_cache_bypass $http_upgrade;
    }
    # 静态文件缓存配置
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg|eot|otf|ttc)$ {
        expires 30d;
        access_log off;
        add_header Cache-Control "public";
    }
    # 防止访问隐藏文件（以 . 开头的文件，如 .env）
    location ~ /\. {
        deny all;
    }
    # 防止访问备份文件
    location ~* \.(bak|old|backup|swp|tmp|dist)$ {
        deny all;
    }
    # 限制请求体大小
    client_max_body_size 10M;
    # 限制连接数和请求速率
    limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    location / {
        limit_req zone=one burst=20 nodelay;
        limit_conn addr 10;
    }
    # 错误页面配置
    error_page 403 /403.html;
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location = /403.html {
        root /var/www/html;
    }
    location = /404.html {
        root /var/www/html;
    }
    location = /50x.html {
        root /var/www/html;
    }
    # 配置允许访问、读取、列出和下载的目录
    location /files/ {
        root /var/www/html; # 替换为您的实际文件目录路径
        autoindex on; # 启用目录列表功能
        autoindex_exact_size off; # 显示文件大小（更友好显示）
        autoindex_localtime on; # 显示本地时间
        # 允许下载文件
        types {
            text/plain txt;
            application/octet-stream bin;
        }
        # 安全性：限制目录访问到指定路径
        allow all; # 允许所有用户访问
    }
}

# 如果需要支持 HTTP 自动跳转到 HTTPS
server {
    listen 80;
    server_name example.com;
    # 自动跳转到 HTTPS
    return 301 https://$host$request_uri;
}


