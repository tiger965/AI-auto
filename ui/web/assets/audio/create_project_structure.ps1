
# 设置目标路径
$targetPath = "C:\Users\tiger\Desktop\key\code\organized_project"

# 确保路径存在
if (-Not (Test-Path $targetPath)) {
    New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
}

# 要创建的子目录
$folders = @(
    "api", "config", "core", "examples", "misc",
    "modules", "system", "tests", "ui", "utils"
)

# 创建子目录
foreach ($folder in $folders) {
    $folderPath = Join-Path $targetPath $folder
    if (-Not (Test-Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath | Out-Null
        Write-Host "📁 创建目录：$folderPath"
    } else {
        Write-Host "📁 已存在目录：$folderPath"
    }
}

# 要创建的文件和内容
$files = @{
    "__init__.py" = "# __init__"
    "main.py" = "# main entry`nif __name__ -eq '__main__':`n    print('Hello from main')"
    "README.md" = "# 项目说明"
    "requirements.txt" = "# 请在此列出依赖库"
}

# 创建文件并验证写入
foreach ($file in $files.Keys) {
    $filePath = Join-Path $targetPath $file
    Set-Content -Path $filePath -Value $files[$file] -Force
    Write-Host "📄 写入文件：$filePath，内容如下：" -ForegroundColor Cyan
    Get-Content $filePath
    Write-Host "`n-----------------------------`n"
}

Write-Host "`n✅ 所有文件与文件夹操作完成，请刷新资源管理器查看。" -ForegroundColor Green
