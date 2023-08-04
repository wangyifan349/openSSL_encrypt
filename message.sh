#!/bin/bash
#实际使用情况，不应该用预定密码，这里通过安全方式，协商了预定义的密码。
if command -v xclip &>/dev/null; then
  echo "xclip 已安装。"
else
  echo "xclip 未安装。"
  read -p "是否要安装 xclip？(y/n): " choice
  case "$choice" in
    [Yy]* )
      sudo apt update
      sudo apt install xclip
      echo "xclip 已安装。"
      ;;
    [Nn]* )
      echo "将不安装 xclip。"
      ;;
    * )
      echo "无效的选择，将不安装 xclip。"
      ;;
  esac
fi
while true; do
    echo -n "请输入字符串 (或者输入 'exit' 退出): "
    read -s input_string
    echo

    if [ "$input_string" == "exit" ]; then
        break
    fi

    decrypted_string=$(echo "$input_string" | openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1" 2> /dev/null)

    if [ $? -ne 0 ]; then
        echo "无法解密，进行加密操作:"
        encrypted_string=$(echo "$input_string" | openssl enc -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1")

        echo "$encrypted_string"
        echo "$encrypted_string" | xclip -selection clipboard
        echo "已复制加密结果到剪贴板。"
    else
        echo "解密结果:"
        echo "$decrypted_string"
    fi
done
