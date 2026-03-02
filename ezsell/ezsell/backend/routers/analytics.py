"""
Analytics and Dashboard Router
Provides user insights, activity analytics, and visualization data
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
import json
from collections import Counter

from models.database import (
    get_db, User, Listing, UserActivity, UserInterest,
    Favorite, Message, RecommendationHistory
)
from core.security import get_current_user
from core.recommendation_engine import RecommendationEngine
from schemas.recommendation_schemas import (
    UserDashboard, CategoryInsight, KeywordInsight,
    ActivityTimeline, UserActivityResponse, UserInterestResponse,
    SearchInsight, PopularSearches, UserActivityCreate
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _resolve_user(token_data, db: Session) -> User:
    """Resolve TokenData → full User ORM object (raises 401 if not found)"""
    user = db.query(User).filter(User.username == token_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/track")
async def track_activity(
    activity: UserActivityCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track a user activity (search, view, click, favorite).
    Called by the frontend whenever a user performs an action.
    """
    user = _resolve_user(current_user, db)

    # Category synonym map — mirrors the one in listings.py
    CATEGORY_SYNONYMS = {
        'mobile': 'mobile', 'mobiles': 'mobile', 'phone': 'mobile', 'phones': 'mobile', 
        'smartphone': 'mobile', 'smartphones': 'mobile', 'cellphone': 'mobile', 
        'handset': 'mobile', 'iphone': 'mobile', 'android': 'mobile',
        'laptop': 'laptop', 'laptops': 'laptop', 'notebook': 'laptop',
        'notebooks': 'laptop', 'macbook': 'laptop', 'computer': 'laptop', 'pc': 'laptop',
        'sofa': 'furniture', 'sofas': 'furniture', 'couch': 'furniture', 'furniture': 'furniture',
        'couches': 'furniture', 'bed': 'furniture', 'beds': 'furniture',
        'wardrobe': 'furniture', 'wardrobes': 'furniture', 'table': 'furniture',
        'tables': 'furniture', 'chair': 'furniture', 'chairs': 'furniture',
        'desk': 'furniture', 'desks': 'furniture', 'cabinet': 'furniture',
        'shelf': 'furniture', 'shelves': 'furniture', 'dresser': 'furniture',
    }

    activity_type = activity.activity_type
    search_query = activity.search_query
    listing_id = activity.listing_id
    category = activity.category
    session_id = activity.session_id or "web"
    duration_seconds = activity.duration_seconds

    # Normalize category strings (Plural -> Singular, handle "all")
    if category:
        category = category.lower().strip()
        if category in ['all', '']:
            category = None
        elif category == 'mobiles':
            category = 'mobile'
        elif category == 'laptops':
            category = 'laptop'

    # Use RecommendationEngine for robust tracking + interest updates
    engine = RecommendationEngine(db)
    engine.track_activity(
        user_id=user.id,
        session_id=session_id,
        activity_type=activity_type,
        listing_id=listing_id,
        search_query=search_query,
        category=category,
        duration_seconds=duration_seconds
    )

    print(f"DEBUG ALPHA-Z: Tracked {activity_type} for user {user.id} via RecommendationEngine")

    return {"status": "tracked", "activity_type": activity_type}


@router.get("/dashboard", response_model=UserDashboard)
async def get_user_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive user dashboard with insights
    """
    current_user = _resolve_user(current_user, db)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all activities in date range
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id,
        UserActivity.created_at >= start_date
    ).all()
    
    # Count activities by type
    total_searches = sum(1 for a in activities if a.activity_type == 'search')
    total_views = sum(1 for a in activities if a.activity_type == 'view')
    total_clicks = sum(1 for a in activities if a.activity_type == 'click')
    
    # Get favorites count
    total_favorites = db.query(func.count(Favorite.id)).filter(
        Favorite.user_id == current_user.id
    ).scalar()
    
    # Get messages count
    total_messages = db.query(func.count(Message.id)).filter(
        Message.sender_id == current_user.id
    ).scalar()
    
    # Get top categories
    categories = []
    for activity in activities:
        if activity.category:
            categories.append(activity.category)
    
    category_counts = Counter(categories)
    total_categories = sum(category_counts.values())
    
    top_categories = [
        CategoryInsight(
            category=cat,
            count=count,
            percentage=round((count / total_categories * 100), 2) if total_categories > 0 else 0
        )
        for cat, count in category_counts.most_common(5)
    ]
    
    # Get top keywords
    all_keywords = []
    for activity in activities:
        if activity.keywords:
            try:
                keywords = json.loads(activity.keywords)
                all_keywords.extend(keywords)
            except json.JSONDecodeError:
                pass
    
    keyword_counts = Counter(all_keywords)
    total_keywords = sum(keyword_counts.values())
    
    top_keywords = [
        KeywordInsight(
            keyword=kw,
            frequency=count,
            relevance_score=round((count / total_keywords), 3) if total_keywords > 0 else 0
        )
        for kw, count in keyword_counts.most_common(10)
    ]
    
    # Get activity timeline (daily aggregation)
    timeline_data = {}
    for activity in activities:
        date_key = activity.created_at.date().isoformat()
        if date_key not in timeline_data:
            timeline_data[date_key] = {
                'search_count': 0,
                'view_count': 0,
                'click_count': 0,
                'favorite_count': 0
            }
        
        if activity.activity_type == 'search':
            timeline_data[date_key]['search_count'] += 1
        elif activity.activity_type == 'view':
            timeline_data[date_key]['view_count'] += 1
        elif activity.activity_type == 'click':
            timeline_data[date_key]['click_count'] += 1
        elif activity.activity_type == 'favorite':
            timeline_data[date_key]['favorite_count'] += 1

    # Pad timeline with last 7 days to ensure a continuous line in charts
    today = datetime.utcnow().date()
    padded_timeline = {}
    for i in range(6, -1, -1):
        date_str = (today - timedelta(days=i)).isoformat()
        padded_timeline[date_str] = {
            'search_count': 0,
            'view_count': 0,
            'click_count': 0,
            'favorite_count': 0
        }
    
    # Fill in actual data
    for date, counts in timeline_data.items():
        if date in padded_timeline:
            padded_timeline[date] = counts
        elif datetime.fromisoformat(date).date() >= (today - timedelta(days=days)):
            # Also include data outside the 7-day window if it exists within the requested range
            padded_timeline[date] = counts

    activity_timeline = [
        ActivityTimeline(date=date, **counts)
        for date, counts in sorted(padded_timeline.items())
    ]
    
    # Get user interests for price range
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id
    ).first()
    
    price_range = {
        'min': user_interest.price_range_min if user_interest else None,
        'max': user_interest.price_range_max if user_interest else None
    }
    
    # Get top brands
    brands = []
    for activity in activities:
        if activity.listing_id:
            listing = db.query(Listing).filter(Listing.id == activity.listing_id).first()
            if listing and listing.brand:
                brands.append(listing.brand)
    
    brand_counts = Counter(brands)
    top_brands = [
        {'brand': brand, 'count': count}
        for brand, count in brand_counts.most_common(5)
    ]
    
    # Calculate engagement score (0-100)
    engagement_factors = [
        min(total_searches / 5, 1) * 20,   # Up to 20 points (5 searches)
        min(total_views / 20, 1) * 30,    # Up to 30 points (20 views)
        min(total_favorites / 5, 1) * 25,  # Up to 25 points (5 favorites)
        min(total_messages / 3, 1) * 15,   # Up to 15 points (3 messages)
        min(len(activities) / 50, 1) * 10  # Up to 10 points (50 total activities)
    ]
    engagement_score = round(sum(engagement_factors), 1)
    
    return UserDashboard(
        total_searches=total_searches,
        total_views=total_views,
        total_favorites=total_favorites,
        total_messages=total_messages,
        top_categories=top_categories,
        top_keywords=top_keywords,
        activity_timeline=activity_timeline,
        price_range=price_range,
        top_brands=top_brands,
        engagement_score=engagement_score
    )


@router.get("/activities", response_model=List[UserActivityResponse])
async def get_user_activities(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    activity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's activity history
    """
    current_user = _resolve_user(current_user, db)
    query = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    )
    
    if activity_type:
        query = query.filter(UserActivity.activity_type == activity_type)
    
    activities = query.order_by(
        desc(UserActivity.created_at)
    ).offset(skip).limit(limit).all()
    
    # Parse keywords from JSON
    result = []
    for activity in activities:
        keywords = None
        if activity.keywords:
            try:
                keywords = json.loads(activity.keywords)
            except json.JSONDecodeError:
                pass
        
        result.append(UserActivityResponse(
            id=activity.id,
            user_id=activity.user_id,
            session_id=activity.session_id,
            activity_type=activity.activity_type,
            listing_id=activity.listing_id,
            search_query=activity.search_query,
            category=activity.category,
            keywords=keywords,
            created_at=activity.created_at,
            duration_seconds=activity.duration_seconds
        ))
    
    return result


@router.get("/interests", response_model=UserInterestResponse)
async def get_user_interests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated user interests
    """
    current_user = _resolve_user(current_user, db)
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id
    ).first()
    
    if not user_interest:
        raise HTTPException(
            status_code=404,
            detail="No interest data available yet. Start browsing to build your profile!"
        )
    
    # Parse JSON fields
    try:
        categories = json.loads(user_interest.categories)
        keywords = json.loads(user_interest.keywords)
        brands = json.loads(user_interest.brands) if user_interest.brands else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing interest data")
    
    return UserInterestResponse(
        id=user_interest.id,
        user_id=user_interest.user_id,
        categories=categories,
        keywords=keywords,
        brands=brands,
        price_range_min=user_interest.price_range_min,
        price_range_max=user_interest.price_range_max,
        last_updated=user_interest.last_updated,
        total_activities=user_interest.total_activities
    )


@router.get("/search-insights", response_model=PopularSearches)
async def get_search_insights(
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get insights about user's search patterns
    """
    current_user = _resolve_user(current_user, db)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get search activities
    searches = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id,
        UserActivity.activity_type == 'search',
        UserActivity.search_query.isnot(None),
        UserActivity.created_at >= start_date
    ).all()
    
    # Aggregate search queries
    search_counts = Counter()
    search_last_time = {}
    categories = []
    all_keywords = []
    
    for search in searches:
        query = search.search_query.lower().strip()
        search_counts[query] += 1
        if query not in search_last_time or search.created_at > search_last_time[query]:
            search_last_time[query] = search.created_at
        
        if search.category:
            categories.append(search.category)
        
        if search.keywords:
            try:
                keywords = json.loads(search.keywords)
                all_keywords.extend(keywords)
            except json.JSONDecodeError:
                pass
    
    # Get top searches
    top_searches = [
        SearchInsight(
            query=query,
            count=count,
            avg_results=None,  # Could be enhanced to track results count
            last_searched=search_last_time[query]
        )
        for query, count in search_counts.most_common(10)
    ]
    
    # Get trending categories and keywords
    trending_categories = [cat for cat, _ in Counter(categories).most_common(5)]
    trending_keywords = [kw for kw, _ in Counter(all_keywords).most_common(10)]
    
    return PopularSearches(
        searches=top_searches,
        trending_categories=trending_categories,
        trending_keywords=trending_keywords
    )


@router.get("/recommendation-performance")
async def get_recommendation_performance(
    days: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance metrics of recommendations
    """
    current_user = _resolve_user(current_user, db)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get recommendation history
    recommendations = db.query(RecommendationHistory).filter(
        RecommendationHistory.user_id == current_user.id,
        RecommendationHistory.shown_at >= start_date
    ).all()
    
    if not recommendations:
        return {
            'total_shown': 0,
            'total_clicked': 0,
            'click_through_rate': 0,
            'by_type': {}
        }
    
    total_shown = len(recommendations)
    total_clicked = sum(1 for r in recommendations if r.clicked)
    click_through_rate = round((total_clicked / total_shown * 100), 2) if total_shown > 0 else 0
    
    # Performance by recommendation type
    by_type = {}
    for rec in recommendations:
        rec_type = rec.recommendation_type
        if rec_type not in by_type:
            by_type[rec_type] = {'shown': 0, 'clicked': 0, 'ctr': 0}
        
        by_type[rec_type]['shown'] += 1
        if rec.clicked:
            by_type[rec_type]['clicked'] += 1
    
    # Calculate CTR for each type
    for rec_type in by_type:
        shown = by_type[rec_type]['shown']
        clicked = by_type[rec_type]['clicked']
        by_type[rec_type]['ctr'] = round((clicked / shown * 100), 2) if shown > 0 else 0
    
    return {
        'total_shown': total_shown,
        'total_clicked': total_clicked,
        'click_through_rate': click_through_rate,
        'by_type': by_type,
        'avg_score': round(sum(r.score for r in recommendations) / len(recommendations), 3)
    }


@router.delete("/clear-history")
async def clear_activity_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear user's activity history and reset interests
    """
    current_user = _resolve_user(current_user, db)
    # Delete activities
    db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).delete()
    
    # Delete interests
    db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id
    ).delete()
    
    # Delete recommendation history
    db.query(RecommendationHistory).filter(
        RecommendationHistory.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    return {"message": "Activity history cleared successfully"}
