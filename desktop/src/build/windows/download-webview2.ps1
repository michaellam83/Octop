param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("amd64", "arm64")]
    [string]$Architecture
)

$downloads = @{
    amd64 = @{
        Uri      = "https://go.microsoft.com/fwlink/?linkid=2124701"
        FileName = "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
    }
    arm64 = @{
        Uri      = "https://go.microsoft.com/fwlink/?linkid=2099616"
        FileName = "MicrosoftEdgeWebView2RuntimeInstallerARM64.exe"
    }
}

$download = $downloads[$Architecture]
$targetDirectory = Join-Path $PSScriptRoot "nsis"
$target = Join-Path $targetDirectory $download.FileName
$partial = "$target.download"

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null

if (-not (Test-Path -LiteralPath $target)) {
    Write-Host "Downloading WebView2 runtime for $Architecture..."
    Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath $partial
    & curl.exe `
        --fail `
        --location `
        --show-error `
        --retry 4 `
        --retry-all-errors `
        --retry-delay 5 `
        --max-time 900 `
        --output $partial `
        $download.Uri
    if ($LASTEXITCODE -ne 0) {
        throw "WebView2 runtime download failed with curl exit code $LASTEXITCODE"
    }

    if (-not (Test-Path -LiteralPath $partial -PathType Leaf)) {
        throw "WebView2 runtime download did not create a file: $partial"
    }
    Move-Item -Force -LiteralPath $partial -Destination $target
}

$file = Get-Item -LiteralPath $target -ErrorAction Stop
if ($file.Length -lt 1MB) {
    throw "WebView2 runtime download is unexpectedly small: $target"
}
Write-Host "WebView2 runtime ready: $($file.Name) ($($file.Length) bytes)"
