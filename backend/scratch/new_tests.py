
# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8 – TESTING AND EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
h1(doc, 'Testing and Evaluation')

h2(doc, 'API & Module Endpoint Testing')
para(doc, 'The following tables detail the endpoint-level test cases and their execution outcomes across the core modules of the application.')

h3(doc, '8.1.1 M1 — Profile Management Tests')
para(doc, 'Table 33: M1 Profile Management Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M1-1', 'Register new user with email & phone', 'POST /auth/register', '201 Created, user in DB', 'Pass'],
    ['T-M1-2', 'Login with correct credentials', 'POST /auth/login', '200 OK, JWT returned', 'Pass'],
    ['T-M1-3', 'Login with wrong password', 'POST /auth/login', '401 Unauthorized', 'Pass'],
    ['T-M1-4', 'Google OAuth sign-in flow', 'Browser OAuth redirect', 'Token set, user created/fetched', 'Pass'],
    ['T-M1-5', 'Access secured endpoint without token', 'GET /users/me', '401 Unauthorized', 'Pass'],
    ['T-M1-6', 'Update profile fields', 'PATCH /users/me', '200 OK, fields updated', 'Pass'],
    ['T-M1-7', 'Upload avatar image', 'POST /users/me/avatar', '200 OK, avatar_url set', 'Pass'],
    ['T-M1-8', 'Admin flag verification', 'GET /users/me as admin', 'is_admin: true in response', 'Pass']
])

h3(doc, '8.1.2 M2 — Product Listings Tests')
para(doc, 'Table 34: M2 Product Listings Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M2-1', 'Create listing with 3 images', 'POST /listings/', '201 Created', 'Pass'],
    ['T-M2-2', 'Fetch listing by ID', 'GET /listings/{id}', '200 OK, full listing data', 'Pass'],
    ['T-M2-3', 'Edit listing title', 'PATCH /listings/{id}', '200 OK, title updated', 'Pass'],
    ['T-M2-4', 'Delete listing as owner', 'DELETE /listings/{id}', '200 OK, removed from DB', 'Pass'],
    ['T-M2-5', 'Hide listing (toggle)', 'PATCH /listings/{id}/toggle-visibility', 'is_active: false', 'Pass'],
    ['T-M2-6', 'Mark listing as sold', 'PATCH /listings/{id}/mark-sold', 'is_sold: true', 'Pass'],
    ['T-M2-7', 'Submit listing for approval', 'POST /listings/', 'approval_status: pending', 'Pass'],
    ['T-M2-8', 'Admin approve listing', 'PATCH /approvals/{id}/approve', 'approval_status: approved', 'Pass'],
    ['T-M2-9', 'Search by category', 'GET /listings/?category=mobile', 'Filtered results returned', 'Pass'],
    ['T-M2-10', 'AI title validation', 'POST /listings/validate-title', 'Valid/invalid flag returned', 'Pass']
])

h3(doc, '8.1.3 M3 — Price Prediction Tests')
para(doc, 'Table 35: M3 Price Prediction Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M3-1', 'Predict price for mobile phone (ML)', 'POST /predictions/mobile', 'Price range + confidence score', 'Pass'],
    ['T-M3-2', 'Predict price for laptop (ML)', 'POST /predictions/laptop', 'Price range + confidence score', 'Pass'],
    ['T-M3-3', 'Predict price for furniture (ML)', 'POST /predictions/furniture', 'Price range + confidence score', 'Pass'],
    ['T-M3-4', 'Groq LLM price estimation', 'POST /predictions/advanced', 'LLM-sourced price + OLX snippets', 'Pass'],
    ['T-M3-5', 'OLX DuckDuckGo scraping', 'Internal service call', 'Prices extracted and IQR-filtered', 'Pass'],
    ['T-M3-6', 'Prediction on create form', 'Frontend UX', 'Suggested price shown to seller', 'Pass'],
    ['T-M3-7', 'Confidence score < 50% flagged', 'Frontend UX', 'Low confidence warning shown', 'Pass']
])

h3(doc, '8.1.4 M4 — Recommendations Tests')
para(doc, 'Table 36: M4 Recommendations Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M4-1', 'Log view activity', 'POST /recommendations/activity', '200 OK, activity recorded', 'Pass'],
    ['T-M4-2', 'Get personalized feed', 'GET /recommendations/', 'Returns interest-matched listings', 'Pass'],
    ['T-M4-3', 'Get trending for anonymous', 'GET /recommendations/trending', 'Returns top-viewed listings', 'Pass'],
    ['T-M4-4', 'Filter by price range', 'GET /listings/?min_price=X&max_price=Y', 'Listings within range returned', 'Pass'],
    ['T-M4-5', 'Semantic similarity search', 'GET /listings/?q=leather+sofa', 'NLP-ranked results returned', 'Pass']
])

h3(doc, '8.1.5 M5 — Analytical Dashboard Tests')
para(doc, 'Table 37: M5 Analytical Dashboard Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M5-1', 'Admin fetch dashboard stats', 'GET /analytics/overview', 'User/listing/revenue totals', 'Pass'],
    ['T-M5-2', 'Admin view all users', 'GET /users/ (admin)', 'Full user list with details', 'Pass'],
    ['T-M5-3', 'Admin view all listings', 'GET /listings/ (admin)', 'All listings regardless of status', 'Pass'],
    ['T-M5-4', 'Admin reject listing with reason', 'PATCH /approvals/{id}/reject', 'Status set, rejection reason saved', 'Pass'],
    ['T-M5-5', 'Admin view support tickets', 'GET /support/admin/tickets', 'All tickets with user info', 'Pass'],
    ['T-M5-6', 'Support requests count card', 'Frontend UX', 'Correct total + open count shown', 'Pass']
])

h3(doc, '8.1.6 M6 — AR / Try-On Tests')
para(doc, 'Table 38: M6 AR / Try-On Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M6-1', 'Generate procedural 3D model', 'POST /products/{id}/assets/generate', 'GLB/USDZ URLs returned', 'Pass'],
    ['T-M6-2', 'Launch WebAR viewer', 'Frontend UX (/ar/{id})', 'model-viewer loads GLB', 'Pass'],
    ['T-M6-3', 'Trigger Tripo AI generation', 'POST /products/{id}/assets/generate-3d', 'Task ID returned, polling starts', 'Pass'],
    ['T-M6-4', 'Poll AI generation status', 'GET /products/{id}/assets/generate-3d/{task_id}', 'status: done, URLs available', 'Pass'],
    ['T-M6-5', 'Admin manual GLB upload', 'POST /products/{id}/assets/upload-glb', 'GLB URL stored in DB', 'Pass'],
    ['T-M6-6', 'iOS USDZ AR QuickLook', 'iOS Safari', 'Native AR viewer launched', 'Pass'],
    ['T-M6-7', 'Fixed scale lock', 'Frontend UX', 'Model does not resize freely', 'Pass']
])

h3(doc, '8.1.7 M7 — Fraud Prevention Tests')
para(doc, 'Table 39: M7 Fraud Prevention Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M7-1', 'Detect duplicate listing', 'POST duplicate listing', 'listing_hash collision detected', 'Pass'],
    ['T-M7-2', 'Detect duplicate image', 'POST listing with reused image', 'image_hash collision flagged', 'Pass'],
    ['T-M7-3', 'Fraud flags stored', 'DB inspection', 'JSON array in fraud_flags column', 'Pass'],
    ['T-M7-4', 'Flagged listing surfaced to admin', 'Admin Dashboard', 'Flagged items appear in review queue', 'Pass'],
    ['T-M7-5', 'Reject with documented reason', 'PATCH /approvals/{id}/reject + reason', 'rejection_reason field saved in DB', 'Pass']
])

h3(doc, '8.1.8 M8 — Support & Notifications Tests')
para(doc, 'Table 40: M8 Support & Notifications Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M8-1', 'Submit support ticket', 'POST /support/tickets', '201 Created, ticket in DB', 'Pass'],
    ['T-M8-2', 'Submit bug report', 'POST /support/tickets (type: bug)', '201 Created', 'Pass'],
    ['T-M8-3', 'Admin fetch all tickets', 'GET /support/admin/tickets', 'All tickets with user info returned', 'Pass'],
    ['T-M8-4', 'Admin update ticket to working', 'PATCH /support/admin/tickets/{id}/status', 'Status updated, notification created', 'Pass'],
    ['T-M8-5', 'Admin update ticket to done', 'PATCH /support/admin/tickets/{id}/status', 'Status updated, notification created', 'Pass'],
    ['T-M8-6', 'User fetch notifications', 'GET /notifications', 'Notification list returned', 'Pass'],
    ['T-M8-7', 'Unread count endpoint', 'GET /notifications/unread/count', 'Correct count returned', 'Pass'],
    ['T-M8-8', 'Mark notification as read', 'POST /notifications/{id}/read', 'is_read: true set in DB', 'Pass'],
    ['T-M8-9', 'Mark all notifications as read', 'POST /notifications/read-all', 'All user notifications marked read', 'Pass'],
    ['T-M8-10', 'Bell badge shows unread count', 'Frontend UX', 'Badge visible with correct number', 'Pass'],
    ['T-M8-11', 'Notification popover renders', 'Frontend UX', 'Alert list visible in dropdown', 'Pass'],
    ['T-M8-12', 'Click notification navigates user', 'Frontend UX', 'User routed to /profile', 'Pass']
])

h3(doc, '8.1.9 M9 — Messaging Tests')
para(doc, 'Table 41: M9 Messaging Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M9-1', 'Send message to seller', 'POST /messages/', '201 Created, stored in DB', 'Pass'],
    ['T-M9-2', 'Fetch conversations list', 'GET /messages/conversations', 'All threads returned', 'Pass'],
    ['T-M9-3', 'Read messages in a conversation', 'GET /messages/{conversation_id}', 'Message history returned', 'Pass'],
    ['T-M9-4', 'Unread message count in nav', 'GET /messages/unread/count', 'Correct count in badge', 'Pass'],
    ['T-M9-5', 'Mark conversation as read', 'POST /messages/{id}/read', 'is_read: true for all messages', 'Pass']
])

h3(doc, '8.1.10 M10 — Favorites & Dashboard Tests')
para(doc, 'Table 42: M10 Favorites & Dashboard Tests', style='Caption')
simple_table(doc, ['Test ID', 'Test Case', 'Method / Layer', 'Expected Result', 'Outcome'], [
    ['T-M10-1', 'Add listing to favorites', 'POST /favorites/{id}', '200 OK, saved in DB', 'Pass'],
    ['T-M10-2', 'Remove listing from favorites', 'DELETE /favorites/{id}', '200 OK, removed from DB', 'Pass'],
    ['T-M10-3', 'Fetch all user favorites', 'GET /favorites/', 'Full favorites list returned', 'Pass'],
    ['T-M10-4', 'Check if listing is favorited', 'GET /favorites/{id}/check', 'is_favorited: true/false', 'Pass'],
    ['T-M10-5', 'Dashboard shows own listings', 'GET /listings/my', 'Only user\'s listings returned', 'Pass'],
    ['T-M10-6', 'Dashboard status count cards', 'Frontend UX', 'Correct active/hidden/sold counts', 'Pass']
])

h2(doc, 'Unit Testing')
para(doc, 'Unit testing checks individual components to ensure each one behaves as expected.')

h3(doc, '8.2.1 Unit Testing 1: Validate login functionality with correct and incorrect inputs.')
para(doc, 'Testing Objective: To ensure the login form is working correctly with valid and invalid inputs.')
para(doc, 'Table 43: Unit Testing 1 login Functionalities', style='Caption')
simple_table(doc, ['No.', 'Test case', 'Attribute and value', 'Expected result', 'Result'], [
    ['1', 'Check valid login', 'username: ahmed\nPassword: ahmed123', 'User is logged in and redirected to dashboard.', 'Pass'],
    ['2', 'Invalid email format', 'username: ahme', 'Error, no such sort of username', 'Pass'],
    ['3', 'Invalid password', 'Password: EZsell123', 'Dashboard unaccessible, login page refresh', 'Pass']
])

h3(doc, '8.2.2 Unit Testing 2: Listing Image Upload')
para(doc, 'Testing Objective: Ensure supported file types are accepted and invalid formats are rejected.')
para(doc, 'Table 44: Unit Testing 2 Listing Image Upload', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Result'], [
    ['1', 'Upload supported image', 'image.jpg', 'File accepted and uploaded to storage', 'Pass'],
    ['2', 'Upload unsupported format', 'file.txt', 'Wont show any other sort of file other than jpg, jpeg, png', 'Pass'],
    ['3', 'Upload large file', 'big_image.webp (10MB)', 'Error', 'Pass']
])

h3(doc, '8.2.3 Unit Testing 3: Price Prediction')
para(doc, 'Testing Objective: Ensure that the AI price prediction module correctly processes features and returns a valid predicted price with confidence.')
para(doc, 'Table 45: Unit Testing 3 Price Prediction', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Result'], [
    ['1', 'Predict price for mobile', 'title=Samsung s23, condition=used', 'Return predicted price + confidence', 'Pass'],
    ['2', 'Predict price for laptop', 'brand=HP omen, core i3, RAM=8GB', 'Return predicted price + confidence', 'Pass'],
    ['3', 'Missing required feature', 'condition = null', 'No Prediction', 'Pass']
])

h3(doc, '8.2.4 Unit Testing 4: Listing Creation (Post Ad)')
para(doc, 'Testing Objective: Ensure that new listings are created successfully with all required fields.')
para(doc, 'Table 46: Unit Testing 4 Listing Creation', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Result'], [
    ['1', 'Valid listing', 'title, desc, price, category, image provided', 'Listing saved successfully', 'Pass'],
    ['2', 'Missing title', 'title=null', 'Error', 'Pass'],
    ['3', 'Price not numeric', 'price="ten thousand"', 'Error', 'Pass'],
    ['4', 'Image missing', 'no images uploaded', 'Error', 'Pass']
])

h3(doc, '8.2.5 Unit Testing 5: User Dashboard Data Fetch')
para(doc, 'Testing Objective: Ensure that dashboard fetches correct analytics based on user_id.')
para(doc, 'Table 47: Unit Testing 5 Dashboard Data', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Result'], [
    ['1', 'Fetch dashboard data', 'user_id valid', 'Returns totals (views, listings, contacts)', 'Pass'],
    ['2', 'No listings', 'user with 0 listings', 'Show zero analytics', 'Pass'],
    ['3', 'Invalid user_id', 'user_id = null', 'Error', 'Pass']
])

h3(doc, '8.2.6 Unit Testing 6: Admin Analytics Dashboard')
para(doc, 'Testing Objective: Verify correct aggregation of platform-wide metrics.')
para(doc, 'Table 48: Unit Testing 6 Admin Analytics', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Result'], [
    ['1', 'Fetch system metrics', 'none', 'Return totals: users, listings, active listings', 'Pass'],
    ['2', 'No users available', 'empty database', 'Display zero metrics, no errors', 'Pass']
])

h3(doc, '8.2.7 Unit Testing 7: AR Room Analysis Functions')
para(doc, 'Testing Objective: Ensure that AR room analysis helper functions correctly process images and detect room properties.')
para(doc, 'Table 49: Unit Testing 7 AR Analysis', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Result'], [
    ['1', 'Detect dominant colors', 'room image with blue walls', 'Returns color: "Blue", hex: "#4A90E2"', 'Pass'],
    ['2', 'Estimate room dimensions', 'room image with visible walls', 'Returns width, height, depth estimates', 'Pass'],
    ['3', 'Detect room style', 'modern furniture in image', 'Returns style: "Modern", confidence: 85%', 'Pass'],
    ['4', 'Calculate suitability', 'furniture vs room dimensions', 'Returns score: 75–95%', 'Pass'],
    ['5', 'Invalid image format', 'file: not an image', 'Returns error: "Invalid image"', 'Pass']
])

h2(doc, 'Functional Testing')
para(doc, 'The functional testing will take place after the unit testing. In this functional testing, the functionality of each of the module is tested. This is to ensure that the system produced meets the specifications and requirements.')

h3(doc, '8.3.1 Functional Testing 1: Upload Listing Images')
para(doc, 'Testing Objective: Ensure that uploaded listing images/files are accepted for supported formats and rejected otherwise.')
para(doc, 'Table 50: Functional Testing 1', style='Caption')
simple_table(doc, ['No.', 'Test case', 'Attribute and value', 'Expected result', 'Actual result', 'Result'], [
    ['1', 'Upload valid image', 'image.jpg', 'File accepted and uploaded to storage', 'Uploaded successfully', 'Pass'],
    ['2', 'Upload unsupported file type', 'file.txt', 'Won’t allow', 'Didn’t allowed', 'Pass'],
    ['3', 'Upload large file (>10MB)', 'Big image.webp', 'Display warning: "File size too large"', 'Warning shown', 'Pass']
])

h3(doc, '8.3.2 Functional Testing 2: AI Price Prediction')
para(doc, 'Testing Objective: Verify that the price prediction engine returns valid prices and confidence for different listings.')
para(doc, 'Table 51: Functional Testing 2', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'Predict price for mobile device', 'Category: Mobile, Brand: Samsung, RAM: 8GB, Storage: 128GB', 'Display predicted price along with confidence range', 'Prediction displayed correctly', 'Pass'],
    ['2', 'Predict price for laptop', 'Category: Laptop, Brand: HP, Processor: Intel i5, RAM: 8GB', 'Display predicted price along with confidence range', 'Prediction displayed correctly', 'Pass'],
    ['3', 'Prediction with high confidence', 'Well-defined and complete specifications', 'Display narrow confidence range', 'High confidence shown correctly', 'Pass'],
    ['4', 'Auto-approval range display', 'Successful price prediction', 'Display green auto-approval price range', 'Auto-approval range displayed correctly', 'Pass'],
    ['5', 'Re-prediction on field change', 'User modifies product specifications', 'System automatically triggers a new price prediction', 'Auto-prediction working correctly', 'Pass']
])

h3(doc, '8.3.3 Functional Testing 3: User & Admin Dashboard Analytics')
para(doc, 'Testing Objective: Ensure that dashboards correctly display metrics for users and admins.')
para(doc, 'Table 52: Functional Testing 3', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'User dashboard with listings', 'Valid user_id with existing listings', 'Display total listings, total views, and contact count', 'Metrics displayed correctly', 'Pass'],
    ['2', 'User dashboard with no listings', 'User with zero listings', 'Display message: "No data available"', 'Message displayed correctly', 'Pass'],
    ['3', 'Admin dashboard metrics', 'Complete system data available', 'Display total users, total listings, and active listings', 'Metrics displayed correctly', 'Pass'],
    ['4', 'Admin dashboard with empty database', 'No users or listings in system', 'Display zero values for all metrics', 'Zero metrics displayed correctly', 'Pass'],
    ['5', 'Admin dashboard top sellers', 'Users with multiple listings', 'Display top 5 sellers ranked by number of listings', 'Top sellers displayed correctly', 'Pass']
])

h3(doc, '8.3.4 Functional Testing 4: Listing Creation & Validation')
para(doc, 'Testing Objective: Ensure that listing creation, duplicate prevention, and price validation work correctly.')
para(doc, 'Table 53: Functional Testing 4', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'Create listing with valid data', 'Title, description, price, category, images provided', 'Listing created successfully and user is redirected to dashboard', 'Listing created and visible on dashboard', 'Pass'],
    ['2', 'Create listing with duplicate title', 'Title already exists (case-insensitive)', 'System rejects submission with error', 'Duplicate title rejected correctly', 'Pass'],
    ['3', 'Create listing with duplicate images', 'Same image uploaded twice', 'System rejects submission with error', 'Duplicate image rejected', 'Pass'],
    ['4', 'Create listing with alphabetic price', 'Price entered as "five thousand"', 'System rejects submission with error', 'Alphabetic price rejected', 'Pass'],
    ['5', 'Create listing with valid images', '1–7 images, JPG/PNG format, each under 10MB', 'Images uploaded successfully', 'Images uploaded and displayed correctly', 'Pass']
])

h3(doc, '8.3.5 Functional Testing 5: Admin Approval System')
para(doc, 'Testing Objective: Ensure that the administrator can correctly approve, reject, and manage pending listings')
para(doc, 'Table 54: Functional Testing 5', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'View pending listings', 'Admin logged in', 'Display all listings with status set to "Pending"', 'Pending listings displayed correctly', 'Pass'],
    ['2', 'Approve listing manually', 'Admin clicks Approve button', 'Listing status changes to "Active" and notification is sent to seller', 'Status changed to active successfully', 'Pass'],
    ['3', 'Reject listing manually', 'Admin clicks Reject and provides reason', 'Listing status changes to "Rejected" and rejection reason is saved', 'Listing rejected with reason saved', 'Pass'],
    ['4', 'Auto-approval for listings', 'Price within ±20% of predicted price', 'Listing is automatically approved without admin intervention', 'Auto-approved successfully', 'Pass'],
    ['5', 'Manual review for listings', 'Price outside ±20% of predicted price', 'Listing is sent to admin queue for manual review', 'Listing sent to pending review correctly', 'Pass']
])

h3(doc, '8.3.6 Functional Testing 6: 3D AR (Augmented Reality) Features')
para(doc, 'Testing Objective: Ensure that 3D AR model upload, preview, customization, and mobile viewing work correctly for furniture listings.')
para(doc, 'Table 55: Functional Testing 6', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'Upload room photo for AR analysis', 'Valid JPG/PNG image, furniture listing', 'Room analyzed for dimensions, style, lighting; AI insights displayed', 'Room analysis working correctly', 'Pass'],
    ['2', 'AR canvas preview with furniture', 'Room photo uploaded', 'Canvas viewer opens; furniture rendered as 3D rectangles with proper perspective', 'Canvas preview working correctly', 'Pass'],
    ['3', 'AR customization (color/material)', 'Change furniture material', 'Furniture color/material updates in real-time on canvas', 'Customization working correctly', 'Pass'],
    ['4', 'Drag and drop furniture placement', 'Drag furniture objects on canvas', 'Furniture repositions with shadows and perspective maintained', 'Drag-and-drop working correctly', 'Pass'],
    ['5', 'Multiple view angles', 'Switch between front/3D/top views', 'Canvas updates to display different perspective angles', 'View switching working correctly', 'Pass']
])

h2(doc, 'Business Rules Testing')
para(doc, 'Testing Objective: Verify that business logic rules are correctly applied for listings, price predictions, and anomalies.')
para(doc, 'Table 56: Business Rules Testing Matrix', style='Caption')
simple_table(doc, ['Condition / Rule', 'R1', 'R2', 'R3', 'R4', 'R5'], [
    ['Listing Title Same?', 'Yes', 'No', 'No', 'No', 'No'],
    ['Price unusually high?', 'Yes', 'Yes', 'No', 'No', 'No'],
    ['Very old listing?', 'No', 'No', 'No', 'Yes', 'No'],
    ['Invalid Input / Data Error?', 'No', 'No', 'No', 'Yes', 'No'],
    ['Action', 'A1 (Flag duplicate)', 'A2 (Mark unusually high price)', 'A3 (Flag outdated listing)', 'A4 (Flag invalid data entry)', 'A5 (No anomaly)']
])

h2(doc, 'Integration Testing')
para(doc, 'Integration testing ensures that different modules work correctly when connected together.')

h3(doc, '8.5.1 Integration Testing 1: User Registration - Email Verification - Login')
para(doc, 'Testing Objective: Verify that the user registration, authentication, and initial dashboard flow are correctly integrated.')
para(doc, 'Table 57: Integration Testing 1', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'User registers and account is created', 'Valid username, email, and password', 'User account is created in the database and a success message is displayed', 'Account created successfully', 'Pass'],
    ['2', 'User registers with duplicate username', 'Username already exists', 'System displays error message', 'Duplicate username rejected', 'Pass'],
    ['3', 'Newly registered user logs in', 'Valid newly registered credentials', 'User logs in successfully and is redirected to the user dashboard', 'Login working correctly', 'Pass'],
    ['4', 'Newly registered user views empty dashboard', 'New user with no listings', 'Dashboard displays "No listings yet" message', 'Empty dashboard state working correctly', 'Pass']
])

h3(doc, '8.5.2 Integration Testing 2: Listing Upload - AI Price Prediction - Dashboard Update')
para(doc, 'Testing Objective: Verify the end-to-end flow from uploading a listing to predicting price and updating dashboards.')
para(doc, 'Table 58: Integration Testing 2', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'Full listing pipeline', 'User uploads a new listing', 'Data is saved successfully, price is predicted, and dashboards are updated', 'End-to-end process worked correctly', 'Pass'],
    ['2', 'Auto-approval triggered', 'Listing price within approved range', 'Price predicted → listing auto-approved → listing becomes active in feed', 'Auto-approval working correctly', 'Pass'],
    ['3', 'Manual review triggered', 'Listing price outside approved range', 'Price predicted → listing sent to admin → status set to pending', 'Manual review triggered successfully', 'Pass'],
    ['4', 'User dashboard updates', 'User creates a new listing', 'Listing count increases on user dashboard', 'User dashboard updated correctly', 'Pass'],
    ['5', 'Admin dashboard updates', 'New listing added to system', 'Total listings count increases in admin analytics', 'Admin dashboard updated correctly', 'Pass']
])

h3(doc, '8.5.3 Integration Testing 3: Login - Dashboard - Listings')
para(doc, 'Table 59: Integration Testing 3', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'User logs in and dashboard loads', 'Valid user credentials', 'Dashboard loads successfully with listings feed', 'Dashboard loaded correctly', 'Pass'],
    ['2', 'User clicks Post Ad', 'Logged-in user', 'User is able to create and upload a listing', 'Listing upload works correctly', 'Pass'],
    ['3', 'Buyer-behavior browsing', 'User behaving as buyer only', 'User can browse and scroll listings without posting', 'Browsing works correctly', 'Pass'],
    ['4', 'User views listings', 'Any logged-in user', 'User can view all available listings', 'Listings displayed correctly', 'Pass']
])

h3(doc, '8.5.4 Integration Testing 4: Category Selection - Form Fields - Price Prediction')
para(doc, 'Testing Objective: Verify that dynamic form fields update correctly based on category selection.')
para(doc, 'Table 60: Integration Testing 4', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'User selects Mobile category', 'Category set to Mobile', 'Brand, RAM, storage fields are displayed', 'Mobile-specific fields displayed correctly', 'Pass'],
    ['2', 'User enters mobile specifications', 'Brand: Apple, RAM: 8GB, Storage: 256GB', 'Predicted price is displayed along with confidence range', 'Price prediction working correctly', 'Pass'],
    ['3', 'User selects Laptop category', 'Category set to Laptop', 'Processor, GPU, RAM, storage fields displayed', 'Laptop-specific fields displayed correctly', 'Pass'],
    ['4', 'User changes category selection', 'Switch from Mobile to Laptop', 'Mobile fields are hidden and laptop fields are displayed', 'Fields updated correctly', 'Pass'],
    ['5', 'User completes specifications', 'All required fields filled', 'Green auto-approval price range is displayed', 'Auto-approval range displayed correctly', 'Pass']
])

h3(doc, '8.5.5 Integration Testing 5: Favorites System - Dashboard - Listing Updates')
para(doc, 'Testing Objective: Verify that the favorites system is correctly integrated.')
para(doc, 'Table 61: Integration Testing 5', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'User adds a listing to favorites', 'User clicks favorite icon', 'Favorite is saved to database', 'Favorite saved successfully', 'Pass'],
    ['2', 'User adds favorite and dashboard updates', 'Listing added to favorites', 'Favorite count increases on user dashboard', 'Dashboard updated correctly', 'Pass'],
    ['3', 'User views favorites', 'User navigates to favorites page', 'All favorited listings are displayed', 'Favorites displayed correctly', 'Pass'],
    ['4', 'User removes a favorite', 'User clicks unfavorite icon', 'Favorite is removed, icon changes to unfilled state', 'Favorite removed successfully', 'Pass'],
    ['5', 'Listing deletion updates favorites', 'Seller deletes a listing', 'Listing is automatically removed from all users’ favorites', 'Favorites cleanup working correctly', 'Pass']
])

h3(doc, '8.5.6 Integration Testing 6: 3D AR Model Upload → Storage → Preview')
para(doc, 'Testing Objective: Verify the end-to-end 3D AR workflow.')
para(doc, 'Table 62: Integration Testing 6', style='Caption')
simple_table(doc, ['No.', 'Test Case', 'Attribute and Value', 'Expected Result', 'Actual Result', 'Result'], [
    ['1', 'Upload 3D model and store on server', 'Upload GLB file for furniture', 'Model saved to ar_previews directory', 'Model stored successfully', 'Pass'],
    ['2', 'AR badge displayed', 'Furniture listing with 3D model', 'AR View badge visible on listing card', 'Badge displayed correctly', 'Pass'],
    ['3', 'User clicks AR preview', 'Click View in AR button', 'AR viewer opens; 3D model renders', 'AR viewer working correctly', 'Pass'],
    ['4', 'User customizes AR model', 'Change color/material and save', 'Customizations saved and reflected in all AR views', 'Customizations saved successfully', 'Pass']
])
