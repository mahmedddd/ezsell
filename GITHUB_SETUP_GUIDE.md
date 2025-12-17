# GitHub Setup and Collaboration Guide

## Prerequisites

### 1. Install Git
Since Git is not currently installed, you need to install it first:

1. **Download Git for Windows:**
   - Visit: https://git-scm.com/download/win
   - Download the installer
   - Run the installer and follow the setup wizard (use default settings)

2. **Verify Installation:**
   After installation, open a new PowerShell window and run:
   ```powershell
   git --version
   ```

### 2. Configure Git
Set up your Git identity:
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Push to GitHub

### Step 1: Initialize Git Repository
```powershell
cd C:\Users\ahmed\Downloads\ezsell
git init
```

### Step 2: Add All Files
```powershell
git add .
```

### Step 3: Create Initial Commit
```powershell
git commit -m "Initial commit: EzSell marketplace platform"
```

### Step 4: Create GitHub Repository
1. Go to https://github.com
2. Log in to your account (create one if needed)
3. Click the "+" icon in the top right
4. Select "New repository"
5. Fill in:
   - **Repository name:** `ezsell` (or your preferred name)
   - **Description:** "AI-powered marketplace with AR preview and price prediction"
   - **Visibility:** Private (recommended) or Public
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### Step 5: Connect to GitHub
After creating the repository, GitHub will show you commands. Use these:

```powershell
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ezsell.git

# Rename the default branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Set Up Collaborators

### Option 1: Add Direct Collaborators (Recommended for Small Teams)

1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Collaborators" in the left sidebar
4. Click "Add people"
5. Enter their GitHub username or email
6. Select the appropriate permission level:
   - **Read:** Can view and clone
   - **Write:** Can push changes (recommended for collaborators)
   - **Admin:** Full control including settings

### Option 2: Use GitHub Organizations (For Larger Teams)

1. Create a GitHub Organization
2. Add team members
3. Transfer the repository to the organization
4. Manage team permissions through the organization settings

## Collaborator Workflow

### For Collaborators:

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/YOUR_USERNAME/ezsell.git
   cd ezsell
   ```

2. **Before making changes:**
   ```powershell
   git pull origin main
   ```

3. **Make changes, then commit:**
   ```powershell
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

### Best Practices:

1. **Use Branches for Features:**
   ```powershell
   # Create a new branch
   git checkout -b feature/new-feature
   
   # Make changes and commit
   git add .
   git commit -m "Add new feature"
   
   # Push the branch
   git push origin feature/new-feature
   ```

2. **Create Pull Requests:**
   - Go to GitHub repository
   - Click "Pull requests" → "New pull request"
   - Select your branch
   - Add description and request review
   - Merge after approval

3. **Keep Your Local Repository Updated:**
   ```powershell
   git fetch origin
   git pull origin main
   ```

## Branch Protection Rules (Optional but Recommended)

1. Go to repository Settings → Branches
2. Add branch protection rule for `main`
3. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass
   - Require conversation resolution before merging

## Common Git Commands

```powershell
# Check status
git status

# View commit history
git log --oneline

# Create a branch
git checkout -b branch-name

# Switch branches
git checkout branch-name

# Delete a branch
git branch -d branch-name

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- filename

# Update from remote
git pull

# View remotes
git remote -v
```

## Troubleshooting

### Authentication Issues
If you're asked for credentials repeatedly, set up SSH keys or use a Personal Access Token:

**Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` permissions
3. Use this token as your password when pushing

**SSH Keys (Recommended):**
```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Copy the public key
cat ~/.ssh/id_ed25519.pub
```
Then add the key to GitHub: Settings → SSH and GPG keys → New SSH key

Change remote URL to SSH:
```powershell
git remote set-url origin git@github.com:YOUR_USERNAME/ezsell.git
```

## Next Steps

1. Install Git
2. Configure Git with your credentials
3. Initialize the repository
4. Create GitHub repository
5. Push your code
6. Invite collaborators
7. Start collaborating!

## Important Notes

- The `.gitignore` file has been created to exclude sensitive files, dependencies, and build artifacts
- Consider using environment variables for sensitive data (API keys, database credentials)
- Large files (>100MB) require Git LFS (Large File Storage)
- Review the committed files before pushing to ensure no sensitive data is included
