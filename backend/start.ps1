# Quick Start Script for EZSell

Write-Host "🚀 Starting EZSell Application..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Check if packages are installed
$installed = & .\venv\Scripts\pip.exe list
if ($installed -notmatch "fastapi") {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    & .\venv\Scripts\pip.exe install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Check .env filei 
if (-Not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your configuration" -ForegroundColor Yellow
    exit 1
}

# Check Google OAuth credentials
$envContent = Get-Content .env -Raw
if ($envContent -match "GOOGLE_CLIENT_ID=your-google-client-id") {
    Write-Host "⚠️  Warning: Google OAuth credentials not configured" -ForegroundColor Yellow
    Write-Host "   Google login will not work until you add credentials to .env" -ForegroundColor Yellow
    Write-Host "   See GOOGLE_OAUTH_COMPLETE_SETUP.md for instructions" -ForegroundColor Yellow
    Write-Host ""
}

if ($envContent -match "SMTP_USERNAME=your-email@gmail.com") {
    Write-Host "⚠️  Warning: Email verification not configured" -ForegroundColor Yellow
    Write-Host "   Email verification will not work until you add Gmail credentials to .env" -ForegroundColor Yellow
    Write-Host "   See EMAIL_VERIFICATION_SETUP.md for instructions" -ForegroundColor Yellow
    Write-Host ""
}

# Start the server
Write-Host "🎯 Starting FastAPI server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

& .\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
