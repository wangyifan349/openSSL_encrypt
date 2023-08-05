@echo off
setlocal

:loop
echo 请输入字符串 (或者输入 'exit' 退出):    REM 提示用户输入一个字符串，或者输入 'exit' 退出脚本。
set /p input_string=                       REM 读取用户输入，并将其保存在 'input_string' 变量中。

if "%input_string%"=="exit" goto :eof      REM 如果输入为 'exit'，则退出脚本。

echo %input_string%| openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1" 2> NUL
REM 尝试使用 OpenSSL 进行 AES-256 CBC 解密。
REM '-d' 表示解密，'-aes-256-cbc' 表示 AES-256 CBC 加密模式，'-a' 表示使用 Base64 编码，
REM '-salt' 添加加密时的盐值，'-pbkdf2' 使用 PBKDF2 密钥派生算法，'-pass pass:"..."' 指定密码用于派生加密密钥。
REM '2> NUL' 将错误输出重定向到空设备，以阻止错误信息显示在屏幕上。

if %errorlevel% neq 0 (
    echo 无法解密，进行加密操作:             
    echo %input_string%| openssl enc -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1"
    REM 使用 OpenSSL 再次进行加密，使用相同的加密设置。
) else (
    echo 解密结果:                           REM 如果解密成功，显示解密的结果。
    echo %input_string%| openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1"
    REM 再次解密 'input_string'，以显示解密的结果。
)

goto loop                                  REM 回到循环的开始，以便重复执行过程。

REM 脚本结束。
