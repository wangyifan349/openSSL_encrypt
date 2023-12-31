#!/bin/bash

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
    destination_file_path="$destination_path/$file_name"

    # 检查文件是否存在，如果存在，加上_2、_3等以防止名称冲突
    counter=1
    while [ -e "$destination_file_path" ]; do
        base_name="${file_name%.*}"
        extension="${file_name##*.}"
        counter=$((counter+1))
        file_name="${base_name}_$counter.$extension"
        destination_file_path="$destination_path/$file_name"
    done

    # 使用cp命令将文件拷贝到目标路径
    cp "$file_path" "$destination_file_path"
done

echo "拷贝完成！"

# 进入目标路径，确保find命令在正确的路径下运行
cd "$destination_path" || exit 1

# 使用find命令查找所有jpg、jpeg、png文件，并计算它们的SHA512哈希值
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -exec sha512sum {} + \
| sort -k1,1 \
| uniq -w 128 -d --all-repeated=separate \
| awk '{print substr($0, index($0,$2))}' \
| while read -r duplicate_file; do
    # 删除重复文件
    echo "删除重复文件: $duplicate_file"
    rm "$duplicate_file"  # Use the relative path directly
done

echo "重复图片已去除。"
