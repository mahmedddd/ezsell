@echo off
REM EZSell Project Verification Script
REM Run this to verify everything is set up correctly

echo.
echo ================================================
echo    EZSell Project Verification Script
echo ================================================
echo.

set ERRORS=0

REM Check Python
echo [1/8] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    set /a ERRORS+=1
) else (
    python --version
    echo [PASS] Python found
)
echo.

REM Check Node.js
echo [2/8] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Node.js not found
    set /a ERRORS+=1
) else (
    node --version
    echo [PASS] Node.js found
)
echo.

REM Check npm
echo [3/8] Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] npm not found
    set /a ERRORS+=1
) else (
    npm --version
    echo [PASS] npm found
)
echo.

REM Check Git
echo [4/8] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Git not found
    set /a ERRORS+=1
) else (
    git --version
    echo [PASS] Git found
)
echo.

REM Check backend directory
echo [5/8] Checking backend directory...
if exist "ezsell\ezsell\backend\main.py" (
    echo [PASS] Backend directory exists
) else (
    echo [FAIL] Backend directory not found
    set /a ERRORS+=1
)
echo.

REM Check frontend directory
echo [6/8] Checking frontend directory...
if exist "ezsell\ezsell\frontend\package.json" (
    echo [PASS] Frontend directory exists
) else (
    echo [FAIL] Frontend directory not found
    set /a ERRORS+=1
)
echo.

REM Check documentation
echo [7/8] Checking documentation...
if exist "README.md" (
    if exist "QUICKSTART.md" (
        if exist "SETUP_GUIDE.md" (
            echo [PASS] All documentation files exist
        ) else (
            echo [FAIL] SETUP_GUIDE.md missing
            set /a ERRORS+=1
        )
    ) else (
        echo [FAIL] QUICKSTART.md missing
        set /a ERRORS+=1
    )
) else (
    echo [FAIL] README.md missing
    set /a ERRORS+=1
)
echo.

REM Check setup scripts
echo [8/8] Checking setup scripts...
if exist "setup.bat" (
    if exist "setup.sh" (
        echo [PASS] Setup scripts exist
    ) else (
        echo [FAIL] setup.sh missing
        set /a ERRORS+=1
    )
) else (
    echo [FAIL] setup.bat missing
    set /a ERRORS+=1
)
echo.

REM Summary
echo ================================================
echo    Verification Summary
echo ================================================
if %ERRORS% EQU 0 (
    echo [SUCCESS] All checks passed! ✓
    echo.
    echo Your project is ready to use!
    echo.
    echo Next steps:
    echo 1. Run setup.bat to install dependencies
    echo 2. Start backend: ezsell\ezsell\backend\start_backend.bat
    echo 3. Start frontend: ezsell\ezsell\frontend\start_frontend.bat
    echo 4. Open http://localhost:8080
) else (
    echo [FAILED] %ERRORS% check(s) failed! ✗
    echo.
    echo Please fix the errors above before proceeding.
    echo See SETUP_GUIDE.md for detailed instructions.
)
echo ================================================
echo.

pause
