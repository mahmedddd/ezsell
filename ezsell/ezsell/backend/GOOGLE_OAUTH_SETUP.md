# Google OAuth Setup Guide

## Step 1: Create Google OAuth Credentials

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project (or select existing):**
   - Click "Select a project" → "New Project"
   - Name: "EZSell" → Create

3. **Enable Google+ API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Create OAuth Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "EZSell Web Client"
   
5. **Configure OAuth Consent Screen (if not done):**
   - Go to "OAuth consent screen"
   - User Type: External → Create
   - App name: "EZSell"
   - User support email: your email
   - Developer contact: your email
   - Save and Continue

6. **Add Authorized Redirect URIs:**
   ```
   http://localhost:8000/api/v1/auth/google/callback
   ```
   
7. **Save and Copy Credentials:**
   - You'll get:
     - **Client ID**: `xxxxxxx.apps.googleusercontent.com`
     - **Client Secret**: `GOCSPX-xxxxxxxxxx`

## Step 2: Update Backend .env File

Open `backend/.env` and update:

```env
GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-actual-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

## Step 3: Google Login Flow

### Backend Endpoints Created:

1. **`GET /api/v1/auth/google/login`**
   - Redirects user to Google login page
   
2. **`GET /api/v1/auth/google/callback`**
   - Handles Google OAuth response
   - Creates or updates user in database
   - Returns JWT access token

### Frontend Implementation:

Add a "Login with Google" button:

```tsx
// In Login.tsx
const handleGoogleLogin = () => {
  window.location.href = 'http://localhost:8000/api/v1/auth/google/login';
};

<Button onClick={handleGoogleLogin} variant="outline" className="w-full">
  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
    {/* Google Icon SVG */}
  </svg>
  Continue with Google
</Button>
```

## How It Works:

### New User (First Time Google Login):
1. User clicks "Login with Google"
2. Redirects to Google → User signs in with Google account
3. Google returns user data (email, name, profile picture, Google ID)
4. Backend checks if Google ID exists in database → **Not found**
5. Backend checks if email exists → **Not found**
6. Backend creates new user:
   - `username`: from email (e.g., john from john@gmail.com)
   - `email`: from Google
   - `full_name`: from Google
   - `avatar_url`: from Google profile picture
   - `google_id`: unique Google user ID
   - `auth_provider`: "google"
   - `is_verified`: true (Google accounts are pre-verified)
   - `hashed_password`: null (no password needed)
7. Saves to Supabase database
8. Returns JWT token
9. User is logged in!

### Existing User (Returning Google Login):
1. User clicks "Login with Google"
2. Google returns user data
3. Backend finds user by `google_id` in database
4. Updates `last_login` timestamp
5. Returns JWT token
6. User is logged in!

### Linking Google to Existing Account:
If user already registered with email/password, then tries Google login:
- Backend finds user by email
- Links Google ID to that user account
- User can now login with both methods!

## Database Schema:

Users table now includes:
- `google_id` - Unique Google user ID (nullable, indexed)
- `auth_provider` - "local" or "google"
- `hashed_password` - Nullable (null for Google OAuth users)

## Security:

✅ Google OAuth is secure - passwords are managed by Google
✅ JWT tokens for session management
✅ User data stored in Supabase
✅ Email verification not needed (Google accounts are trusted)

## Testing:

1. Start backend: `python -m uvicorn main:app --reload`
2. Visit: http://localhost:8000/docs
3. Try: `GET /api/v1/auth/google/login`
4. Should redirect to Google login

Once credentials are added, Google login will work! 🚀
