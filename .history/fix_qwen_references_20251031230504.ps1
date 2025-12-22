# 批量替换Qwen2.5到Qwen3的PowerShell脚本

# 替换列表（按顺序执行，从最具体到最通用）
$replacements = @(
    @{Old="Qwen/Qwen2.5-1.5B-Instruct"; New="Qwen/Qwen3-1.7B-Instruct"},
    @{Old="Qwen/Qwen2.5-7B-Instruct"; New="Qwen/Qwen3-8B-Instruct"},
    @{Old="Qwen2.5-7B-zh"; New="Qwen3-1.7B-zh"},
    @{Old="qwen2.5-7b-zh"; New="qwen3-1.7b-zh"},
    @{Old="Qwen2.5-7B"; New="Qwen3-1.7B"},
    @{Old="qwen2.5-7b"; New="qwen3-1.7b"},
    @{Old="Qwen2.5-1.5B"; New="Qwen3-1.7B"},
    @{Old="qwen2.5-1.5b"; New="qwen3-1.7b"},
    @{Old="qwen2.5-1.8b"; New="qwen3-1.7b"},
    @{Old="Qwen1.5-7B"; New="Qwen3-8B"}
)

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

