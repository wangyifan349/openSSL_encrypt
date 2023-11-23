#!/bin/bash

# 询问解密路径
read -p "输入被解密的路径: " encrypted_folder
# 检查加密文件夹是否存在
if [[ ! -d "$encrypted_folder" ]]; then
    echo "指定的文件夹不存在，请检查路径。"
    exit 1
fi

# 请求输入解密密码
read -sp "输入解密密码： " decryption_password
echo

# 创建临时文件夹用于存储解密文件
temp_folder=$(mktemp -d)

# 进入加密文件夹
cd "$encrypted_folder" || exit 1

# 使用AES-256-CBC算法解密所有加密文件，并将解密后的文件存放在临时文件夹中
find . -type f -name "*.aes" -print0 | while IFS= read -r -d '' file; do
    original_file="${file%.aes}" # 移除.aes扩展名以得到原始文件名
    # 解密每个文件并将其存储在临时文件夹中
    openssl enc -aes-256-cbc -pbkdf2 -d -salt -in "$file" -out "$temp_folder/$original_file" -k "$decryption_password" && {
        # 如果解密成功，则用解密文件替换加密文件
        mv -f "$temp_folder/$original_file" "$original_file"
        echo "已解密: $original_file"
    } || echo "解密失败: $file"
done

# 删除临时文件夹
rm -r "$temp_folder"

echo "解密完成。所有文件在 '$encrypted_folder' 已经被解密并覆盖。"
