@echo off
REM 考虑到尊重windows的用户，这里补充一个脚本，但是Windows的批处理脚本语言并不如Bash脚本强大。
REM 批处理脚本没有内置的方法来处理文件名冲突的问题，可以使用python3在windows下来实现比较好。

setlocal enabledelayedexpansion

set /p source_path="请输入源路径: "
set /p destination_path="请输入目标路径: "

:: 复制源路径中的所有图片文件到目标路径
REM 脚本先使用robocopy复制源路径中的所有图片文件到目标路径。
robocopy "%source_path%" "%destination_path%" *.jpg *.jpeg *.png /NFL /NDL

:: 遍历目标路径中的所有图片文件

for /R "%destination_path%" %%F in (*.jpg, *.jpeg, *.png) do (
    :: 计算文件的SHA512哈希值，并将其存储到临时文件中
    CertUtil -hashfile "%%F" SHA512 >temp.txt
:: 使用CertUtil计算每个文件的SHA512哈希值。
    :: 读取临时文件的第一行（即SHA512哈希值）
    set /p hash=<temp.txt
    :: 检查是否已经存在具有相同哈希值的文件
    if exist "!hash!.hash" (
        echo 删除重复文件: %%F
        del "%%F"
    ) else (
        :: 如果不存在具有相同哈希值的文件，则将哈希值存储为一个文件，以便于后续的查重
        echo.>"!hash!.hash"
    )
)
:: 删除临时文件
del *.hash temp.txt
