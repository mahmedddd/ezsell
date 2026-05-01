# Google OAuth Quick Setup Guide

## Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one:
   - Click "Select a project" → "New Project"
   - Name: `EZSell` (or any name)
   - Click "Create"

3. Enable Google+ API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. Create OAuth Credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure consent screen first:
     - User Type: "External"
     - App name: `EZSell`
     - User support email: Your email
     - Developer contact: Your email
     - Click "Save and Continue"
     - Scopes: Click "Save and Continue" (default is fine)
     - Test users: Add your email
     - Click "Save and Continue"

5. Create OAuth Client ID:
   - Application type: "Web application"
   - Name: `EZSell Web Client`
   - Authorized redirect URIs: Add these two URLs:
     - `http://localhost:8000/api/v1/auth/google/callback`
     - `http://127.0.0.1:8000/api/v1/auth/google/callback`
   - Click "Create"

6. Copy credentials:
   - You'll see a popup with your Client ID and Client Secret
   - Copy both values

## Step 2: Update Backend .env File

Open `backend/.env` and update these lines:

```env
GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret-here
```

## Step 3: Test the Flow

1. **Start Backend** (if not running):
   ```powershell
   cd C:\Users\rajaa\OneDrive\Desktop\ezsell\ezsell\backend
   .\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend** (if not running):
   ```powershell
   cd C:\Users\rajaa\OneDrive\Desktop\ezsell\ezsell\frontend
   npm run dev
   ```

3. **Test Google Login**:
   - Go to http://localhost:8080/login
   - Click "Continue with Google" button
   - Select your Google account
   - Grant permissions
   - You'll be redirected back and logged in automatically

## How It Works

### User Registration from Google:
✅ **Name**: Stored in `full_name` field from Google profile
✅ **Email**: Stored in `email` field from Google account
✅ **Avatar**: Profile picture URL stored in `avatar_url`
✅ **Username**: Auto-generated from email (e.g., `john` from john@gmail.com)
✅ **Verified**: Automatically marked as verified
✅ **Auth Provider**: Set to "google"

### Duplicate Prevention:
✅ **By Google ID**: Checks if user with same google_id exists (prevents duplicate Google logins)
✅ **By Email**: If email exists but no google_id, links Google account to existing user
✅ **Unique Username**: If username exists, adds number suffix (john1, john2, etc.)

### Database Storage:
```
User Table:
- id: Auto-generated
- username: From email prefix (e.g., "john")
- email: From Google (e.g., "john@gmail.com")
- full_name: From Google (e.g., "John Doe")
- avatar_url: Google profile picture URL
- google_id: Google's unique user ID (prevents duplicates)
- auth_provider: "google"
- is_verified: True
- hashed_password: NULL (no password needed)
- last_login: Updated on each login
```

## Frontend Features Added

✅ **Login Page**: "Continue with Google" button
✅ **Signup Page**: "Continue with Google" button  
✅ **Callback Page**: Handles OAuth redirect and token storage
✅ **Auto-redirect**: After successful login, redirects to dashboard

## Security Features

1. **No Duplicate Users**: 
   - Checks google_id first
   - Checks email second
   - Links accounts if email matches

2. **Email Verification**: 
   - Google users are pre-verified
   - No email OTP needed for Google signups

3. **Token Security**: 
   - JWT tokens issued same as email/password users
   - Same authorization flow

## Troubleshooting

**Error: "redirect_uri_mismatch"**
- Make sure you added the exact URL to Google Console
- URL must be: `http://localhost:8000/api/v1/auth/google/callback`

**Error: "Access blocked: This app's request is invalid"**
- Complete OAuth consent screen configuration
- Add your email as a test user

**User not redirected after login**
- Check browser console for errors
- Verify frontend is running on port 8080

**Duplicate users created**
- This should not happen with the current implementation
- System checks google_id and email before creating

## Testing Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 8080
- [ ] Google credentials in .env file
- [ ] Can see "Continue with Google" button
- [ ] Button redirects to Google login
- [ ] After login, redirected to dashboard
- [ ] Check database - user has email, full_name, google_id
- [ ] Try logging in again - no duplicate user created
- [ ] Try with different Google account
