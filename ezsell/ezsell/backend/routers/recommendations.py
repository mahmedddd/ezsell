"""
Recommendations Router
Provides personalized recommendations and similar listings
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from models.database import get_db, User, Listing
from core.security import get_current_user, get_current_user_optional
from core.recommendation_engine import RecommendationEngine
from schemas.recommendation_schemas import (
    RecommendationsResponse, RecommendationItem,
    PersonalizedRecommendationsRequest, SimilarListingsRequest,
    UserActivityCreate
)

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.post("/track-activity")
async def track_user_activity(
    activity: UserActivityCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Track user activity for building recommendations
    Supports both logged-in and anonymous users
    """
    engine = RecommendationEngine(db)
    
    # Generate session ID if not provided
    session_id = activity.session_id or str(uuid.uuid4())
    
    tracked_activity = engine.track_activity(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        activity_type=activity.activity_type,
        listing_id=activity.listing_id,
        search_query=activity.search_query,
        category=activity.category,
        duration_seconds=activity.duration_seconds
    )
    
    return {
        "message": "Activity tracked successfully",
        "activity_id": tracked_activity.id,
        "session_id": session_id
    }


@router.get("/personalized", response_model=RecommendationsResponse)
async def get_personalized_recommendations(
    limit: int = Query(default=20, le=100, ge=1),
    exclude_viewed: bool = Query(default=True),
    min_score: float = Query(default=0.1, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations based on user's interests and activity
    """
    engine = RecommendationEngine(db)
    
    # Get recommendations
    recommendations = engine.get_personalized_recommendations(
        user_id=current_user.id,
        limit=limit,
        exclude_viewed=exclude_viewed
    )
    
    # Filter by minimum score
    recommendations = [
        (listing, score, rec_type)
        for listing, score, rec_type in recommendations
        if score >= min_score
    ]
    
    # Save to history
    engine.save_recommendations(current_user.id, recommendations)
    
    # Format response
    recommendation_items = []
    for listing, score, rec_type in recommendations:
        # Generate reason based on recommendation type
        if rec_type == "interest_based":
            reason = f"Based on your interests in {listing.category}"
        elif rec_type == "trending":
            reason = "Trending now"
        elif rec_type == "recent":
            reason = "Recently added"
        else:
            reason = "Recommended for you"
        
        recommendation_items.append(RecommendationItem(
            listing_id=listing.id,
            score=round(score, 3),
            recommendation_type=rec_type,
            reason=reason,
            listing_details={
                'title': listing.title,
                'price': listing.price,
                'category': listing.category,
                'brand': listing.brand,
                'condition': listing.condition,
                'images': listing.images,
                'created_at': listing.created_at.isoformat()
            }
        ))
    
    return RecommendationsResponse(
        recommendations=recommendation_items,
        total=len(recommendation_items),
        generated_at=datetime.utcnow()
    )


@router.post("/similar", response_model=RecommendationsResponse)
async def get_similar_listings(
    request: SimilarListingsRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get listings similar to a specific listing
    Works for both logged-in and anonymous users
    """
    # Verify listing exists
    listing = db.query(Listing).filter(Listing.id == request.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    engine = RecommendationEngine(db)
    
    # Get similar listings
    similar = engine.get_similar_listings(
        listing_id=request.listing_id,
        limit=request.limit
    )
    
    # Format response
    recommendation_items = []
    for similar_listing, score, rec_type in similar:
        # Generate detailed reason
        reasons = []
        if similar_listing.category == listing.category:
            reasons.append(f"same category ({listing.category})")
        if similar_listing.brand and similar_listing.brand == listing.brand:
            reasons.append(f"same brand ({listing.brand})")
        if similar_listing.price and listing.price:
            price_diff = abs(similar_listing.price - listing.price) / listing.price
            if price_diff < 0.2:
                reasons.append("similar price")
        
        reason = "Similar: " + ", ".join(reasons) if reasons else "Similar listing"
        
        recommendation_items.append(RecommendationItem(
            listing_id=similar_listing.id,
            score=round(score, 3),
            recommendation_type="similar",
            reason=reason,
            listing_details={
                'title': similar_listing.title,
                'price': similar_listing.price,
                'category': similar_listing.category,
                'brand': similar_listing.brand,
                'condition': similar_listing.condition,
                'images': similar_listing.images,
                'created_at': similar_listing.created_at.isoformat()
            }
        ))
    
    return RecommendationsResponse(
        recommendations=recommendation_items,
        total=len(recommendation_items),
        generated_at=datetime.utcnow()
    )


@router.get("/trending", response_model=RecommendationsResponse)
async def get_trending_listings(
    limit: int = Query(default=20, le=50, ge=1),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get trending listings based on recent activity
    Public endpoint - no authentication required
    """
    engine = RecommendationEngine(db)
    
    # Get trending listings
    trending = engine._get_trending_listings(limit=limit * 2)  # Get more initially
    
    # Filter by category if specified
    if category:
        trending = [
            (listing, score, rec_type)
            for listing, score, rec_type in trending
            if listing.category == category
        ]
    
    trending = trending[:limit]
    
    # Format response
    recommendation_items = []
    for listing, score, rec_type in trending:
        recommendation_items.append(RecommendationItem(
            listing_id=listing.id,
            score=round(score, 3),
            recommendation_type=rec_type,
            reason="Trending now" if rec_type == "trending" else "Recently added",
            listing_details={
                'title': listing.title,
                'price': listing.price,
                'category': listing.category,
                'brand': listing.brand,
                'condition': listing.condition,
                'images': listing.images,
                'created_at': listing.created_at.isoformat()
            }
        ))
    
    return RecommendationsResponse(
        recommendations=recommendation_items,
        total=len(recommendation_items),
        generated_at=datetime.utcnow()
    )


@router.post("/click/{listing_id}")
async def track_recommendation_click(
    listing_id: int,
    recommendation_type: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track when user clicks on a recommended listing
    Used to improve recommendation accuracy
    """
    # Verify listing exists
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    engine = RecommendationEngine(db)
    engine.track_recommendation_click(
        user_id=current_user.id,
        listing_id=listing_id,
        recommendation_type=recommendation_type
    )
    
    return {"message": "Click tracked successfully"}


@router.get("/categories")
async def get_recommended_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommended categories based on user interests
    """
    from models.database import UserInterest
    import json
    
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id
    ).first()
    
    if not user_interest:
        # Return popular categories if no user data
        return {
            "recommended_categories": ["Electronics", "Furniture", "Vehicles"],
            "based_on": "popular"
        }
    
    try:
        categories = json.loads(user_interest.categories)
        # Sort by frequency
        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "recommended_categories": [cat for cat, _ in sorted_categories[:5]],
            "based_on": "your_interests"
        }
    except json.JSONDecodeError:
        return {
            "recommended_categories": ["Electronics", "Furniture", "Vehicles"],
            "based_on": "popular"
        }


@router.get("/for-you")
async def get_for_you_feed(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get a mixed feed of personalized and trending content
    Works for both logged-in and anonymous users
    """
    engine = RecommendationEngine(db)
    
    if current_user:
        # Mix personalized and trending for logged-in users
        personalized = engine.get_personalized_recommendations(
            user_id=current_user.id,
            limit=int(limit * 0.7)  # 70% personalized
        )
        trending = engine._get_trending_listings(limit=int(limit * 0.3))  # 30% trending
        
        # Combine and deduplicate
        seen_ids = set()
        combined = []
        
        for listing, score, rec_type in personalized + trending:
            if listing.id not in seen_ids:
                combined.append((listing, score, rec_type))
                seen_ids.add(listing.id)
        
        recommendations = combined[skip:skip + limit]
    else:
        # Show trending for anonymous users
        trending = engine._get_trending_listings(limit=limit + skip)
        recommendations = trending[skip:skip + limit]
    
    # Format response
    items = []
    for listing, score, rec_type in recommendations:
        items.append({
            'listing_id': listing.id,
            'title': listing.title,
            'price': listing.price,
            'category': listing.category,
            'brand': listing.brand,
            'condition': listing.condition,
            'images': listing.images,
            'score': round(score, 3),
            'recommendation_type': rec_type,
            'created_at': listing.created_at.isoformat()
        })
    
    return {
        'items': items,
        'total': len(items),
        'skip': skip,
        'limit': limit
    }
