#!/bin/bash
# EZSell Project Verification Script
# Run this to verify everything is set up correctly

echo ""
echo "================================================"
echo "   EZSell Project Verification Script"
echo "================================================"
echo ""

ERRORS=0

# Check Python
echo "[1/8] Checking Python..."
if command -v python3 &> /dev/null; then
    python3 --version
    echo "[PASS] Python found"
else
    echo "[FAIL] Python not found"
    ((ERRORS++))
fi
echo ""

# Check Node.js
echo "[2/8] Checking Node.js..."
if command -v node &> /dev/null; then
    node --version
    echo "[PASS] Node.js found"
else
    echo "[FAIL] Node.js not found"
    ((ERRORS++))
fi
echo ""

# Check npm
echo "[3/8] Checking npm..."
if command -v npm &> /dev/null; then
    npm --version
    echo "[PASS] npm found"
else
    echo "[FAIL] npm not found"
    ((ERRORS++))
fi
echo ""

# Check Git
echo "[4/8] Checking Git..."
if command -v git &> /dev/null; then
    git --version
    echo "[PASS] Git found"
else
    echo "[FAIL] Git not found"
    ((ERRORS++))
fi
echo ""

# Check backend directory
echo "[5/8] Checking backend directory..."
if [ -f "ezsell/ezsell/backend/main.py" ]; then
    echo "[PASS] Backend directory exists"
else
    echo "[FAIL] Backend directory not found"
    ((ERRORS++))
fi
echo ""

# Check frontend directory
echo "[6/8] Checking frontend directory..."
if [ -f "ezsell/ezsell/frontend/package.json" ]; then
    echo "[PASS] Frontend directory exists"
else
    echo "[FAIL] Frontend directory not found"
    ((ERRORS++))
fi
echo ""

# Check documentation
echo "[7/8] Checking documentation..."
if [ -f "README.md" ] && [ -f "QUICKSTART.md" ] && [ -f "SETUP_GUIDE.md" ]; then
    echo "[PASS] All documentation files exist"
else
    echo "[FAIL] Some documentation files missing"
    ((ERRORS++))
fi
echo ""

# Check setup scripts
echo "[8/8] Checking setup scripts..."
if [ -f "setup.bat" ] && [ -f "setup.sh" ]; then
    echo "[PASS] Setup scripts exist"
else
    echo "[FAIL] Some setup scripts missing"
    ((ERRORS++))
fi
echo ""

# Summary
echo "================================================"
echo "   Verification Summary"
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo "[SUCCESS] All checks passed! ✓"
    echo ""
    echo "Your project is ready to use!"
    echo ""
    echo "Next steps:"
    echo "1. Run ./setup.sh to install dependencies"
    echo "2. Start backend: cd ezsell/ezsell/backend && python -m uvicorn main:app --reload"
    echo "3. Start frontend: cd ezsell/ezsell/frontend && npm run dev"
    echo "4. Open http://localhost:8080"
else
    echo "[FAILED] $ERRORS check(s) failed! ✗"
    echo ""
    echo "Please fix the errors above before proceeding."
    echo "See SETUP_GUIDE.md for detailed instructions."
fi
echo "================================================"
echo ""
