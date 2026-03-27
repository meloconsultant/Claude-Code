# Claude Code Installer for Windows
# Usage: irm https://claude.ai/install.ps1 | iex

[CmdletBinding()]
param(
    [string]$Version = "latest"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Step   { param([string]$Msg) Write-Host "  » $Msg" -ForegroundColor Cyan }
function Write-Ok     { param([string]$Msg) Write-Host "  ✔ $Msg" -ForegroundColor Green }
function Write-Warn   { param([string]$Msg) Write-Host "  ! $Msg"  -ForegroundColor Yellow }
function Write-Fail   { param([string]$Msg) Write-Host "  ✘ $Msg" -ForegroundColor Red }

function Exit-WithError {
    param([string]$Msg)
    Write-Fail $Msg
    Write-Host ""
    exit 1
}

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Test-MinimumVersion {
    param([string]$VersionString, [int]$MinMajor)
    try {
        $major = [int]($VersionString -replace '^v', '' -split '\.')[0]
        return $major -ge $MinMajor
    } catch {
        return $false
    }
}

# ── Banner ───────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Claude Code Installer" -ForegroundColor White
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── Node.js prerequisite ─────────────────────────────────────────────────────

Write-Step "Checking for Node.js..."

$nodePath = Get-CommandPath "node"

if ($nodePath) {
    $nodeVersion = (& node --version 2>&1).ToString().Trim()
    if (Test-MinimumVersion $nodeVersion 18) {
        Write-Ok "Node.js $nodeVersion is already installed."
    } else {
        Write-Warn "Node.js $nodeVersion is installed but version 18 or higher is required."
        Write-Step "Attempting to upgrade Node.js..."
        $nodePath = $null   # fall through to installer
    }
}

if (-not $nodePath) {
    Write-Step "Node.js not found — installing via winget..."

    $winget = Get-CommandPath "winget"
    if ($winget) {
        try {
            & winget install --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
            if ($LASTEXITCODE -ne 0) { throw "winget exited with code $LASTEXITCODE" }

            # Refresh PATH so the new node is available in this session
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("PATH", "User")

            $nodeVersion = (& node --version 2>&1).ToString().Trim()
            Write-Ok "Node.js $nodeVersion installed successfully."
        } catch {
            Exit-WithError "Failed to install Node.js via winget: $_`n  Please install Node.js 18+ manually from https://nodejs.org and re-run this script."
        }
    } else {
        # winget not available — guide the user instead of a silent download
        Write-Host ""
        Write-Fail "winget is not available on this system."
        Write-Host "  Please install Node.js 18 or higher from https://nodejs.org" -ForegroundColor Yellow
        Write-Host "  then re-run this installer:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "      irm https://claude.ai/install.ps1 | iex" -ForegroundColor White
        Write-Host ""
        exit 1
    }
}

# ── npm availability ──────────────────────────────────────────────────────────

Write-Step "Checking for npm..."

$npmPath = Get-CommandPath "npm"
if (-not $npmPath) {
    Exit-WithError "npm was not found even after Node.js installation.`n  Please reinstall Node.js from https://nodejs.org"
}

$npmVersion = (& npm --version 2>&1).ToString().Trim()
Write-Ok "npm $npmVersion found."

# ── Install Claude Code ───────────────────────────────────────────────────────

$packageName = "@anthropic-ai/claude-code"
$installArg  = if ($Version -eq "latest") { $packageName } else { "${packageName}@${Version}" }

Write-Step "Installing $installArg globally..."

try {
    & npm install -g $installArg 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ne 0) { throw "npm exited with code $LASTEXITCODE" }
} catch {
    Exit-WithError "Installation failed: $_`n  Try running the command manually: npm install -g $installArg"
}

# ── Verify ────────────────────────────────────────────────────────────────────

Write-Step "Verifying installation..."

$claudePath = Get-CommandPath "claude"
if (-not $claudePath) {
    # npm global executables live at the prefix directory on Windows
    $npmGlobalBin = (& npm config get prefix 2>&1).ToString().Trim()
    if ($npmGlobalBin -and (Test-Path $npmGlobalBin)) {
        $env:PATH = "$npmGlobalBin;$env:PATH"
        $claudePath = Get-CommandPath "claude"
    }
}

if ($claudePath) {
    try {
        $claudeVersion = (& claude --version 2>&1).ToString().Trim()
        Write-Ok "Claude Code $claudeVersion installed at $claudePath"
    } catch {
        Write-Ok "Claude Code installed at $claudePath"
    }
} else {
    Write-Warn "claude command not found on PATH."
    Write-Host ""
    Write-Host "  npm global binaries may not be in your PATH." -ForegroundColor Yellow
    Write-Host "  Run the following to find the directory and add it:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "      npm config get prefix" -ForegroundColor White
    Write-Host ""
    Write-Host "  Then add that path to your PATH environment variable." -ForegroundColor Yellow
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  Get started:  claude" -ForegroundColor White
Write-Host "  Docs:         https://docs.anthropic.com/claude-code" -ForegroundColor DarkGray
Write-Host ""
