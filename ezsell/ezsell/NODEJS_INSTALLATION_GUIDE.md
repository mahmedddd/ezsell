# Node.js Installation Guide for EZSell

## Step 1: Uninstall Current Node.js

1. **Press `Win + X`** on your keyboard
2. Select **"Apps and Features"** (or "Add or remove programs")
3. In the search box, type **"Node.js"**
4. Click on **Node.js** in the list
5. Click **"Uninstall"**
6. Follow the prompts to complete uninstallation
7. **Restart your computer** (important!)

## Step 2: Download Node.js LTS

1. Open your browser and go to: **https://nodejs.org/**
2. Download the **LTS (Long Term Support)** version
   - Look for the green button that says "LTS Recommended For Most Users"
   - Current LTS version is **v20.x** or **v22.x**
3. Save the `.msi` installer file

## Step 3: Install Node.js with Correct PATH

1. **Run the downloaded `.msi` installer** (double-click it)
2. Click **"Next"** on the welcome screen
3. **Accept the license agreement**
4. Choose installation location (default is fine: `C:\Program Files\nodejs`)
5. **IMPORTANT**: On the "Custom Setup" screen:
   - Make sure **"Add to PATH"** is checked ✓
   - Make sure **"npm package manager"** is checked ✓
6. Click **"Next"**
7. On the "Tools for Native Modules" screen:
   - You can check this if you want, but it's optional
8. Click **"Install"**
9. Wait for installation to complete
10. Click **"Finish"**

## Step 4: Verify Installation

1. **Close ALL PowerShell windows** (important!)
2. **Open a NEW PowerShell window**
3. Run these commands to verify:

```powershell
node --version
npm --version
```

You should see version numbers like:
```
v20.x.x
10.x.x
```

## Step 5: Start the Frontend

Once Node.js is properly installed:

```powershell
# Navigate to frontend directory
cd C:\Users\rajaa\OneDrive\Desktop\ezsell\ezsell\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on **http://localhost:8080**

## Troubleshooting

### If `node` command is not recognized after installation:

1. **Restart your computer** (this refreshes the PATH)
2. Open a **new** PowerShell window
3. Try `node --version` again

### If still not working:

Manually add to PATH:
1. Press `Win + X` → Select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", find "Path"
5. Click "Edit"
6. Click "New"
7. Add: `C:\Program Files\nodejs`
8. Click "OK" on all dialogs
9. **Restart your computer**

---

## Quick Reference

**Node.js Download**: https://nodejs.org/
**Choose**: LTS version (green button)
**Make sure**: "Add to PATH" is checked during installation
**After install**: Restart computer and open new PowerShell

---

## What's Next?

Once Node.js is installed and verified:

1. ✅ Backend is already running on http://localhost:8000
2. ⬜ Install frontend dependencies: `npm install`
3. ⬜ Start frontend: `npm run dev`
4. ⬜ Access app at http://localhost:8080
5. ⬜ Test complete flow: Signup → Login → Create Listing → Browse

**Let me know once Node.js is installed and I'll help you start the frontend!** 🚀
