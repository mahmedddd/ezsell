# Troubleshooting Guide - Create Listing Network Error

## Issue: "Network Error" When Creating Listings

If you're seeing a network error when trying to create a listing, follow these steps to diagnose and fix the issue.

## Step 1: Check Backend Server

### Verify Backend is Running
Open a new terminal and run:
```bash
# Windows:
netstat -ano | findstr :8000

# Linux/macOS:
lsof -i :8000
```

**Expected output**: You should see a process listening on port 8000.

If nothing appears, the backend is NOT running. Start it:
```bash
cd ezsell/ezsell/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Test Backend Health
```bash
# Windows PowerShell:
Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET

# Linux/macOS/Windows (curl):
curl http://localhost:8000/
```

**Expected output**: `{"message":"Welcome to the EZSell API"}`

## Step 2: Check Browser Console

1. Open your browser (Chrome/Firefox)
2. Press `F12` to open Developer Tools
3. Go to the `Console` tab
4. Try to create a listing
5. Look for error messages in red

### Common Console Errors:

#### Error: "Network request failed" or "ERR_CONNECTION_REFUSED"
**Cause**: Backend server is not running.
**Solution**: Start the backend server (see Step 1).

#### Error: "401 Unauthorized"
**Cause**: You're not logged in or your session expired.
**Solution**: 
1. Logout
2. Login again
3. Try creating the listing again

#### Error: "422 Validation Error"
**Cause**: Missing or invalid form data.
**Solution**: Check the console for specific field errors and ensure all required fields are filled correctly.

#### Error: "timeout of 30000ms exceeded"
**Cause**: Backend is slow or hanging.
**Solution**:
1. Check backend console for errors
2. Restart backend server
3. Check database connection

## Step 3: Check Network Tab

1. Open Developer Tools (`F12`)
2. Go to `Network` tab
3. Try to create a listing
4. Look for the POST request to `/api/v1/listings`

### Request is RED:
- Click on it
- Check the `Response` tab
- Look for error details

### Request is YELLOW (pending):
- Backend is not responding
- Check if backend server is running

### Request shows CORS error:
- Check backend CORS configuration
- Ensure `http://localhost:8080` is in allowed origins

## Step 4: Verify Form Data

Before submitting, ensure:

### Required Fields:
- ✅ Title (minimum 5 characters)
- ✅ Description (minimum 10 characters)
- ✅ Location (not empty)
- ✅ Image uploaded
- ✅ Price (greater than 0)
- ✅ Category selected

### Category-Specific Fields:
**Mobile/Laptop:**
- ✅ Brand selected from dropdown

**Furniture:**
- ✅ Furniture type selected
- ✅ Material selected

### Title Validation:
- Title must include brand AND model information
- ❌ Bad: "Mobile for sale"
- ❌ Bad: "Samsung mobile"
- ✅ Good: "Samsung Galaxy S23 Ultra"

## Step 5: Clear Browser Cache

Sometimes cached data causes issues:

1. Open Developer Tools (`F12`)
2. Right-click the refresh button
3. Click "Empty Cache and Hard Reload"
4. Try again

Or:

1. Go to browser settings
2. Clear browsing data
3. Select "Cached images and files"
4. Clear data
5. Refresh the page

## Step 6: Check Authentication

### Verify Token Exists:
1. Open Developer Tools (`F12`)
2. Go to `Application` tab (Chrome) or `Storage` tab (Firefox)
3. Expand `Local Storage`
4. Click on `http://localhost:8080`
5. Check if `authToken` exists

**If missing:**
1. Logout
2. Login again

**If exists:**
- Copy the token value
- Check if it's a valid JWT (should have 3 parts separated by dots)

## Step 7: Test with Postman/cURL

### Using cURL (Advanced):

1. First, login and get token:
```bash
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"youruser","password":"yourpass"}'
```

2. Copy the `access_token` from response

3. Create listing:
```bash
curl -X POST http://localhost:8000/api/v1/listings \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "title=Samsung Galaxy S23" \
  -F "description=Good condition phone" \
  -F "category=mobile" \
  -F "price=50000" \
  -F "condition=used" \
  -F "location=Lahore" \
  -F "brand=Samsung" \
  -F "images=@/path/to/image.jpg"
```

If this works, the backend is fine and the issue is in the frontend.

## Step 8: Check Backend Logs

Look at the backend terminal for errors:

### Common Backend Errors:

#### "404 Not Found"
- API endpoint changed
- Check frontend is calling correct URL

#### "500 Internal Server Error"
- Backend code error
- Check backend console for Python traceback
- May need to fix backend code

#### "Database error"
- Database file missing or corrupted
- Run: `python create_tables.py`

## Step 9: Restart Everything

Sometimes a fresh start helps:

1. **Stop Backend**: `Ctrl+C` in backend terminal
2. **Stop Frontend**: `Ctrl+C` in frontend terminal  
3. **Kill all processes**:
   ```bash
   # Windows:
   taskkill /F /IM python.exe
   taskkill /F /IM node.exe
   
   # Linux/macOS:
   pkill python
   pkill node
   ```
4. **Wait 5 seconds**
5. **Start Backend**: `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
6. **Start Frontend**: `npm run dev`
7. **Try again**

## Step 10: Enable Detailed Logging

The latest version includes detailed console logging. Check the browser console for messages like:

```
=== STARTING LISTING CREATION ===
Form data: {...}
Image file: ...
Token present: true
Prepared listing data for API: {...}
Calling listingService.createListing...
```

This will show you exactly where the process is failing.

## Common Solutions Summary

| Error | Solution |
|-------|----------|
| Network request failed | Start backend server |
| 401 Unauthorized | Login again |
| 422 Validation Error | Fill all required fields correctly |
| Timeout | Restart backend, check database |
| CORS error | Check backend CORS settings |
| Missing token | Logout and login again |
| Invalid title | Include brand AND model in title |
| No image | Upload an image |
| Database error | Run `create_tables.py` |

## Still Not Working?

### Check These Files:

1. **Frontend API client**: `frontend/src/lib/api.ts`
   - Verify `API_BASE_URL` is `http://localhost:8000/api/v1`

2. **Backend CORS**: `backend/main.py`
   - Verify `localhost:8080` is in `allow_origins`

3. **Backend listings router**: `backend/routers/listings.py`
   - Check the create listing endpoint

### Get Help:

1. **Copy ALL console errors**
2. **Copy backend terminal output**
3. **Screenshot the error**
4. **Open GitHub issue** with all the above information

## Prevention

To avoid future issues:

1. ✅ Always check both servers are running before using the app
2. ✅ Don't close backend/frontend terminals
3. ✅ Login before creating listings
4. ✅ Fill all required fields
5. ✅ Use valid titles (brand + model)
6. ✅ Upload images in supported formats (JPG, PNG)
7. ✅ Keep browser console open during development

---

**Last Updated**: December 23, 2024
