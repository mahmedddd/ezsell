# EZSell - Comprehensive Testing Guide

**Date:** December 21, 2025  
**Backend:** http://localhost:8000  
**Frontend:** http://localhost:8081  
**API Docs:** http://localhost:8000/docs

---

## 🎯 Quick Test Overview

### System Status
- ✅ Backend Running (FastAPI on port 8000)
- ✅ Frontend Running (Vite on port 8081)
- ✅ Database (SQLite - ezsell.db)
- ✅ Email Service (Gmail SMTP configured)
- ✅ OpenCV (v4.10.0.84 installed)
- ✅ All Dependencies Installed

---

## 📋 Feature Testing Checklist

## 1️⃣ USER AUTHENTICATION & REGISTRATION

### Test: User Registration with Email Verification
**Steps:**
1. Open http://localhost:8081/signup
2. Enter email address
3. Click "Send Verification Code"
4. Check email inbox for 6-digit code (expires in 2 minutes)
5. Enter verification code
6. Complete registration form:
   - Username (check availability indicator)
   - Password
   - Full Name
7. Submit registration

**Expected Results:**
- ✅ Verification email received
- ✅ Code validation works
- ✅ Username availability checked in real-time
- ✅ Auto-login after successful registration
- ✅ Redirect to dashboard

**API Endpoints:**
- `POST /api/v1/send-verification-code`
- `POST /api/v1/verify-code`
- `POST /api/v1/register`

---

### Test: User Login
**Steps:**
1. Open http://localhost:8081/login
2. Enter username and password
3. Click "Login"

**Expected Results:**
- ✅ Successful login with valid credentials
- ✅ Clear error message if user doesn't exist
- ✅ Clear error message for wrong password
- ✅ JWT token stored in localStorage
- ✅ Redirect to dashboard

**Error Messages to Test:**
- Invalid username: "User not found. Please check your username or sign up for a new account."
- Wrong password: "Incorrect username or password. Please try again."
- Network issue: "Unable to connect to server. Please check your internet connection."

**API Endpoint:**
- `POST /api/v1/login`

---

### Test: Google OAuth Login
**Steps:**
1. Click "Continue with Google" button
2. Authorize with Google account
3. Get redirected back to application

**Expected Results:**
- ✅ OAuth flow completes
- ✅ User account created/linked
- ✅ Auto-login successful

**API Endpoints:**
- `GET /api/v1/auth/google/login`
- `GET /api/v1/auth/google/callback`

---

## 2️⃣ LISTINGS MANAGEMENT

### Test: Create New Listing
**Steps:**
1. Login to dashboard
2. Click "Create Listing" or "Add Product"
3. Fill in listing details:
   - Title
   - Description
   - Category (Mobile, Laptop, Furniture)
   - Price
   - Condition (New, Like New, Good, Fair, Poor)
   - Location
   - Upload images (optional)
4. Submit listing

**Expected Results:**
- ✅ Listing created successfully
- ✅ Images uploaded and saved
- ✅ Listing appears in "My Listings"
- ✅ Status shows as "pending" (awaiting approval)

**API Endpoint:**
- `POST /api/v1/listings/`

---

### Test: View All Listings
**Steps:**
1. Navigate to marketplace/home page
2. Browse all available listings
3. Use filters:
   - Category filter
   - Price range
   - Condition filter
   - Search by keyword

**Expected Results:**
- ✅ All approved listings displayed
- ✅ Filters work correctly
- ✅ Search functionality works
- ✅ Pagination works (if implemented)

**API Endpoint:**
- `GET /api/v1/listings/`

---

### Test: View Listing Details
**Steps:**
1. Click on any listing
2. View detailed information
3. Check all details displayed correctly

**Expected Results:**
- ✅ All listing information shown
- ✅ Images displayed properly
- ✅ Seller information visible
- ✅ Contact/message button available
- ✅ Favorite button works

**API Endpoint:**
- `GET /api/v1/listings/{id}`

---

### Test: Update Listing
**Steps:**
1. Go to "My Listings"
2. Click "Edit" on your listing
3. Modify details
4. Save changes

**Expected Results:**
- ✅ Changes saved successfully
- ✅ Updated information displayed
- ✅ Images can be added/removed

**API Endpoint:**
- `PUT /api/v1/listings/{id}`

---

### Test: Delete Listing
**Steps:**
1. Go to "My Listings"
2. Click "Delete" on your listing
3. Confirm deletion

**Expected Results:**
- ✅ Listing removed from database
- ✅ Confirmation message shown
- ✅ No longer appears in listings

**API Endpoint:**
- `DELETE /api/v1/listings/{id}`

---

## 3️⃣ PRICE PREDICTION (ML FEATURE)

### Test: Predict Mobile Phone Price
**Steps:**
1. Navigate to price prediction page
2. Select category: "Mobile"
3. Enter details:
   - Brand (e.g., Apple, Samsung, Xiaomi)
   - Model name
   - RAM (GB)
   - Storage (GB)
   - Screen size (inches)
   - Battery capacity (mAh)
   - Camera (MP)
   - Processor
   - Age (years)
   - Condition
4. Click "Predict Price"

**Expected Results:**
- ✅ ML model returns predicted price
- ✅ Price range shown
- ✅ Confidence score displayed
- ✅ Similar listings shown (if available)

**API Endpoint:**
- `POST /api/v1/predict/mobile`

---

### Test: Predict Laptop Price
**Steps:**
1. Select category: "Laptop"
2. Enter details:
   - Brand (e.g., Dell, HP, Lenovo, Apple)
   - Model
   - Processor (Intel i3/i5/i7/i9, AMD Ryzen)
   - RAM (GB)
   - Storage (GB)
   - Storage Type (HDD/SSD)
   - Screen size (inches)
   - Graphics card
   - Age (years)
   - Condition
3. Click "Predict Price"

**Expected Results:**
- ✅ Accurate price prediction
- ✅ Prediction explanation shown

**API Endpoint:**
- `POST /api/v1/predict/laptop`

---

### Test: Predict Furniture Price
**Steps:**
1. Select category: "Furniture"
2. Enter details:
   - Type (Sofa, Table, Chair, Bed, etc.)
   - Material (Wood, Metal, Fabric)
   - Dimensions (L x W x H)
   - Age (years)
   - Condition
   - Brand (if applicable)
3. Click "Predict Price"

**Expected Results:**
- ✅ Price prediction returned
- ✅ Market comparison shown

**API Endpoint:**
- `POST /api/v1/predict/furniture`

---

## 4️⃣ AR FURNITURE CUSTOMIZATION

### Test: Generate AR Preview
**Steps:**
1. Navigate to AR customization page
2. Select furniture item from dropdown:
   - Modern Sofa
   - Dining Table
   - Office Chair
   - Bookshelf
   - Coffee Table
   - Bed Frame
3. Upload room image (photo of your room)
4. Click "Generate AR Preview"
5. View AR-overlayed image

**Expected Results:**
- ✅ Image uploaded successfully
- ✅ OpenCV processes image
- ✅ Furniture overlay applied
- ✅ Preview image displayed
- ✅ Semi-transparent furniture area shown
- ✅ Border and label added
- ✅ Image saved to `/static/ar_previews/`

**API Endpoints:**
- `POST /api/v1/ar-preview`
- `GET /api/v1/furniture-items`

**Test with API:**
```bash
# Using curl (PowerShell)
$headers = @{"Content-Type"="multipart/form-data"}
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ar-preview" `
  -Method POST `
  -Form @{
    furniture_item="Modern Sofa"
    room_image=Get-Item "C:\path\to\room.jpg"
  }
```

---

## 5️⃣ MESSAGING SYSTEM

### Test: Send Message to Seller
**Steps:**
1. View a listing
2. Click "Contact Seller" or "Send Message"
3. Type your message
4. Click "Send"

**Expected Results:**
- ✅ Message sent successfully
- ✅ Notification shown
- ✅ Message appears in conversation

**API Endpoint:**
- `POST /api/v1/messages/`

---

### Test: View Conversations
**Steps:**
1. Go to "Messages" section
2. View all conversations
3. Click on a conversation
4. Read messages

**Expected Results:**
- ✅ All conversations listed
- ✅ Unread count displayed
- ✅ Messages ordered by time
- ✅ Real-time updates (if implemented)

**API Endpoints:**
- `GET /api/v1/messages/conversations`
- `GET /api/v1/messages/conversation/{userId}/{listingId}`

---

### Test: Mark Messages as Read
**Steps:**
1. Open unread message
2. Message automatically marked as read

**Expected Results:**
- ✅ Unread count decreases
- ✅ Message status updated

**API Endpoint:**
- `PATCH /api/v1/messages/{id}/read`

---

## 6️⃣ FAVORITES SYSTEM

### Test: Add to Favorites
**Steps:**
1. View any listing
2. Click "Favorite" or heart icon
3. Check favorites page

**Expected Results:**
- ✅ Listing added to favorites
- ✅ Heart icon fills/changes color
- ✅ Appears in favorites list

**API Endpoint:**
- `POST /api/v1/favorites/{listing_id}`

---

### Test: Remove from Favorites
**Steps:**
1. Go to favorites page
2. Click "Remove" or heart icon again
3. Confirm removal

**Expected Results:**
- ✅ Listing removed from favorites
- ✅ No longer appears in favorites list

**API Endpoint:**
- `DELETE /api/v1/favorites/{listing_id}`

---

### Test: View All Favorites
**Steps:**
1. Navigate to "Favorites" page
2. View all saved listings

**Expected Results:**
- ✅ All favorited listings shown
- ✅ Quick access to listings
- ✅ Can remove from favorites

**API Endpoint:**
- `GET /api/v1/favorites`

---

## 7️⃣ RECOMMENDATION SYSTEM (AI-Powered)

### Test: Track User Activity
**Steps:**
1. Browse different listings
2. View specific products
3. Search for items
4. System automatically tracks activity

**Expected Results:**
- ✅ Activities logged in database
- ✅ Keywords extracted using NLP
- ✅ User interests updated
- ✅ Categories tracked

**API Endpoint:**
- `POST /api/recommendations/track-activity`

**Test Data:**
```json
{
  "action": "view",
  "listing_id": 1,
  "search_query": "iPhone 15 Pro",
  "category": "mobile"
}
```

---

### Test: Get Personalized Recommendations
**Steps:**
1. After browsing several items
2. Navigate to "For You" or recommendations section
3. View personalized recommendations

**Expected Results:**
- ✅ Recommendations based on browsing history
- ✅ Items match user interests
- ✅ Categories aligned with preferences
- ✅ Keyword-based matching works

**API Endpoint:**
- `GET /api/recommendations/personalized?limit=10`

**Algorithm:**
- 40% weight on category matching
- 40% weight on keyword similarity
- 10% weight on price range
- 10% weight on brand matching

---

### Test: Get Trending Listings
**Steps:**
1. Navigate to trending section
2. View most popular items

**Expected Results:**
- ✅ Listings with most views shown
- ✅ Sorted by popularity
- ✅ Category filter works

**API Endpoint:**
- `GET /api/recommendations/trending?category=mobile&limit=10`

---

### Test: Get Similar Listings
**Steps:**
1. View a listing
2. Check "Similar Items" section

**Expected Results:**
- ✅ Similar products shown
- ✅ Based on category and keywords
- ✅ Price range considered

**API Endpoint:**
- `POST /api/recommendations/similar`

```json
{
  "listing_id": 1,
  "limit": 5
}
```

---

### Test: Get "For You" Recommendations
**Steps:**
1. Go to dashboard/home
2. View "For You" section

**Expected Results:**
- ✅ Mixed recommendations
- ✅ Trending + Personalized
- ✅ Dynamic based on user behavior

**API Endpoint:**
- `GET /api/recommendations/for-you?limit=10`

---

## 8️⃣ ANALYTICS DASHBOARD

### Test: View User Dashboard
**Steps:**
1. Navigate to analytics/insights page
2. View personal statistics

**Expected Results:**
- ✅ Total views count
- ✅ Search history
- ✅ Favorite categories shown
- ✅ Top keywords displayed
- ✅ Activity timeline visible
- ✅ Engagement score calculated

**API Endpoint:**
- `GET /api/analytics/dashboard`

**Dashboard Includes:**
```json
{
  "total_views": 45,
  "total_searches": 12,
  "favorite_categories": ["mobile", "laptop"],
  "top_keywords": ["iPhone", "MacBook", "Samsung"],
  "recent_activities": [...],
  "engagement_score": 8.5,
  "recommendations_clicked": 5
}
```

---

### Test: View Activity History
**Steps:**
1. Navigate to activity page
2. View all past activities

**Expected Results:**
- ✅ All activities listed chronologically
- ✅ Shows views, searches, favorites
- ✅ Timestamp for each activity
- ✅ Keywords extracted shown

**API Endpoint:**
- `GET /api/analytics/activities?limit=50`

---

### Test: View Interest Profile
**Steps:**
1. Go to interests/preferences page
2. View aggregated interests

**Expected Results:**
- ✅ Categories with counts
- ✅ Keywords with frequencies
- ✅ Brands with counts
- ✅ Price ranges preference
- ✅ Last updated timestamp

**API Endpoint:**
- `GET /api/analytics/interests`

---

### Test: View Search Insights
**Steps:**
1. Navigate to search insights
2. View search patterns

**Expected Results:**
- ✅ Popular search terms
- ✅ Search frequency
- ✅ Categories searched
- ✅ Search success rate

**API Endpoint:**
- `GET /api/analytics/search-insights`

---

### Test: View Recommendation Performance
**Steps:**
1. Go to recommendation metrics
2. View how well recommendations perform

**Expected Results:**
- ✅ Click-through rate
- ✅ Successful recommendations count
- ✅ User engagement metrics

**API Endpoint:**
- `GET /api/analytics/recommendation-performance`

---

## 9️⃣ ADMIN FEATURES (Approval System)

### Test: View Pending Approvals (Admin Only)
**Steps:**
1. Login as admin user
2. Navigate to "Approvals" section
3. View all pending listings

**Expected Results:**
- ✅ All pending listings shown
- ✅ Listing details visible
- ✅ Approve/Reject buttons available

**API Endpoint:**
- `GET /api/v1/approvals/pending`

---

### Test: Approve Listing (Admin Only)
**Steps:**
1. View pending listing
2. Click "Approve"
3. Confirm approval

**Expected Results:**
- ✅ Listing status changed to "approved"
- ✅ Listing now visible to all users
- ✅ Notification sent to seller (optional)

**API Endpoint:**
- `POST /api/v1/approvals/{listing_id}/approve`

---

### Test: Reject Listing (Admin Only)
**Steps:**
1. View pending listing
2. Click "Reject"
3. Enter rejection reason
4. Confirm rejection

**Expected Results:**
- ✅ Listing status changed to "rejected"
- ✅ Reason saved in database
- ✅ Notification sent to seller

**API Endpoint:**
- `POST /api/v1/approvals/{listing_id}/reject`

```json
{
  "reason": "Inappropriate content"
}
```

---

## 🔟 PASSWORD MANAGEMENT

### Test: Forgot Password
**Steps:**
1. Click "Forgot Password" on login page
2. Enter email address
3. Check email for reset code
4. Enter reset code
5. Set new password
6. Login with new password

**Expected Results:**
- ✅ Reset code sent to email (expires in 1 minute)
- ✅ Code validation works
- ✅ Password updated successfully
- ✅ Can login with new password

**API Endpoints:**
- `POST /api/v1/forgot-password`
- `POST /api/v1/verify-reset-code`
- `POST /api/v1/reset-password`

---

## 1️⃣1️⃣ NLP KEYWORD EXTRACTION

### Test: Keyword Extraction from Text
**Background Process - Auto-runs when:**
- User searches for items
- Listing is created
- User views listings

**Test Cases:**
```
Input: "iPhone 15 Pro Max 256GB"
Expected Keywords: ["iphone", "15", "pro", "max", "256gb"]
Expected Brand: "Apple"
Expected Category: "mobile"

Input: "MacBook Pro M3 16GB RAM"
Expected Keywords: ["macbook", "pro", "m3", "16gb", "ram"]
Expected Brand: "Apple"
Expected Category: "laptop"

Input: "Samsung Galaxy S24 Ultra"
Expected Keywords: ["samsung", "galaxy", "s24", "ultra"]
Expected Brand: "Samsung"
Expected Category: "mobile"

Input: "Modern wooden dining table 6 seater"
Expected Keywords: ["modern", "wooden", "dining", "table", "6", "seater"]
Expected Category: "furniture"
```

**Verification:**
- Check database `user_activities` table for extracted keywords
- Check `user_interests` table for aggregated keywords

---

## 🧪 API TESTING WITH SWAGGER

### Access Interactive API Documentation
**URL:** http://localhost:8000/docs

**Steps:**
1. Open browser to http://localhost:8000/docs
2. View all available endpoints
3. Expand any endpoint
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"
7. View response

**All Endpoint Categories:**
- 👤 Users
- 🔐 Google OAuth
- 📦 Listings
- 💰 Predictions
- 🏠 AR Customization
- 💬 Messages
- ⭐ Favorites
- ✅ Approvals
- 🎯 Recommendations
- 📊 Analytics

---

## 🔧 TESTING TIPS

### 1. Database Inspection
```powershell
# View database contents
cd C:\Users\ahmed\Downloads\ezsell\ezsell\ezsell\backend
python -c "from models.database import *; from sqlalchemy import create_engine; engine = create_engine('sqlite:///./ezsell.db'); print('Tables:', engine.table_names())"
```

### 2. Check Logs
- **Backend logs:** Check the terminal running uvicorn
- **Frontend logs:** Check browser console (F12)
- **Email logs:** Check terminal for email sending status

### 3. Reset Database (If Needed)
```powershell
cd backend
python create_tables.py  # Recreates all tables
```

### 4. Test Email Service
```powershell
cd backend
python -c "import asyncio; from core.email_service import email_service; asyncio.run(email_service.send_verification_email('your@email.com', '123456'))"
```

### 5. Test NLP Service
```powershell
cd backend
python test_nlp_standalone.py
```

### 6. Test Recommendation Engine
```powershell
cd backend
python test_database_engine.py
```

---

## 📊 EXPECTED PERFORMANCE

### Response Times (Target)
- User authentication: < 500ms
- Listing retrieval: < 200ms
- Price prediction: < 1s
- AR preview generation: < 3s
- Recommendations: < 300ms
- Analytics dashboard: < 500ms

### Success Criteria
- ✅ All endpoints return proper status codes
- ✅ Error messages are clear and helpful
- ✅ No server crashes during testing
- ✅ Database operations complete successfully
- ✅ Email delivery works consistently
- ✅ ML predictions are reasonable
- ✅ AR previews generate correctly
- ✅ Recommendations are relevant

---

## 🐛 KNOWN ISSUES & LIMITATIONS

### Current Limitations:
1. **AR Customization:** Simple overlay (not real 3D rendering)
2. **Real-time Chat:** Polling-based (not WebSocket)
3. **Image Storage:** Local filesystem (not cloud)
4. **ML Models:** Trained on sample data (limited accuracy)
5. **Email:** Rate-limited by Gmail SMTP

### Python 3.14 Compatibility:
- ⚠️ NumPy 2.x compilation issues (using 1.26.4)
- ✅ OpenCV working with headless version
- ✅ All other packages compatible

---

## 📞 SUPPORT & TROUBLESHOOTING

### If Backend Doesn't Start:
```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### If Frontend Doesn't Start:
```powershell
cd frontend
npm install  # or: bun install
npm run dev  # or: bun run dev
```

### If Database Issues Occur:
```powershell
cd backend
python create_tables.py
```

### Clear Browser Cache:
- Press Ctrl+Shift+Delete
- Clear cache and cookies
- Restart browser

---

## ✅ FINAL CHECKLIST

**Before Declaring Testing Complete:**

- [ ] User can register with email verification
- [ ] User can login successfully
- [ ] Google OAuth works
- [ ] Listings can be created, viewed, updated, deleted
- [ ] Price predictions work for all categories
- [ ] AR preview generates correctly
- [ ] Messages can be sent and received
- [ ] Favorites work properly
- [ ] Recommendations are relevant
- [ ] Analytics dashboard displays correctly
- [ ] Admin approval system works
- [ ] Password reset works
- [ ] All API endpoints respond correctly
- [ ] No console errors in frontend
- [ ] No server errors in backend
- [ ] Email notifications sent successfully

---

## 🎉 SUCCESS METRICS

**Your EZSell application is fully functional when:**

✅ All 11 major features tested successfully  
✅ All 60+ test cases passed  
✅ Both servers running stable  
✅ No critical errors in logs  
✅ User experience is smooth  
✅ Data persists correctly in database  
✅ Email notifications working  
✅ ML predictions reasonable  
✅ Recommendations relevant  
✅ API documentation accessible  

---

## 📝 NOTES

**Testing Date:** December 21, 2025  
**System:** Windows with PowerShell  
**Python Version:** 3.14  
**Node Version:** (Check with `node --version`)  
**Database:** SQLite (ezsell.db)  

**Happy Testing! 🚀**
