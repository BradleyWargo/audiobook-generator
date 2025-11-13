# GitHub Setup Guide

This guide shows you how to push the audiobook-generator project to GitHub safely, without exposing personal information.

## What's Protected? ✅

Your `.gitignore` file ensures these will **NEVER** be committed:
- ✅ `credentials/*.json` - Your Google Cloud service account key
- ✅ `src/config_local.py` - Your personal project ID and bucket name
- ✅ `input/*.epub` and `input/*.docx` - Your ebook files
- ✅ `output/*.wav` - Generated audio files
- ✅ `logs/*.log` - Processing logs
- ✅ `.DS_Store` - Mac system files

## What Will Be Committed? 📦

Only public, shareable code:
- ✅ Source code with placeholder values
- ✅ Documentation (README, QUICKSTART, etc.)
- ✅ `config.example.json` with example values
- ✅ `requirements.txt`
- ✅ `.gitignore` itself
- ✅ Empty directory markers (`.gitkeep`)

## Prerequisites

### 1. GitHub Account (if you don't have one)

Go to [github.com](https://github.com) and:
1. Click "Sign up"
2. Follow the registration process
3. Verify your email

### 2. Git Installation (check if installed)

In Terminal:
```bash
git --version
```

If not installed, download from [git-scm.com](https://git-scm.com) or install via Homebrew:
```bash
brew install git
```

### 3. Configure Git (first time only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step-by-Step: Push to GitHub

### Option A: Create Repository on GitHub First (Recommended for Beginners)

#### 1. Create Repository on GitHub.com

1. Go to [github.com](https://github.com)
2. Click the **"+"** icon (top right) → **"New repository"**
3. Fill in:
   - **Repository name:** `audiobook-generator`
   - **Description:** "Convert ebooks to audiobooks using Google Cloud TTS"
   - **Visibility:** Choose Public or Private
   - **Do NOT** check "Initialize with README" (we already have one)
4. Click **"Create repository"**

#### 2. Push Your Project from Terminal

Open Terminal in VSCode and run these commands:

```bash
# Navigate to your project
cd "/Users/bradley/Documents/Python Projects/active/audiobook-generator"

# Initialize git (if not already done)
git init

# Add all files (gitignore will exclude sensitive ones)
git add .

# Check what will be committed (verify no secrets!)
git status

# Review the files to be committed
git diff --cached --name-only

# Create your first commit
git commit -m "Initial commit: Audiobook generator project"

# Add GitHub as remote (REPLACE with your actual GitHub URL)
git remote add origin https://github.com/YOUR-USERNAME/audiobook-generator.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### 3. Enter GitHub Credentials

When prompted:
- **Username:** Your GitHub username
- **Password:** Use a **Personal Access Token** (not your password!)

**To get a Personal Access Token:**
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: "audiobook-generator"
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)
7. Use this token as your password in Terminal

---

### Option B: Create Repository from Terminal (Advanced)

If you have [GitHub CLI](https://cli.github.com/) installed:

```bash
cd "/Users/bradley/Documents/Python Projects/active/audiobook-generator"
git init
git add .
git commit -m "Initial commit: Audiobook generator project"
gh repo create audiobook-generator --public --source=. --remote=origin --push
```

---

## Verify Nothing Secret Was Committed

### Before Pushing, Check Files

```bash
# See what files will be committed
git status

# List all tracked files
git ls-files

# Make sure none of these appear:
# - credentials/*.json (except .gitkeep)
# - src/config_local.py
# - input/*.epub or input/*.docx
# - output/*.wav
# - logs/*.log
```

### After Pushing, View on GitHub

1. Go to your repository on GitHub.com
2. Click through the files
3. Verify:
   - ✅ `credentials/` folder exists but only contains `.gitkeep`
   - ✅ `src/audiobook_generator.py` shows placeholder values like `"your-project-id"`
   - ✅ `config.example.json` shows placeholder values
   - ✅ No service account JSON visible

## Future Updates

After making changes to your code:

```bash
# Check what changed
git status

# Add specific files or all changes
git add .

# Commit with a message
git commit -m "Add feature: chapter selection"

# Push to GitHub
git push
```

## Common Issues

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR-USERNAME/audiobook-generator.git
```

### "rejected - non-fast-forward"
```bash
git pull origin main --rebase
git push
```

### "Authentication failed"
- Make sure you're using a Personal Access Token, not your password
- Check the token has `repo` permissions
- Try regenerating the token

### Accidentally committed a secret?
**If you committed but didn't push yet:**
```bash
# Undo the last commit but keep changes
git reset --soft HEAD~1

# Remove the sensitive file
git rm --cached path/to/secret-file

# Re-commit
git commit -m "Initial commit"
```

**If you already pushed:**
1. Delete the repository on GitHub
2. Create a new one
3. Be more careful this time!
4. Or use `git filter-branch` (advanced, Google it)

## Double-Check Security

Run this command to see what's being tracked:

```bash
cd "/Users/bradley/Documents/Python Projects/active/audiobook-generator"
git ls-files | grep -E "credentials/.*\.json|config_local\.py|\.epub|\.docx|\.wav|\.log"
```

**This should return NOTHING.** If it shows files, they're being tracked and need to be removed:

```bash
git rm --cached path/to/sensitive/file
git commit -m "Remove sensitive file"
```

## Your Project is Now Public (or Private)!

Repository URL: `https://github.com/YOUR-USERNAME/audiobook-generator`

Share it with others, and they can:
1. Clone your repo
2. Add their own credentials
3. Create their own `config_local.py`
4. Start generating audiobooks!

---

**Ready to push?** Just follow the steps above. Your personal data is safe! 🔒
