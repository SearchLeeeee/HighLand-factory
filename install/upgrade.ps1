# HighLand-factory upgrade (Windows / PowerShell 7+)
#
# Run this after pulling a newer factory checkout. It refreshes the local engine,
# re-syncs the generic skills/packs into the agent skill roots, and optionally
# refreshes initialized work repos.
#
# Usage:
#   pwsh -File install/upgrade.ps1                 # sync current checkout
#   pwsh -File install/upgrade.ps1 -Pull           # git pull --ff-only, then sync
#   pwsh -File install/upgrade.ps1 -Work D:\my-project  # no-leakage: ignore
#   pwsh -File install/upgrade.ps1 -Work D:\a,D:\b -ApplyWorkUpgrade  # no-leakage: ignore
#   pwsh -File install/upgrade.ps1 -NoSkills       # engine only (agent-config managed)
#   pwsh -File install/upgrade.ps1 -SkillsRoot D:\custom\skills -WithPacks  # no-leakage: ignore

[CmdletBinding()]
param(
    [switch]$Pull,
    [string[]]$Work = @(),
    [switch]$ApplyWorkUpgrade,
    [switch]$NoSkills,
    [string]$SkillsRoot = "",
    [switch]$Force,
    [switch]$WithPacks
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$InstallScript = Join-Path $PSScriptRoot "install.ps1"
$FactoryCmd = Join-Path $RepoRoot "bin\factory.cmd"

function Write-Step([string]$Message) { Write-Host "[upgrade] $Message" }
function Write-Warn([string]$Message) { Write-Host "[upgrade] WARN: $Message" -ForegroundColor Yellow }

Write-Step "Factory repo: $RepoRoot"

if ($Pull) {
    Write-Step "git pull --ff-only"
    git -C $RepoRoot pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        throw "git pull failed. Resolve local changes first, or run upgrade without -Pull."
    }
}

$versionFile = Join-Path $RepoRoot "VERSION"
if (Test-Path $versionFile) { Write-Step ("Version: {0}" -f (Get-Content $versionFile -Raw).Trim()) }

# Reuse the installer for venv, shims and skill/pack linking. It is idempotent and
# removes links that point into this checkout but whose source skill was deleted.
$installArgs = @{}
if ($NoSkills) { $installArgs["NoSkills"] = $true }
if ($SkillsRoot) { $installArgs["SkillsRoot"] = $SkillsRoot }
if ($Force) { $installArgs["Force"] = $true }
if ($WithPacks) { $installArgs["WithPacks"] = $true }

& $InstallScript @installArgs
if ($LASTEXITCODE -ne 0) { throw "install.ps1 failed" }

if ($Work.Count -eq 0) {
    Write-Step "No -Work paths given. Agent links and engine are refreshed; work repos were not touched."
    Write-Step "Refresh a work repo with: install/upgrade.ps1 -Work <path> [-ApplyWorkUpgrade]"
    return
}

foreach ($workPath in $Work) {
    if (-not (Test-Path $workPath)) {
        Write-Warn "work repo not found: $workPath"
        continue
    }
    $resolved = (Resolve-Path $workPath).Path
    $configFile = Join-Path $resolved ".factory\factory.yaml"
    if (-not (Test-Path $configFile)) {
        Write-Warn "$resolved is not an initialized work repo (missing .factory/factory.yaml); skipped"
        continue
    }
    Write-Step "Refreshing work repo: $resolved"
    # Refresh machine-scoped local.yaml without touching agent links again.
    & $InstallScript -Work $resolved -NoSkills
    if ($LASTEXITCODE -ne 0) { throw "install.ps1 -Work failed for $resolved" }

    Write-Step "Checking generated files: $resolved"
    & $FactoryCmd upgrade --work $resolved --check
    $checkExit = $LASTEXITCODE
    if ($ApplyWorkUpgrade) {
        if ($checkExit -ne 0) {
            Write-Step "Applying generated-file refresh: $resolved"
            & $FactoryCmd upgrade --work $resolved --apply
            if ($LASTEXITCODE -ne 0) { throw "factory upgrade --apply failed for $resolved" }
        } else {
            Write-Step "Already up to date: $resolved"
        }
        & $FactoryCmd doctor --work $resolved
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "doctor reported issues for $resolved; fix them before starting work"
        }
    } elseif ($checkExit -ne 0) {
        Write-Warn "generated files need refresh in $resolved; rerun with -ApplyWorkUpgrade"
    }
}

Write-Step "Done."
Write-Step "Next: restart your agent session so it reloads the refreshed skills."
