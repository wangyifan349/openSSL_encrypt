# 由于windows的bat脚本命令行功能有限，这是一种利用Windows powsershell的办法。这个脚本包括了处理文件名冲突和去除重复文件的功能。
# 提示用户输入源路径和目标路径
$sourcePath = Read-Host -Prompt "请输入源路径"
$destinationPath = Read-Host -Prompt "请输入目标路径"

# 检查源路径是否存在
while (-not (Test-Path -Path $sourcePath -PathType Container)) {
    $sourcePath = Read-Host -Prompt "源路径不存在，请重新输入源路径"
}

# 检查目标路径是否存在
while (-not (Test-Path -Path $destinationPath -PathType Container)) {
    $destinationPath = Read-Host -Prompt "目标路径不存在，请重新输入目标路径"
}

# 在源路径中查找所有jpg、jpeg、png文件，并复制到目标路径
Get-ChildItem -Path $sourcePath -Recurse -Include @("*.jpg", "*.jpeg", "*.png") | ForEach-Object {
    $destinationFilePath = Join-Path -Path $destinationPath -ChildPath $_.Name
    $counter = 1

    # 检查文件是否存在，如果存在，加上_2、_3等以防止名称冲突
    while (Test-Path -Path $destinationFilePath) {
        $baseName = $_.BaseName
        $extension = $_.Extension
        $newName = "$baseName`_$counter$extension"
        $destinationFilePath = Join-Path -Path $destinationPath -ChildPath $newName
        $counter++
    }

    # 拷贝文件到目标路径
    Copy-Item -Path $_.FullName -Destination $destinationFilePath
}

Write-Host "拷贝完成！"

# 在目标路径中查找所有jpg、jpeg、png文件，并计算它们的SHA512哈希值
$hashTable = @{}
Get-ChildItem -Path $destinationPath -Recurse -Include @("*.jpg", "*.jpeg", "*.png") | ForEach-Object {
    $hash = Get-FileHash -Path $_.FullName -Algorithm SHA512
    # 检查是否存在具有相同哈希值的文件
    if ($hashTable.Contains($hash.Hash)) {
        # 删除重复文件
        Write-Host "删除重复文件: $($_.FullName)"
        Remove-Item -Path $_.FullName
    } else {
        $hashTable.Add($hash.Hash, $_.FullName)
    }
}

Write-Host "重复图片已去除。"
