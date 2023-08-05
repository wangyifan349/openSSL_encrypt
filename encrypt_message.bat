@echo off
setlocal
REM  可以去https://slproweb.com/products/Win32OpenSSL.html下载Win64 OpenSSL v3.1.2安装即可，全自动傻瓜操作。
REM 检查是否存在 OpenSSL
where openssl > NUL 2>&1
if %errorlevel% neq 0 (
    echo OpenSSL 未安装或未在系统路径中找到。请确保已正确安装 OpenSSL 并配置系统路径。
    pause
    exit /b 1
)
:loop
echo 请输入字符串 (或者输入 'exit' 退出):
set /p input_string=

if "%input_string%"=="exit" goto :eof

echo %input_string%| openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1" 2> NUL
REM pass冒号后面填写密码
if %errorlevel% neq 0 (
    echo 无法解密，进行加密操作:
    echo %input_string%| openssl enc -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1" | clip
    echo 已加密并复制结果到剪贴板。
) else (
    echo 解密结果:
    echo %input_string%| openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -pass pass:"jflsx.wijJfflscdIlSAqkfmc@jfeio1"
)

goto loop
