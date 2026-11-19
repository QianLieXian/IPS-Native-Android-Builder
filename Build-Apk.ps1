[CmdletBinding()]
param(
    [string]$Linux,
    [string]$Proxy,
    [string]$Cache,
    [string]$Output
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
if (!$Linux) {
    $nearby = @((Join-Path $root 'linux'), (Join-Path (Split-Path $root -Parent) 'linux'))
    $Linux = $nearby | Where-Object { Test-Path -LiteralPath $_ -PathType Container } | Select-Object -First 1
}
if (!$Linux) {
    $Linux = (Read-Host 'Path to the extracted Linux game (the linux folder)').Trim('"')
}
if (!$Linux -or !(Test-Path -LiteralPath $Linux -PathType Container)) {
    throw 'The Linux game folder was not found.'
}
$Linux = (Resolve-Path -LiteralPath $Linux).Path
$gameData = Join-Path $Linux 'Isekai Parlor Simulator_Data'
if (!(Test-Path -LiteralPath (Join-Path $gameData 'globalgamemanagers') -PathType Leaf)) {
    throw 'Choose the linux folder containing Isekai Parlor Simulator_Data.'
}
if (!$Cache) { $Cache = Join-Path $root '.build-cache' }
if (!$Output) { $Output = Join-Path $root 'dist' }
$Cache = [IO.Path]::GetFullPath($Cache)
$Output = [IO.Path]::GetFullPath($Output)
if ($Proxy) {
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
}

$runtime = Join-Path $Cache 'python-3.12.10'
$python = Join-Path $runtime 'python.exe'
$runtimeMarker = Join-Path $runtime '.ready'
if (!(Test-Path -LiteralPath $runtimeMarker)) {
    $downloads = Join-Path $Cache 'downloads'
    [IO.Directory]::CreateDirectory($downloads) | Out-Null
    $archive = Join-Path $downloads 'python-3.12.10-embed-amd64.zip'
    $url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'
    if (!(Test-Path -LiteralPath $archive)) {
        & curl.exe -fL --retry 2 --output "$archive.part" $url
        if ($LASTEXITCODE) { throw 'Python download failed.' }
        Move-Item -LiteralPath "$archive.part" -Destination $archive -Force
    }
    $stream = [IO.File]::OpenRead($archive)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '')
    } finally {
        $sha.Dispose()
        $stream.Dispose()
    }
    if ($hash -ne '4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3') {
        throw "Python archive SHA-256 mismatch. Remove the cached archive and retry: $archive"
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Directory]::CreateDirectory($runtime) | Out-Null
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        foreach ($entry in $zip.Entries) {
            if ($entry.Name -ne $entry.FullName) { throw 'Unexpected Python archive path.' }
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $runtime $entry.Name), $true)
        }
    } finally {
        $zip.Dispose()
    }
    $paths = Join-Path $runtime 'python312._pth'
    $contents = [IO.File]::ReadAllText($paths).Replace('#import site', 'import site')
    [IO.File]::WriteAllText($paths, $contents)
    New-Item -ItemType File -Path $runtimeMarker | Out-Null
}
$env:PYTHONUTF8 = '1'
& $python (Join-Path $root 'build.py') $gameData $Cache $Output
exit $LASTEXITCODE
