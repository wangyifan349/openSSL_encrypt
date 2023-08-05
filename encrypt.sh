#!/bin/bash

# 询问加密路径
read -p "输入被加密的路径: " source_folder
#检查并赋予源文件夹读取权限
if [[ ! -r "$source_folder" ]]; then
    echo "Adding read permission to the source folder..."
    chmod +r "$source_folder"
fi

# Ask for the encryption password
read -sp "输入加密密码： " encryption_password
echo

# Create a temporary folder to store encrypted files
temp_folder=$(mktemp -d)

# Encrypt files using AES-256-CBC with PBKDF2 and overwrite the source files
cd "$source_folder"
for file in *; do
    if [[ ! -w "$file" ]]; then
        echo "正在添加对 '$file' 的写入权限..."
        chmod +w "$file"
    fi

    openssl enc -aes-256-cbc -pbkdf2 -salt -in "$file" -out "$temp_folder/$file.aes" -k "$encryption_password"
    mv "$temp_folder/$file.aes" "$file"
done

# 删除临时文件夹
rm -r "$temp_folder"

echo "加密完成。 所有文件中 '$source_folder' 已经被加密并覆盖"
