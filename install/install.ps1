# HighLand-factory installer (Windows / PowerShell 7+)
#
# What it does:
#   1. Creates a local Python venv under <repo>/.venv with PyYAML (or reuses one).
#   2. Writes <repo>/bin/factory.cmd and <repo>/bin/factory (POSIX shim).
#   3. Links the generic skills into the user-level skill roots of detected agents.
#   4. Optionally refreshes <work>/.factory/local.yaml with this machine's paths.
#
# Usage:
#   pwsh -File install/install.ps1
#   pwsh -File install/install.ps1 -Work D:\my-project  # no-leakage: ignore
#   pwsh -File install/install.ps1 -Force          # replace existing skill links

[CmdletBinding()]
param(
    [switch]$Force,
    [string]$Work = "",
    [string]$Python = "",
    [switch]$NoSkills,
    [string]$SkillsRoot = "",
    [switch]$WithPacks
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvDir = Join-Path $RepoRoot ".venv"
$BinDir = Join-Path $RepoRoot "bin"

function Write-Step([string]$Message) { Write-Host "[install] $Message" }
function Write-Warn([string]$Message) { Write-Host "[install] WARN: $Message" -ForegroundColor Yellow }

function Find-Python {
    if ($Python) {
        if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
        return $Python
    }
    foreach ($candidate in @("python", "python3", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                $version = & $candidate -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2>$null
                if ($version -match "^3\s+(\d+)") { return $candidate }
            } catch { }
        }
    }
    throw "No Python 3 interpreter found. Install Python 3.10+ or pass -Python <path>."
}

function Ensure-Venv {
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Step "Reusing venv: $VenvDir"
        return $venvPython
    }
    $base = Find-Python
    Write-Step "Creating venv with $base"
    & $base -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "python -m venv failed" }
    return $venvPython
}

function Ensure-PyYaml([string]$VenvPython) {
    & $VenvPython -c "import yaml" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Step "PyYAML already available"
        return
    }
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        Write-Step "Installing PyYAML with uv"
        & uv pip install --python $VenvPython --quiet pyyaml
    } else {
        Write-Step "Installing PyYAML with pip"
        & $VenvPython -m pip install --quiet --disable-pip-version-check pyyaml
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to install PyYAML" }
    & $VenvPython -c "import yaml; print('PyYAML', yaml.__version__)"
}

function Write-Shims([string]$VenvPython) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    $engine = Join-Path $RepoRoot "engine\factory.py"
    $cmd = @"
@echo off
"$VenvPython" "$engine" %*
"@
    Set-Content -Path (Join-Path $BinDir "factory.cmd") -Value $cmd -Encoding ASCII
    $sh = @"
#!/usr/bin/env sh
exec "$VenvPython" "$engine" "`$@"
"@
    Set-Content -Path (Join-Path $BinDir "factory") -Value $sh -Encoding UTF8 -NoNewline
    Write-Step "Wrote shims under $BinDir"
}

function Get-SkillRoots {
    $roots = [System.Collections.Generic.List[object]]::new()
    $home_ = $HOME
    $candidates = @(
        @{ Agent = "dsh"; Path = Join-Path $home_ ".dsh\skills" },
        @{ Agent = "claude"; Path = Join-Path $home_ ".claude\skills" },
        @{ Agent = "codex"; Path = Join-Path $home_ ".codex\skills" }
    )
    foreach ($candidate in $candidates) {
        $parent = Split-Path -Parent $candidate.Path
        if (Test-Path $parent) {
            $roots.Add([pscustomobject]@{ Agent = $candidate.Agent; Path = $candidate.Path })
        }
    }
    return $roots
}

function Link-Skills([string]$SkillsRoot, [string]$Destination, [string]$Label) {
    if (-not (Test-Path $SkillsRoot)) {
        Write-Warn "${Label}: source not found: $SkillsRoot"
        return
    }
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $sourceNames = @(Get-ChildItem $SkillsRoot -Directory | ForEach-Object { $_.Name })
    $sourcePrefix = (Resolve-Path $SkillsRoot).Path
    $linked = 0
    foreach ($skill in Get-ChildItem $SkillsRoot -Directory) {
        $dest = Join-Path $Destination $skill.Name
        if (Test-Path $dest) {
            $item = Get-Item $dest -Force
            $isLink = ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
            if ($isLink) {
                Remove-Item $dest -Force -Recurse
            } elseif ($Force) {
                Remove-Item $dest -Force -Recurse
            } else {
                Write-Warn "${Label}: $dest exists and is not a link; skipped (use -Force to replace)"
                continue
            }
        }
        New-Item -ItemType Junction -Path $dest -Target $skill.FullName | Out-Null
        $linked++
    }
    # Remove links this installer created earlier for skills that no longer exist.
    foreach ($existing in Get-ChildItem $Destination -Force -ErrorAction SilentlyContinue) {
        $isLink = ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
        if (-not $isLink) { continue }
        $target = $existing.Target
        if ($target -is [array]) { $target = $target[0] }
        $targetText = [string]$target
        if (-not $targetText.StartsWith($sourcePrefix, [StringComparison]::OrdinalIgnoreCase)) { continue }
        if ($sourceNames -notcontains $existing.Name) {
            Remove-Item $existing.FullName -Force -Recurse
            Write-Step "${Label}: removed stale link $($existing.Name)"
        }
    }
    Write-Step "${Label}: linked $linked skill(s) into $Destination"
}

function Refresh-WorkLocal([string]$WorkPath, [string]$VenvPython) {
    $factoryYaml = Join-Path $WorkPath ".factory\factory.yaml"
    if (-not (Test-Path $factoryYaml)) {
        Write-Warn "-Work $WorkPath is not initialized yet; run: factory init --work `"$WorkPath`""
        return
    }
    $localPath = Join-Path $WorkPath ".factory\local.yaml"
    $content = @"
# Machine-scoped factory values. Gitignored; safe to contain absolute paths.
factory_root: "$($RepoRoot -replace '\\', '/')"
python: "$($VenvPython -replace '\\', '/')"
node: null
ports: {}
env: {}
platform: windows
"@
    Set-Content -Path $localPath -Value $content -Encoding UTF8
    Write-Step "Refreshed $localPath"
}

Write-Step "Factory repo: $RepoRoot"
$venvPython = Ensure-Venv
Ensure-PyYaml $venvPython
Write-Shims $venvPython

$canonicalSkills = Join-Path $RepoRoot "skills"
$canonicalPacks = Join-Path $RepoRoot "packs"
if ($NoSkills) {
    Write-Step "Skipping skill linking (-NoSkills)"
} else {
    if ($SkillsRoot) {
        Link-Skills $canonicalSkills $SkillsRoot "custom"
        if ($WithPacks) { Link-Skills $canonicalPacks $SkillsRoot "custom-packs" }
    } else {
        foreach ($root in Get-SkillRoots) {
            Link-Skills $canonicalSkills $root.Path $root.Agent
            if ($WithPacks) { Link-Skills $canonicalPacks $root.Path "$($root.Agent)-packs" }
        }
    }
}

if ($Work) { Refresh-WorkLocal $Work $venvPython }

Write-Host ""
Write-Step "Done. Add this directory to PATH to call 'factory' anywhere:"
Write-Host "  $BinDir"
Write-Host ""
Write-Step "Or call it directly:"
Write-Host "  $BinDir\factory.cmd --version"
Write-Host ""
Write-Step "Initialize a work repo:"
Write-Host "  $BinDir\factory.cmd init --work D:\my-project"  # no-leakage: ignore
Write-Host "  $BinDir\factory.cmd doctor --work D:\my-project"  # no-leakage: ignore
