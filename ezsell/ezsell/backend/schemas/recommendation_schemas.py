"""
Schemas for recommendation and analytics system
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Activity Tracking Schemas
class UserActivityCreate(BaseModel):
    activity_type: str = Field(..., description="Type of activity: search, view, click, favorite, message")
    listing_id: Optional[int] = None
    search_query: Optional[str] = None
    category: Optional[str] = None
    duration_seconds: Optional[int] = None
    session_id: Optional[str] = None

class UserActivityResponse(BaseModel):
    id: int
    user_id: Optional[int]
    session_id: str
    activity_type: str
    listing_id: Optional[int]
    search_query: Optional[str]
    category: Optional[str]
    keywords: Optional[List[str]]
    created_at: datetime
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True

# User Interest Schemas
class UserInterestResponse(BaseModel):
    id: int
    user_id: int
    categories: Dict[str, int]
    keywords: Dict[str, int]
    brands: Optional[Dict[str, int]]
    price_range_min: Optional[float]
    price_range_max: Optional[float]
    last_updated: datetime
    total_activities: int

    class Config:
        from_attributes = True

# Analytics Schemas
class CategoryInsight(BaseModel):
    category: str
    count: int
    percentage: float

class KeywordInsight(BaseModel):
    keyword: str
    frequency: int
    relevance_score: float

class ActivityTimeline(BaseModel):
    date: str
    search_count: int
    view_count: int
    click_count: int
    favorite_count: int

class UserDashboard(BaseModel):
    total_searches: int
    total_views: int
    total_favorites: int
    total_messages: int
    top_categories: List[CategoryInsight]
    top_keywords: List[KeywordInsight]
    activity_timeline: List[ActivityTimeline]
    price_range: Dict[str, Optional[float]]
    top_brands: List[Dict[str, Any]]
    engagement_score: float

# Recommendation Schemas
class RecommendationItem(BaseModel):
    listing_id: int
    score: float
    recommendation_type: str
    reason: str
    listing_details: Optional[Dict[str, Any]] = None

class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem]
    total: int
    generated_at: datetime

class SimilarListingsRequest(BaseModel):
    listing_id: int
    limit: int = Field(default=10, le=50)

class PersonalizedRecommendationsRequest(BaseModel):
    limit: int = Field(default=20, le=100)
    exclude_viewed: bool = True
    min_score: float = Field(default=0.3, ge=0.0, le=1.0)

# Search Analytics
class SearchInsight(BaseModel):
    query: str
    count: int
    avg_results: Optional[int]
    last_searched: datetime

class PopularSearches(BaseModel):
    searches: List[SearchInsight]
    trending_categories: List[str]
    trending_keywords: List[str]
