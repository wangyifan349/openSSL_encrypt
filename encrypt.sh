#!/bin/bash

# 询问加密文件夹位置
read -p "输入加密文件夹的路径： " encrypted_folder

# 检查并授予加密文件夹的读取权限
if [[ ! -r "$encrypted_folder" ]]; then
    echo "添加对加密文件夹的读取权限..."
    chmod +r "$encrypted_folder"
fi

# 要求输入解密密码
read -sp "输入解密的密码: " decryption_password
echo

# 创建一个临时文件夹来存储解密的文件
temp_folder=$(mktemp -d)

# 使用 AES-256-CBC 和 PBKDF2 解密文件并覆盖加密文件
cd "$encrypted_folder"
for file in *; do
    if [[ ! -w "$file" ]]; then
        echo "Adding write permission to '$file'..."
        chmod +w "$file"
    fi

    # 尝试解密文件，如果解密失败则输出错误信息并继续下一个文件
    if openssl enc -d -aes-256-cbc -pbkdf2 -in "$file" -out "$temp_folder/$file" -k "$decryption_password"; then
        mv "$temp_folder/$file" "$file"
    else
        echo "解密失败：'$file'"
    fi
done

# 删除临时文件夹
rm -r "$temp_folder"

echo "解密完成。 所有文件位于 '$encrypted_folder' 已被解密并覆盖"
