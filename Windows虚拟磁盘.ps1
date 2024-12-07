# 设置记录文件的路径
$RecordFilePath = "C:\Path\To\VHDRecords.txt"

function Create-VHD {
    # 询问用户输入虚拟磁盘的路径
    $VHDPath = Read-Host "请输入虚拟磁盘的完整路径（例如 C:\Path\To\VirtualDisk.vhdx）"

    # 询问用户输入虚拟磁盘的大小（以GB为单位）
    $SizeGB = Read-Host "请输入虚拟磁盘的大小（以GB为单位）"

    # 将大小转换为字节
    $SizeBytes = [int64]$SizeGB * 1GB

    # 创建虚拟磁盘
    New-VHD -Path $VHDPath -SizeBytes $SizeBytes -Dynamic

    # 挂载虚拟磁盘
    Mount-VHD -Path $VHDPath

    # 获取最新的磁盘号
    $Disk = Get-Disk | Where-Object PartitionStyle -Eq 'RAW' | Select-Object -First 1

    # 初始化磁盘
    Initialize-Disk -Number $Disk.Number

    # 创建分区并分配驱动器号
    $Partition = New-Partition -DiskNumber $Disk.Number -UseMaximumSize -AssignDriveLetter

    # 格式化分区为 NTFS
    Format-Volume -DriveLetter $Partition.DriveLetter -FileSystem NTFS -NewFileSystemLabel "VirtualDisk"

    # 设置磁盘策略以提高安全性和可靠性
    Set-Disk -Number $Disk.Number -IsOffline $false -IsReadOnly $false
    Set-StorageSetting -NewFileSystemLabel "VirtualDisk" -IsIntegrityEnabled $true

    # 禁用写缓存以确保数据安全
    Set-Disk -Number $Disk.Number -IsWriteCacheEnabled $false

    # 记录创建的虚拟磁盘信息
    Add-Content -Path $RecordFilePath -Value "$VHDPath,$($Partition.DriveLetter)"

    Write-Host "虚拟磁盘已创建并挂载。驱动器号为 $($Partition.DriveLetter):"
}

function Mount-VHDFromRecord {
    # 显示记录的虚拟磁盘
    if (Test-Path $RecordFilePath) {
        $Records = Get-Content -Path $RecordFilePath
        Write-Host "可挂载的虚拟磁盘："
        $Records | ForEach-Object { Write-Host $_ }
        
        # 询问用户选择挂载哪个虚拟磁盘
        $VHDPath = Read-Host "请输入要挂载的虚拟磁盘路径"
        if ($Records -contains $VHDPath) {
            Mount-VHD -Path $VHDPath.Split(',')[0]
            Write-Host "虚拟磁盘已挂载。"
        } else {
            Write-Host "未找到指定的虚拟磁盘。"
        }
    } else {
        Write-Host "没有记录可用。"
    }
}

function View-VHDRecords {
    # 查看所有记录的虚拟磁盘
    if (Test-Path $RecordFilePath) {
        $Records = Get-Content -Path $RecordFilePath
        Write-Host "已创建的虚拟磁盘："
        $Records | ForEach-Object { Write-Host $_ }
    } else {
        Write-Host "没有记录可用。"
    }
}

# 主菜单
while ($true) {
    Write-Host "`n请选择操作："
    Write-Host "1. 创建新的虚拟磁盘"
    Write-Host "2. 挂载已创建的虚拟磁盘"
    Write-Host "3. 查看已创建的虚拟磁盘"
    Write-Host "4. 退出"
    
    $choice = Read-Host "输入选项编号"
    
    switch ($choice) {
        "1" { Create-VHD }
        "2" { Mount-VHDFromRecord }
        "3" { View-VHDRecords }
        "4" { break }
        default { Write-Host "无效的选项，请重试。" }
    }
}
