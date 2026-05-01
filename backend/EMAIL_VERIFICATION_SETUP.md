# Email Verification Setup Guide

## Email Verification Flow

When users sign up, they must verify their email address before registration is completed:

1. **User enters email** on signup form
2. **Backend sends 6-digit code** to their email
3. **User receives email** with verification code
4. **User enters code** in verification field
5. **Backend verifies code** (checks validity and expiration)
6. **If valid** → Allow registration to proceed
7. **If invalid/expired** → Show error, allow resending

## Setup Gmail SMTP (Recommended)

### Step 1: Enable 2-Step Verification

1. Go to your Google Account: https://myaccount.google.com/
2. Click "Security" in the left sidebar
3. Under "Signing in to Google", click "2-Step Verification"
4. Follow the steps to enable it

### Step 2: Create App Password

1. Go to: https://myaccount.google.com/apppasswords
2. In "Select app", choose "Mail"
3. In "Select device", choose "Other (Custom name)"
4. Enter: "EZSell Backend"
5. Click "Generate"
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 3: Update .env File

Open `backend/.env` and update:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # Your 16-character app password (no spaces)
SMTP_FROM_EMAIL=your-email@gmail.com
```

## API Endpoints

### 1. Send Verification Code

```
POST /api/v1/send-verification-code
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Verification code sent to email",
  "email": "user@example.com"
}
```

**Errors:**
- `400` - Email already registered
- `500` - Failed to send email

### 2. Verify Code

```
POST /api/v1/verify-code
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com"
}
```

**Errors:**
- `400` - Invalid verification code
- `400` - Verification code expired

### 3. Register (After Verification)

```
POST /api/v1/register
```

Same as before, but only works after email is verified.

## Database Schema

### email_verifications Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| email | String(255) | User's email address |
| code | String(6) | 6-digit verification code |
| expires_at | DateTime | Expiration time (10 minutes from creation) |
| is_used | Boolean | Whether code has been used |
| created_at | DateTime | When code was created |

## Frontend Implementation

### Signup Flow

```tsx
// Step 1: Send verification code
const sendCode = async (email: string) => {
  const response = await axios.post('/send-verification-code', { email });
  // Show: "Code sent to your email!"
  // Show verification code input field
};

// Step 2: Verify code
const verifyCode = async (email: string, code: string) => {
  const response = await axios.post('/verify-code', { email, code });
  // Code verified! Now allow registration form
};

// Step 3: Register user
const register = async (userData) => {
  const response = await axios.post('/register', userData);
  // User registered successfully!
};
```

### Updated Signup Component

```tsx
const [step, setStep] = useState(1); // 1: Email, 2: Code, 3: Registration
const [email, setEmail] = useState("");
const [code, setCode] = useState("");

// Step 1: Email input
<Input 
  type="email" 
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  placeholder="Enter your email"
/>
<Button onClick={() => sendVerificationCode(email)}>
  Send Code
</Button>

// Step 2: Code verification
<Input 
  value={code}
  onChange={(e) => setCode(e.target.value)}
  placeholder="Enter 6-digit code"
  maxLength={6}
/>
<Button onClick={() => verifyCode(email, code)}>
  Verify
</Button>

// Step 3: Show full registration form
```

## Email Template

The verification email includes:
- ✅ Beautiful HTML design with EZSell branding
- ✅ Large, easy-to-read 6-digit code
- ✅ Expiration warning (10 minutes)
- ✅ Plain text fallback for email clients

## Security Features

- ✅ Codes expire in 10 minutes
- ✅ Codes can only be used once
- ✅ Email must not already be registered
- ✅ Code validation before registration
- ✅ Secure SMTP with TLS

## Testing

1. Update `.env` with your Gmail credentials
2. Restart backend server
3. Visit: http://localhost:8000/docs
4. Try endpoint: `POST /send-verification-code`
5. Check your email for the code
6. Use code in: `POST /verify-code`

## Troubleshooting

### "Failed to send verification email"
- Check SMTP credentials in `.env`
- Ensure Gmail App Password is correct (no spaces)
- Verify 2-Step Verification is enabled
- Check internet connection

### "Verification code expired"
- Codes expire after 10 minutes
- User must request a new code

### "Invalid verification code"
- Check for typos in the code
- Ensure code hasn't been used already
- Request a new code if needed

## Production Notes

For production:
- Consider using SendGrid, AWS SES, or Mailgun for better deliverability
- Add rate limiting to prevent spam
- Log email sending attempts
- Add "Resend Code" functionality
- Consider SMS verification as alternative

---

Your signup process is now secure with email verification! 🔒📧
