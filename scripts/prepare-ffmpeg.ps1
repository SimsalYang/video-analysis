# Download and extract minimal FFmpeg binaries for bundling
$url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$dest = "vendor/ffmpeg.zip"
$tmpDir = "vendor/ffmpeg-tmp"

if (!(Test-Path "vendor")) {
    New-Item -ItemType Directory -Path "vendor" | Out-Null
}

# Download with error handling
try {
    Write-Host "Downloading FFmpeg..."
    Invoke-WebRequest -Uri $url -OutFile $dest -ErrorAction Stop
} catch {
    Write-Host "ERROR: Failed to download FFmpeg: $_"
    exit 1
}

# Extract with error handling
try {
    Write-Host "Extracting..."
    if (Test-Path $tmpDir) {
        Remove-Item $tmpDir -Recurse -Force
    }
    Expand-Archive -Path $dest -DestinationPath $tmpDir -Force -ErrorAction Stop
} catch {
    Write-Host "ERROR: Failed to extract FFmpeg: $_"
    Remove-Item $dest -Force -EA SilentlyContinue
    exit 1
}

# Find the bin directory
$binDir = $null
try {
    $extractedDirs = Get-ChildItem $tmpDir -Directory
    if ($extractedDirs.Count -eq 0) {
        throw "No directories found in extracted archive"
    }
    $binDir = Join-Path $extractedDirs[0].FullName "bin"
    if (!(Test-Path $binDir)) {
        throw "bin directory not found in archive"
    }
} catch {
    Write-Host "ERROR: $($_)"
    Remove-Item $dest -Force -EA SilentlyContinue
    Remove-Item $tmpDir -Recurse -Force -EA SilentlyContinue
    exit 1
}

# Prepare output directory
if (!(Test-Path "vendor/ffmpeg")) {
    New-Item -ItemType Directory -Path "vendor/ffmpeg" | Out-Null
}

# Copy binaries
try {
    Copy-Item (Join-Path $binDir "ffmpeg.exe") "vendor/ffmpeg/ffmpeg.exe" -ErrorAction Stop
    Copy-Item (Join-Path $binDir "ffprobe.exe") "vendor/ffmpeg/ffprobe.exe" -ErrorAction Stop
} catch {
    Write-Host "ERROR: Failed to copy FFmpeg binaries: $_"
    Remove-Item $dest -Force -EA SilentlyContinue
    Remove-Item $tmpDir -Recurse -Force -EA SilentlyContinue
    exit 1
}

# Cleanup
Remove-Item $dest -Force -EA SilentlyContinue
Remove-Item $tmpDir -Recurse -Force -EA SilentlyContinue

Write-Host "Done. FFmpeg binaries in vendor/ffmpeg/"