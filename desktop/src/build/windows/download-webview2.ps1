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

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null

if (-not (Test-Path -LiteralPath $target)) {
    Write-Host "Downloading WebView2 runtime for $Architecture..."
    Invoke-WebRequest `
        -UseBasicParsing `
        -Uri $download.Uri `
        -OutFile $target `
        -ErrorAction Stop
}

$file = Get-Item -LiteralPath $target -ErrorAction Stop
if ($file.Length -lt 1MB) {
    throw "WebView2 runtime download is unexpectedly small: $target"
}
