#!/bin/bash

# 询问加密路径
read -p "输入被加密的路径: " source_folder
# 检查源文件夹是否存在
if [[ ! -d "$source_folder" ]]; then
    echo "指定的文件夹不存在，请检查路径。"
    exit 1
fi

# 检查并赋予源文件夹读取权限
if [[ ! -r "$source_folder" ]]; then
    echo "正在为源文件夹添加读取权限..."
    chmod +r "$source_folder"
fi

# 请求输入加密密码
read -sp "输入加密密码： " encryption_password
echo

# 创建临时文件夹用于存储加密文件
temp_folder=$(mktemp -d)

# 进入源文件夹
cd "$source_folder" || exit 1

# 使用AES-256-CBC算法和PBKDF2加密所有文件，并将加密后的文件存放在临时文件夹中
find . -type f ! -name "*.aes" -print0 | while IFS= read -r -d '' file; do
    # 加密每个文件并将其存储在临时文件夹中
    openssl enc -aes-256-cbc -pbkdf2 -salt -in "$file" -out "$temp_folder/$file.aes" -k "$encryption_password" && {
        # 如果加密成功，则用加密文件替换原始文件
        mv -f "$temp_folder/$file.aes" "$file"
        echo "已加密: $file"
    }
done

# 删除临时文件夹
rm -r "$temp_folder"

echo "加密完成。所有文件在 '$source_folder' 已经被加密并覆盖。"
