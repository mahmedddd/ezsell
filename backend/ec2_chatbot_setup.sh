#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  EzSell — Chatbot Feature Deployment Script (EC2 / Ubuntu)
#  Run this on your EC2 instance after the dev machine pushes to GitHub
# ═══════════════════════════════════════════════════════════════════

set -e  # Exit immediately on any error

PROJECT_DIR="/home/ubuntu/ezsell"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV="$PROJECT_DIR/.venv"
WEB_ROOT="/var/www/html"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   EzSell Chatbot Feature — EC2 Deploy   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Step 1: Pull latest code ────────────────────────────────────────
echo "📦 [1/7] Pulling latest code from GitHub..."
cd "$PROJECT_DIR"
git pull origin main
echo "✅ Code updated."

# ── Step 2: Add GROQ_CHATBOT_API_KEY to backend .env ───────────────
# NOTE: Replace YOUR_KEY_HERE with your actual Groq chatbot API key.
#       Do NOT commit your real key to GitHub — set it here manually.
echo ""
echo "🔑 [2/7] Injecting GROQ_CHATBOT_API_KEY into backend .env..."
if grep -q "GROQ_CHATBOT_API_KEY" "$BACKEND_DIR/.env" 2>/dev/null; then
    echo "   Key already present in .env — skipping."
else
    echo "GROQ_CHATBOT_API_KEY=YOUR_KEY_HERE" >> "$BACKEND_DIR/.env"
    echo "   ⚠️  Remember to replace YOUR_KEY_HERE in $BACKEND_DIR/.env with your real key!"
fi

# ── Step 3: Upgrade groq Python package ────────────────────────────
echo ""
echo "🐍 [3/7] Upgrading groq package (needs >=0.11.0 for AsyncGroq)..."
source "$VENV/bin/activate"
pip install "groq>=0.11.0" --quiet
echo "✅ groq package upgraded."

# ── Step 4: Build the frontend ─────────────────────────────────────
echo ""
echo "⚛️  [4/7] Building React frontend..."
cd "$PROJECT_DIR"
npm run build
echo "✅ Frontend build complete."

# ── Step 5: Deploy frontend to web root ────────────────────────────
echo ""
echo "🚀 [5/7] Deploying frontend to $WEB_ROOT..."
sudo cp -r "$PROJECT_DIR/dist/"* "$WEB_ROOT/"
echo "✅ Frontend files deployed."

# ── Step 6: Restart Nginx ──────────────────────────────────────────
echo ""
echo "🌐 [6/7] Restarting Nginx..."
sudo nginx -t && sudo systemctl restart nginx
echo "✅ Nginx restarted."

# ── Step 7: Restart backend ────────────────────────────────────────
echo ""
echo "⚙️  [7/7] Restarting EzSell backend..."
sudo systemctl restart ezsell.service
sleep 2
sudo systemctl status ezsell.service --no-pager | head -10
echo "✅ Backend restarted."

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        🎉 Deployment Complete!           ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Chatbot endpoint: /api/v1/chatbot/chat  ║"
echo "║  Suggestions:      /api/v1/chatbot/suggestions  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "⚠️  Don't forget: edit $BACKEND_DIR/.env"
echo "    and replace YOUR_KEY_HERE with your real GROQ_CHATBOT_API_KEY"
echo "    then run: sudo systemctl restart ezsell.service"
