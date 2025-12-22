# 批量替换Qwen2.5到Qwen3的PowerShell脚本

$replacements = @{
    "Qwen2.5-7B-zh" = "Qwen3-1.7B-zh"
    "Qwen2.5-7B" = "Qwen3-1.7B"
    "Qwen2.5-1.5B" = "Qwen3-1.7B"
    "qwen2.5-7b-zh" = "qwen3-1.7b-zh"
    "qwen2.5-7b" = "qwen3-1.7b"
    "qwen2.5-1.5b" = "qwen3-1.7b"
    "qwen2.5-1.8b" = "qwen3-1.7b"
    "Qwen/Qwen2.5-1.5B-Instruct" = "Qwen/Qwen3-1.7B-Instruct"
    "Qwen/Qwen2.5-7B-Instruct" = "Qwen/Qwen3-8B-Instruct"
    "Qwen1.5-7B" = "Qwen3-8B"
}

# 排除的文件和目录
$excludePatterns = @(
    "*\.history\*",
    "*\.venv\*",
    "*\issues\*",
    "*\llama.cpp\*",
    "*\docs\*",
    "*enhanced_model_downloader.py"
)

# 获取所有需要处理的文件
$files = Get-ChildItem -Recurse -File | Where-Object {
    $file = $_
    $_.Extension -in '.py','.json','.yaml' -and
    -not ($excludePatterns | Where-Object { $file.FullName -like $_ })
}

$totalFiles = 0
$totalReplacements = 0

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    
    $originalContent = $content
    $fileReplacements = 0
    
    foreach ($old in $replacements.Keys) {
        $new = $replacements[$old]
        if ($content -match [regex]::Escape($old)) {
            $content = $content -replace [regex]::Escape($old), $new
            $fileReplacements++
        }
    }
    
    if ($content -ne $originalContent) {
        Set-Content $file.FullName -Value $content -Encoding UTF8 -NoNewline
        $totalFiles++
        $totalReplacements += $fileReplacements
        Write-Host "✅ 修复: $($file.FullName) ($fileReplacements 处替换)"
    }
}

Write-Host "`n📊 总计:"
Write-Host "  - 修复文件数: $totalFiles"
Write-Host "  - 总替换次数: $totalReplacements"

