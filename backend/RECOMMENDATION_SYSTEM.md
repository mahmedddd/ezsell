# Recommendation System Documentation

## Overview

The EzSell platform now includes a comprehensive **AI-powered Recommendation System** with **User Analytics Dashboard**. This system tracks user behavior, extracts insights using NLP, and provides personalized product recommendations.

## Features

### 1. **User Activity Tracking**
- Tracks all user interactions: searches, views, clicks, favorites, messages
- Supports both logged-in and anonymous users (via session ID)
- Automatically extracts keywords using NLP from searches and listings
- Records duration spent on listings

### 2. **NLP Keyword Extraction**
- Extracts meaningful keywords from text using regex and pattern matching
- Filters out stopwords and noise
- Identifies brands automatically (Apple, Samsung, Dell, etc.)
- Detects product categories
- Extracts price ranges from text
- Supports multi-word phrases

### 3. **User Interest Profiling**
- Automatically builds user interest profiles
- Aggregates:
  - Favorite categories
  - Top keywords
  - Preferred brands
  - Price range preferences
- Updates in real-time as users interact

### 4. **Personalized Recommendations**
- **Interest-Based**: Recommends based on user's historical interests
- **Similar Items**: Finds listings similar to a specific product
- **Trending**: Shows popular items based on recent activity
- **Collaborative**: Uses keyword similarity between listings

### 5. **Interactive Analytics Dashboard**
- Total activity metrics (searches, views, favorites, messages)
- Top categories with percentages
- Top keywords with relevance scores
- Activity timeline graphs
- Price range insights
- Top brands
- Engagement score (0-100)

## API Endpoints

### Activity Tracking

#### Track User Activity
```http
POST /api/recommendations/track-activity
```

**Request Body:**
```json
{
  "activity_type": "search",  // search, view, click, favorite, message
  "listing_id": 123,          // Optional
  "search_query": "iphone 13 pro",  // Optional
  "category": "Electronics",   // Optional
  "duration_seconds": 45,      // Optional
  "session_id": "uuid-here"    // Optional
}
```

**Response:**
```json
{
  "message": "Activity tracked successfully",
  "activity_id": 456,
  "session_id": "generated-uuid"
}
```

### Recommendations

#### Get Personalized Recommendations
```http
GET /api/recommendations/personalized?limit=20&exclude_viewed=true&min_score=0.1
```

**Authentication:** Required

**Query Parameters:**
- `limit`: Number of recommendations (default: 20, max: 100)
- `exclude_viewed`: Exclude already viewed listings (default: true)
- `min_score`: Minimum relevance score (default: 0.1, range: 0.0-1.0)

**Response:**
```json
{
  "recommendations": [
    {
      "listing_id": 123,
      "score": 0.85,
      "recommendation_type": "interest_based",
      "reason": "Based on your interests in Electronics",
      "listing_details": {
        "title": "iPhone 13 Pro",
        "price": 45000,
        "category": "Electronics",
        "brand": "Apple",
        "condition": "Excellent",
        "images": "[...]",
        "created_at": "2025-12-17T10:00:00"
      }
    }
  ],
  "total": 20,
  "generated_at": "2025-12-20T15:30:00"
}
```

#### Get Similar Listings
```http
POST /api/recommendations/similar
```

**Authentication:** Optional (works for anonymous users)

**Request Body:**
```json
{
  "listing_id": 123,
  "limit": 10
}
```

**Response:** Same format as personalized recommendations

#### Get Trending Listings
```http
GET /api/recommendations/trending?limit=20&category=Electronics
```

**Authentication:** Not required (public endpoint)

**Query Parameters:**
- `limit`: Number of items (default: 20, max: 50)
- `category`: Filter by category (optional)

#### Get "For You" Feed
```http
GET /api/recommendations/for-you?skip=0&limit=20
```

**Authentication:** Optional

Mixed feed of personalized (70%) and trending (30%) content for logged-in users. Shows only trending for anonymous users.

#### Track Recommendation Click
```http
POST /api/recommendations/click/{listing_id}
```

**Authentication:** Required

**Request Body:**
```json
{
  "recommendation_type": "interest_based"
}
```

#### Get Recommended Categories
```http
GET /api/recommendations/categories
```

**Authentication:** Required

**Response:**
```json
{
  "recommended_categories": ["Electronics", "Furniture", "Vehicles"],
  "based_on": "your_interests"
}
```

### Analytics Dashboard

#### Get User Dashboard
```http
GET /api/analytics/dashboard?days=30
```

**Authentication:** Required

**Query Parameters:**
- `days`: Number of days to analyze (default: 30, max: 365)

**Response:**
```json
{
  "total_searches": 45,
  "total_views": 120,
  "total_favorites": 15,
  "total_messages": 8,
  "top_categories": [
    {
      "category": "Electronics",
      "count": 75,
      "percentage": 62.5
    }
  ],
  "top_keywords": [
    {
      "keyword": "iphone",
      "frequency": 20,
      "relevance_score": 0.444
    }
  ],
  "activity_timeline": [
    {
      "date": "2025-12-20",
      "search_count": 5,
      "view_count": 12,
      "click_count": 8,
      "favorite_count": 2
    }
  ],
  "price_range": {
    "min": 5000,
    "max": 50000
  },
  "top_brands": [
    {"brand": "Apple", "count": 15},
    {"brand": "Samsung", "count": 10}
  ],
  "engagement_score": 75.5
}
```

#### Get Activity History
```http
GET /api/analytics/activities?skip=0&limit=50&activity_type=search
```

**Authentication:** Required

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of activities (default: 50, max: 200)
- `activity_type`: Filter by type (optional)

#### Get User Interests
```http
GET /api/analytics/interests
```

**Authentication:** Required

**Response:**
```json
{
  "id": 1,
  "user_id": 123,
  "categories": {
    "Electronics": 75,
    "Furniture": 25
  },
  "keywords": {
    "iphone": 20,
    "laptop": 15,
    "gaming": 10
  },
  "brands": {
    "Apple": 15,
    "Samsung": 10
  },
  "price_range_min": 5000,
  "price_range_max": 50000,
  "last_updated": "2025-12-20T15:30:00",
  "total_activities": 100
}
```

#### Get Search Insights
```http
GET /api/analytics/search-insights?days=7
```

**Authentication:** Required

**Response:**
```json
{
  "searches": [
    {
      "query": "iphone 13 pro",
      "count": 5,
      "avg_results": null,
      "last_searched": "2025-12-20T10:00:00"
    }
  ],
  "trending_categories": ["Electronics", "Furniture"],
  "trending_keywords": ["iphone", "laptop", "gaming"]
}
```

#### Get Recommendation Performance
```http
GET /api/analytics/recommendation-performance?days=30
```

**Authentication:** Required

**Response:**
```json
{
  "total_shown": 100,
  "total_clicked": 25,
  "click_through_rate": 25.0,
  "by_type": {
    "interest_based": {
      "shown": 70,
      "clicked": 20,
      "ctr": 28.57
    },
    "trending": {
      "shown": 30,
      "clicked": 5,
      "ctr": 16.67
    }
  },
  "avg_score": 0.685
}
```

#### Clear Activity History
```http
DELETE /api/analytics/clear-history
```

**Authentication:** Required

Clears all activity history, interests, and recommendation history for the user.

## Database Models

### UserActivity
Tracks individual user interactions:
- `user_id`: User ID (nullable for anonymous)
- `session_id`: Session identifier
- `activity_type`: Type of activity
- `listing_id`: Related listing
- `search_query`: Search text
- `category`: Category
- `keywords`: Extracted keywords (JSON)
- `duration_seconds`: Time spent
- `created_at`: Timestamp

### UserInterest
Aggregated user preferences:
- `user_id`: User ID
- `categories`: Category frequencies (JSON)
- `keywords`: Keyword frequencies (JSON)
- `brands`: Brand preferences (JSON)
- `price_range_min/max`: Price preferences
- `total_activities`: Activity count
- `last_updated`: Last update timestamp

### RecommendationHistory
Tracks shown recommendations:
- `user_id`: User ID
- `listing_id`: Recommended listing
- `recommendation_type`: Algorithm used
- `score`: Relevance score
- `shown_at`: When shown
- `clicked`: Whether clicked
- `clicked_at`: Click timestamp

## How It Works

### 1. Activity Tracking Flow
```
User Action → Track Activity → Extract Keywords → Save to DB → Update Interests
```

### 2. Recommendation Generation
```
1. Get user interests from UserInterest table
2. Query active listings
3. Score each listing based on:
   - Category match (40%)
   - Keyword similarity (40%)
   - Price range match (10%)
   - Brand match (10%)
   - Recency bonus
4. Sort by score
5. Save to history
6. Return recommendations
```

### 3. Keyword Extraction
```
Text → Clean → Extract Multi-word Phrases → Filter Stopwords → 
Prioritize Important Terms → Count Frequencies → Return Top Keywords
```

## Frontend Integration

### Example: Track Search Activity
```javascript
async function trackSearch(query) {
  await fetch('/api/recommendations/track-activity', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      activity_type: 'search',
      search_query: query,
      session_id: getSessionId()
    })
  });
}
```

### Example: Get Recommendations
```javascript
async function getRecommendations() {
  const response = await fetch('/api/recommendations/personalized?limit=20', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  displayRecommendations(data.recommendations);
}
```

### Example: Display Dashboard
```javascript
async function loadDashboard() {
  const response = await fetch('/api/analytics/dashboard?days=30', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const dashboard = await response.json();
  
  // Display metrics
  displayMetrics(dashboard.total_searches, dashboard.total_views);
  
  // Display charts
  displayCategoryChart(dashboard.top_categories);
  displayTimelineChart(dashboard.activity_timeline);
  displayKeywordCloud(dashboard.top_keywords);
}
```

## Recommendation Algorithm Details

### Scoring Formula
```
score = (category_match * 0.4) + (keyword_match * 0.4) + 
        (price_match * 0.1) + (brand_match * 0.1) + recency_bonus
```

### Similarity Calculation
Uses Jaccard similarity for keywords:
```
similarity = intersection(keywords1, keywords2) / union(keywords1, keywords2)
```

## Best Practices

### 1. Track Activities Consistently
- Track searches immediately
- Track views when user opens listing
- Track duration when user leaves listing
- Track favorites when added
- Track messages when sent

### 2. Handle Anonymous Users
- Generate session ID on first visit
- Store in localStorage/cookies
- Pass with every tracking request
- Associate with user ID on login

### 3. Update UI Based on Recommendations
- Show "For You" section on homepage
- Display similar items on listing page
- Show recommended categories in search
- Highlight trending items

### 4. Privacy Considerations
- Allow users to clear history
- Provide opt-out options
- Show transparency about tracking
- Allow data export

## Performance Optimization

### 1. Caching
- Cache user interests (update every 5 minutes)
- Cache trending listings (update hourly)
- Cache recommendation results (5 minutes)

### 2. Batch Processing
- Update interests asynchronously
- Process recommendations in background
- Use database indexes on key fields

### 3. Pagination
- Limit activities per query
- Use skip/limit for large datasets
- Implement infinite scroll

## Future Enhancements

1. **Machine Learning Models**
   - Train collaborative filtering model
   - Use deep learning for embeddings
   - Implement matrix factorization

2. **Advanced Features**
   - Real-time recommendations
   - A/B testing framework
   - Multi-armed bandit algorithms
   - Context-aware recommendations (time, location)

3. **Social Features**
   - Friend recommendations
   - Social proof signals
   - Trending among friends

4. **Business Intelligence**
   - Seller insights
   - Market trends
   - Demand forecasting

## Testing

### Test Recommendation Quality
```python
# Test user with known interests
user_id = 1
engine = RecommendationEngine(db)

# Track multiple activities
engine.track_activity(user_id, "sess1", "search", search_query="iphone 13")
engine.track_activity(user_id, "sess1", "view", listing_id=10)

# Get recommendations
recommendations = engine.get_personalized_recommendations(user_id, limit=10)

# Verify recommendations are relevant
assert len(recommendations) > 0
assert recommendations[0][1] > 0.5  # Score > 0.5
```

## Troubleshooting

### No Recommendations
- Check if user has activities
- Verify UserInterest exists
- Check if listings are active
- Lower min_score threshold

### Low Scores
- Increase activity tracking
- Improve keyword extraction
- Add more product metadata
- Tune scoring weights

### Slow Performance
- Add database indexes
- Implement caching
- Reduce query complexity
- Use pagination

## Support

For issues or questions about the recommendation system:
1. Check API documentation at `/docs`
2. Review this documentation
3. Check database models
4. Test with sample data
