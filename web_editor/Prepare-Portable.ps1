$ErrorActionPreference = 'Stop'
function FileHash([string]$Path) {
    $taskHash = [Security.Cryptography.SHA256]::Create()
    $taskStream = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($taskHash.ComputeHash($taskStream)).Replace('-', '').ToLowerInvariant() }
    finally { $taskStream.Dispose(); $taskHash.Dispose() }
}
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskManifestPath = Join-Path $PSScriptRoot 'release.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
$taskMarker = Join-Path $taskRoot '.runtime-ready.json'
$taskFingerprint = FileHash $taskManifestPath
if (Test-Path -LiteralPath $taskMarker) {
    $taskReady = Get-Content -LiteralPath $taskMarker -Raw | ConvertFrom-Json
    if ($taskReady.fingerprint -eq $taskFingerprint -and $taskReady.root -eq $taskRoot -and
        (Test-Path -LiteralPath (Join-Path $taskRoot 'runtime\python.exe')) -and
        (Test-Path -LiteralPath (Join-Path $taskRoot 'models\flow_matching_best.pth')) -and
        (Test-Path -LiteralPath (Join-Path $taskRoot 'models\clip\model.safetensors'))) { exit 0 }
}
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
function LongPath([string]$Path) {
    if ($Path.StartsWith('\\')) { return '\\?\UNC\' + $Path.Substring(2) }
    return '\\?\' + $Path
}
function SafeTarget([string]$Name) {
    if ($Name -notmatch '^(runtime|models)/' -or $Name -match '[:\\]' -or
        ($Name.Split('/') -contains '..') -or ($Name.Split('/') -contains '.')) { throw "Invalid package path: $Name" }
    $taskTarget = [IO.Path]::GetFullPath((Join-Path $taskRoot $Name.Replace('/', '\')))
    if (-not $taskTarget.StartsWith($taskRoot+'\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive target outside package.' }
    $taskAncestor = [IO.DirectoryInfo]$taskRoot
    while ($null -ne $taskAncestor -and $taskAncestor.FullName.Length -ge $taskRoot.Length) {
        if ($taskAncestor.Exists -and ($taskAncestor.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Package folders must not be links.' }
        $taskAncestor = $taskAncestor.Parent
    }
    $taskParent = [IO.Path]::GetDirectoryName($taskTarget)
    while ($taskParent.Length -gt $taskRoot.Length) {
        if ([IO.Directory]::Exists((LongPath $taskParent)) -and
            ([IO.File]::GetAttributes((LongPath $taskParent)) -band [IO.FileAttributes]::ReparsePoint)) { throw 'Archive directory is a link.' }
        $taskParent = [IO.Path]::GetDirectoryName($taskParent)
    }
    if ([IO.File]::Exists((LongPath $taskTarget)) -and
        ([IO.File]::GetAttributes((LongPath $taskTarget)) -band [IO.FileAttributes]::ReparsePoint)) { throw 'Archive file is a link.' }
    return $taskTarget
}
Write-Host 'Text2Floorplan: preparing the offline runtime. First launch only; this may take several minutes.'
$taskParts = @()
foreach ($taskPart in $taskManifest.parts) {
    if ($taskPart.name -notmatch '^Text2Floorplan-Web-Data-[0-9]+\.zip$') { throw 'Invalid data archive name.' }
    $taskSource = $null
    $taskSearch = $taskRoot
    # Explorer's default Extract All adds a wrapper directory around the ZIP root.
    for ($taskLevel = 0; $taskLevel -lt 3 -and $taskSearch; $taskLevel++) {
        $taskCandidate = Join-Path $taskSearch $taskPart.name
        if (Test-Path -LiteralPath $taskCandidate) { $taskSource = $taskCandidate; break }
        $taskSearch = [IO.Path]::GetDirectoryName($taskSearch)
    }
    if (-not $taskSource) { throw "Missing $($taskPart.name). Download every data ZIP into the same folder as the main ZIP before extracting it." }
    if ((Get-Item -LiteralPath $taskSource).Length -ne $taskPart.size -or
        (FileHash $taskSource) -ne $taskPart.sha256) { throw "Checksum mismatch: $($taskPart.name). Download it again." }
    $taskParts += @{source=$taskSource; part=$taskPart}
}
$taskDrive = New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($taskRoot))
if ($taskDrive.AvailableFreeSpace -lt ([long]$taskManifest.unpacked_bytes + 536870912)) { throw 'Insufficient free space to extract the runtime and models.' }
foreach ($taskPart in $taskParts) {
    Write-Host ('Extracting '+$taskPart.part.name)
    $taskZip = [IO.Compression.ZipFile]::OpenRead((LongPath $taskPart.source))
    try {
        foreach ($taskEntry in $taskZip.Entries) {
            if ($taskEntry.FullName.EndsWith('/')) { continue }
            $taskTarget = SafeTarget $taskEntry.FullName
            [IO.Directory]::CreateDirectory((LongPath ([IO.Path]::GetDirectoryName($taskTarget)))) | Out-Null
            $taskInput = $taskEntry.Open()
            try {
                $taskOutput = [IO.File]::Open((LongPath $taskTarget), [IO.FileMode]::Create, [IO.FileAccess]::Write)
                try { $taskInput.CopyTo($taskOutput) } finally { $taskOutput.Dispose() }
            } finally { $taskInput.Dispose() }
            if (([IO.FileInfo](LongPath $taskTarget)).Length -ne $taskEntry.Length) { throw 'Extracted file length mismatch.' }
        }
    } finally { $taskZip.Dispose() }
}
$env:PATH = "$taskRoot\runtime;$taskRoot\runtime\Library\bin;$taskRoot\runtime\DLLs;$env:PATH"
$env:PYTHONHOME = $null; $env:PYTHONPATH = $null
$env:PYTHONNOUSERSITE = '1'; $env:PYTHONDONTWRITEBYTECODE = '1'; $env:PYTHONIOENCODING = 'utf-8'
$env:HF_HUB_OFFLINE = '1'; $env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:TEXT2REVIT_CHECKPOINT = Join-Path $taskRoot 'models\flow_matching_best.pth'
$env:TEXT2REVIT_CLIP_DIR = Join-Path $taskRoot 'models\clip'
$taskPython = Join-Path $taskRoot 'runtime\python.exe'
Push-Location -LiteralPath $taskRoot
try {
    Write-Host 'Initializing Python paths...'
    & $taskPython -B (Join-Path $taskRoot 'runtime\Scripts\conda-unpack-script.py')
    if ($LASTEXITCODE -ne 0) { throw 'Python path initialization failed.' }
    Write-Host 'Checking the inference runtime and model files...'
    & $taskPython -B (Join-Path $taskRoot 'healthcheck.py')
    if ($LASTEXITCODE -ne 0) { throw 'Inference health check failed.' }
} finally { Pop-Location }
@{fingerprint=$taskFingerprint;root=$taskRoot;version=$taskManifest.version} | ConvertTo-Json | Set-Content -LiteralPath $taskMarker -Encoding UTF8
Write-Host 'Ready. The browser editor will now open. Later launches reuse the prepared runtime.'
