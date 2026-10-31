$ErrorActionPreference = 'Stop'
$inputPath = (Get-ChildItem -LiteralPath 'C:\desktop\botlearn' -Filter '*.docx' | Select-Object -First 1).FullName
$outDir = 'C:\desktop\botlearn\qa\paper'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$pdfPath = Join-Path $outDir 'paper.pdf'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
Write-Output "input=$inputPath"
Write-Output "documents=$($word.Documents.Count)"
try {
    $document = $word.Documents.Open($inputPath)
    Write-Output "opened=$($document.Name)"
    try {
        $document.ExportAsFixedFormat($pdfPath, 17)
        Write-Output "exported=$pdfPath"
    } finally {
        $document.Close($false)
    }
} finally {
    $word.Quit()
}
Get-Item -LiteralPath $pdfPath | Select-Object FullName,Length
