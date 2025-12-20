# Recommendation System - Quick Start Guide

## 🚀 Quick Setup

### 1. Database Migration
The new tables will be created automatically when you start the server:
- `user_activities` - Tracks user interactions
- `user_interests` - Stores aggregated user preferences  
- `recommendation_history` - Tracks shown recommendations

### 2. Start the Backend
```bash
cd ezsell/backend
uvicorn main:app --reload
```

### 3. Test the System
```bash
python test_recommendations.py
```

## 📊 Main Features

### 1. Track User Activity
Every user action should be tracked:

```javascript
// On search
fetch('/api/recommendations/track-activity', {
  method: 'POST',
  body: JSON.stringify({
    activity_type: 'search',
    search_query: userQuery
  })
});

// On listing view
fetch('/api/recommendations/track-activity', {
  method: 'POST',
  body: JSON.stringify({
    activity_type: 'view',
    listing_id: listingId,
    duration_seconds: timeSpent
  })
});
```

### 2. Show Recommendations
```javascript
// Get personalized recommendations
const response = await fetch('/api/recommendations/personalized?limit=20');
const data = await response.json();

// Display recommendations
data.recommendations.forEach(rec => {
  console.log(`${rec.listing_details.title} - Score: ${rec.score}`);
});
```

### 3. Display Analytics Dashboard
```javascript
// Get dashboard data
const dashboard = await fetch('/api/analytics/dashboard?days=30');
const data = await dashboard.json();

// Show metrics
console.log(`Searches: ${data.total_searches}`);
console.log(`Engagement: ${data.engagement_score}/100`);
```

## 🎯 Use Cases

### Homepage: "For You" Section
```http
GET /api/recommendations/for-you?limit=20
```
Shows mixed personalized + trending content

### Listing Page: Similar Items
```http
POST /api/recommendations/similar
Body: { "listing_id": 123, "limit": 10 }
```

### Search: Trending in Category
```http
GET /api/recommendations/trending?category=Electronics&limit=10
```

### Profile: User Dashboard
```http
GET /api/analytics/dashboard?days=30
```

## 🔧 Configuration

### Adjust Scoring Weights
Edit `core/recommendation_engine.py`:
```python
# Category match (40% weight)
score += (category_freq / total_categories) * 0.4

# Keyword match (40% weight)
score += (keyword_matches / total_keywords) * 0.4

# Price range match (10% weight)
score += 0.1

# Brand match (10% weight)
score += 0.1
```

### Add More Keywords
Edit `core/nlp_service.py`:
```python
IMPORTANT_TERMS = {
    # Add your domain-specific terms
    'custom_term1', 'custom_term2', ...
}
```

## 📈 Monitoring

### Check Recommendation Performance
```http
GET /api/analytics/recommendation-performance?days=30
```

Returns:
- Click-through rate (CTR)
- Performance by recommendation type
- Average relevance scores

### View User Activity
```http
GET /api/analytics/activities?limit=50
```

## 🎨 Frontend Integration Examples

### React Component
```jsx
function RecommendationsSection() {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    fetch('/api/recommendations/personalized?limit=10')
      .then(res => res.json())
      .then(data => setRecommendations(data.recommendations));
  }, []);

  return (
    <div>
      <h2>Recommended for You</h2>
      {recommendations.map(rec => (
        <ProductCard 
          key={rec.listing_id}
          {...rec.listing_details}
          score={rec.score}
        />
      ))}
    </div>
  );
}
```

### Vue Component
```vue
<template>
  <div class="dashboard">
    <h2>Your Activity Dashboard</h2>
    <div class="metrics">
      <div>Searches: {{ dashboard.total_searches }}</div>
      <div>Views: {{ dashboard.total_views }}</div>
      <div>Engagement: {{ dashboard.engagement_score }}/100</div>
    </div>
    <CategoryChart :categories="dashboard.top_categories" />
  </div>
</template>

<script>
export default {
  data() {
    return { dashboard: null };
  },
  async mounted() {
    const res = await fetch('/api/analytics/dashboard?days=30');
    this.dashboard = await res.json();
  }
}
</script>
```

## 🐛 Troubleshooting

### "No recommendations available"
**Cause:** User has no activity history yet

**Solution:**
1. Track some activities first
2. Use `/api/recommendations/trending` as fallback
3. Show onboarding to collect preferences

### Low relevance scores
**Cause:** Insufficient data or poor keyword extraction

**Solution:**
1. Increase activity tracking coverage
2. Add more product metadata (brand, detailed description)
3. Lower `min_score` parameter
4. Tune scoring weights

### Slow performance
**Cause:** Large dataset without indexes

**Solution:**
1. Database indexes are automatically created
2. Implement caching for interests
3. Reduce recommendation limit
4. Use pagination

## 📚 Next Steps

1. **Implement Frontend UI**
   - Dashboard page with charts
   - Recommendation sections
   - Activity indicators

2. **Add More Tracking Points**
   - Share actions
   - Price alerts
   - Wishlist additions

3. **Enhance Algorithms**
   - Add collaborative filtering
   - Implement time decay
   - Add location-based recommendations

4. **A/B Testing**
   - Test different algorithms
   - Measure conversion rates
   - Optimize scoring weights

## 📖 Full Documentation

See [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md) for complete API reference and detailed explanations.

## ✅ Checklist

- [x] Database models created
- [x] NLP keyword extraction implemented
- [x] Recommendation engine built
- [x] Analytics dashboard ready
- [x] API endpoints configured
- [ ] Frontend UI implemented
- [ ] User testing completed
- [ ] Performance optimization done

## 🤝 Contributing

When enhancing the recommendation system:
1. Test with real user data
2. Monitor performance metrics
3. Document changes in RECOMMENDATION_SYSTEM.md
4. Update test_recommendations.py

## 📞 Support

For questions or issues:
1. Check [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md)
2. Run tests: `python test_recommendations.py`
3. Check API docs: http://localhost:8000/docs
