#!/bin/bash

# 帮助Linux用户，快速复制图片到指定位置，以实现进一步的加密和解密做准备。

# 提示用户输入源路径和目标路径
read -p "请输入源路径: " source_path
read -p "请输入目标路径: " destination_path

# 检查源路径是否存在
while [ ! -d "$source_path" ]; do
    read -p "源路径不存在，请重新输入源路径: " source_path
done

# 检查目标路径是否存在
while [ ! -d "$destination_path" ]; do
    read -p "目标路径不存在，请重新输入目标路径: " destination_path
done

# 进入源路径，确保find命令在正确的路径下运行
cd "$source_path" || exit 1

# 使用find命令查找所有jpg、jpeg、png文件，并使用while循环逐个处理它们
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | while read -r file_path; do
    # 使用basename命令获取文件名（不含路径）
    file_name=$(basename "$file_path")
    # 使用UUID生成一个随机字符串，并拼接到文件名前面
    # 这样可以确保重名文件不会冲突
    new_file_name="$(uuidgen)_$file_name"
    # 使用cp命令将文件拷贝到目标路径
    cp "$file_path" "$destination_path/$new_file_name"
done

echo "拷贝完成！"

# 进入目标路径，确保find命令在正确的路径下运行
cd "$destination_path" || exit 1

# 使用find命令查找所有jpg、jpeg、png文件，并计算它们的SHA512哈希值
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -exec sha512sum {} + \
| sort -k1,1 \
| uniq -w 128 -d --all-repeated=separate \
| cut -c 135- \
| while read -r duplicate_file; do
    # 删除重复文件
    echo "删除重复文件: $duplicate_file"
    rm "$destination_path/$duplicate_file"
done

echo "重复图片已去除。"
