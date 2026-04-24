$ErrorActionPreference = "Stop"

$ApiBaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://127.0.0.1:5000" }
$DatasetDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InvoiceDir = Join-Path $DatasetDir "invoices"

$AllowedExtensions = @(".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff")

Get-ChildItem -Path $InvoiceDir -File |
    Where-Object { $AllowedExtensions -contains $_.Extension.ToLowerInvariant() } |
    Sort-Object Name |
    ForEach-Object {
    Write-Host "Uploading $($_.Name) ..."
    curl.exe -s -X POST "$ApiBaseUrl/api/invoices" -F "files=@$($_.FullName)"
    Write-Host ""
}

Write-Host "Done. List processed invoices with:"
Write-Host "curl.exe $ApiBaseUrl/api/invoices"
