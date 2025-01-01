#!/bin/bash

# ==============================
# 交互式 SSL 证书生成脚本
# 支持 Nginx 自动检测和证书目录创建
# 支持 cat 查看生成的证书内容
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
echo -e "${CYAN}欢迎使用 SSL 证书生成脚本！${RESET}"
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
    echo -e "${CYAN}以下是 Nginx 配置示例，请根据需要修改您的 Nginx 配置文件：${RESET}"
    echo -e "${YELLOW}"
    echo "server {"
    echo "    listen 443 ssl;"
    echo "    server_name $DOMAIN;"
    echo ""
    echo "    ssl_certificate $NGINX_CERT_DIR/$DOMAIN.crt;"
    echo "    ssl_certificate_key $NGINX_CERT_DIR/$DOMAIN.key;"
    echo ""
    echo "    location / {"
    echo "        root /var/www/html;"
    echo "        index index.html;"
    echo "    }"
    echo "}"
    echo -e "${RESET}"
    echo -e "${CYAN}完成后，请重启 Nginx 服务：${RESET}"
    echo -e "${YELLOW}sudo systemctl restart nginx${RESET}"
else
    echo -e "${YELLOW}未检测到 Nginx 安装，跳过证书复制和配置步骤。${RESET}"
    echo -e "${YELLOW}您可以手动将证书复制到 Nginx 的证书目录，并修改配置文件。${RESET}"
fi

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
