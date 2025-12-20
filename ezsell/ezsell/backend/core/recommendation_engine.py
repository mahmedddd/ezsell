"""
Recommendation Engine
Generates personalized recommendations based on user activity and interests
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
from collections import Counter

from models.database import (
    User, Listing, UserActivity, UserInterest, 
    RecommendationHistory, Favorite
)
from core.nlp_service import KeywordExtractor, calculate_keyword_similarity


class RecommendationEngine:
    """Generate personalized recommendations for users"""
    
    def __init__(self, db: Session):
        self.db = db
        self.keyword_extractor = KeywordExtractor()
    
    def track_activity(
        self,
        user_id: Optional[int],
        session_id: str,
        activity_type: str,
        listing_id: Optional[int] = None,
        search_query: Optional[str] = None,
        category: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> UserActivity:
        """Track user activity and extract keywords"""
        
        # Extract keywords from search query or listing
        keywords = []
        if search_query:
            keywords = self.keyword_extractor.extract_keywords(search_query)
        elif listing_id:
            listing = self.db.query(Listing).filter(Listing.id == listing_id).first()
            if listing:
                text = f"{listing.title} {listing.description} {listing.category} {listing.brand or ''}"
                keywords = self.keyword_extractor.extract_keywords(text)
                category = listing.category
        
        # Create activity record
        activity = UserActivity(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            listing_id=listing_id,
            search_query=search_query,
            category=category,
            keywords=json.dumps(keywords) if keywords else None,
            duration_seconds=duration_seconds
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        # Update user interests if user is logged in
        if user_id:
            self._update_user_interests(user_id)
        
        return activity
    
    def _update_user_interests(self, user_id: int):
        """Aggregate and update user interests from activities"""
        
        # Get all user activities
        activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).all()
        
        if not activities:
            return
        
        # Aggregate data
        all_keywords = []
        all_categories = []
        all_brands = []
        prices = []
        
        for activity in activities:
            if activity.keywords:
                try:
                    keywords = json.loads(activity.keywords)
                    all_keywords.extend(keywords)
                except json.JSONDecodeError:
                    pass
            
            if activity.category:
                all_categories.append(activity.category)
            
            if activity.listing_id:
                listing = self.db.query(Listing).filter(Listing.id == activity.listing_id).first()
                if listing:
                    if listing.brand:
                        all_brands.append(listing.brand)
                    if listing.price:
                        prices.append(listing.price)
        
        # Count frequencies
        category_counts = dict(Counter(all_categories))
        keyword_counts = dict(Counter(all_keywords))
        brand_counts = dict(Counter(all_brands))
        
        # Calculate price range
        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None
        
        # Update or create user interests
        user_interest = self.db.query(UserInterest).filter(
            UserInterest.user_id == user_id
        ).first()
        
        if user_interest:
            user_interest.categories = json.dumps(category_counts)
            user_interest.keywords = json.dumps(keyword_counts)
            user_interest.brands = json.dumps(brand_counts) if brand_counts else None
            user_interest.price_range_min = price_min
            user_interest.price_range_max = price_max
            user_interest.total_activities = len(activities)
            user_interest.last_updated = datetime.utcnow()
        else:
            user_interest = UserInterest(
                user_id=user_id,
                categories=json.dumps(category_counts),
                keywords=json.dumps(keyword_counts),
                brands=json.dumps(brand_counts) if brand_counts else None,
                price_range_min=price_min,
                price_range_max=price_max,
                total_activities=len(activities)
            )
            self.db.add(user_interest)
        
        self.db.commit()
    
    def get_personalized_recommendations(
        self,
        user_id: int,
        limit: int = 20,
        exclude_viewed: bool = True
    ) -> List[Tuple[Listing, float, str]]:
        """Get personalized recommendations for user"""
        
        # Get user interests
        user_interest = self.db.query(UserInterest).filter(
            UserInterest.user_id == user_id
        ).first()
        
        if not user_interest:
            return self._get_trending_listings(limit)
        
        try:
            user_categories = json.loads(user_interest.categories)
            user_keywords = json.loads(user_interest.keywords)
        except json.JSONDecodeError:
            return self._get_trending_listings(limit)
        
        # Get listings to exclude
        exclude_ids = set()
        if exclude_viewed:
            viewed = self.db.query(UserActivity.listing_id).filter(
                UserActivity.user_id == user_id,
                UserActivity.listing_id.isnot(None)
            ).distinct().all()
            exclude_ids = {v[0] for v in viewed}
        
        # Get user's own listings to exclude
        own_listings = self.db.query(Listing.id).filter(
            Listing.owner_id == user_id
        ).all()
        exclude_ids.update([l[0] for l in own_listings])
        
        # Query active listings
        query = self.db.query(Listing).filter(
            Listing.is_active == True,
            Listing.is_approved == True
        )
        
        if exclude_ids:
            query = query.filter(Listing.id.notin_(exclude_ids))
        
        all_listings = query.all()
        
        # Score each listing
        scored_listings = []
        for listing in all_listings:
            score = self._calculate_listing_score(
                listing, user_categories, user_keywords, user_interest
            )
            if score > 0.1:  # Minimum relevance threshold
                scored_listings.append((listing, score, "interest_based"))
        
        # Sort by score and return top results
        scored_listings.sort(key=lambda x: x[1], reverse=True)
        
        return scored_listings[:limit]
    
    def _calculate_listing_score(
        self,
        listing: Listing,
        user_categories: Dict[str, int],
        user_keywords: Dict[str, int],
        user_interest: UserInterest
    ) -> float:
        """Calculate relevance score for a listing"""
        
        score = 0.0
        
        # Category match (40% weight)
        if listing.category in user_categories:
            category_freq = user_categories[listing.category]
            total_categories = sum(user_categories.values())
            score += (category_freq / total_categories) * 0.4
        
        # Keyword match (40% weight)
        listing_text = f"{listing.title} {listing.description} {listing.brand or ''}"
        listing_keywords = self.keyword_extractor.extract_keywords(listing_text)
        
        if listing_keywords:
            keyword_matches = sum(
                user_keywords.get(kw, 0) for kw in listing_keywords
            )
            total_keywords = sum(user_keywords.values())
            if total_keywords > 0:
                score += (keyword_matches / total_keywords) * 0.4
        
        # Price range match (10% weight)
        if listing.price and user_interest.price_range_min and user_interest.price_range_max:
            price_range = user_interest.price_range_max - user_interest.price_range_min
            if price_range > 0:
                if user_interest.price_range_min <= listing.price <= user_interest.price_range_max:
                    score += 0.1
                else:
                    # Partial score if close to range
                    distance = min(
                        abs(listing.price - user_interest.price_range_min),
                        abs(listing.price - user_interest.price_range_max)
                    )
                    if distance < price_range:
                        score += 0.05
        
        # Brand match (10% weight)
        if listing.brand and user_interest.brands:
            try:
                user_brands = json.loads(user_interest.brands)
                if listing.brand in user_brands:
                    score += 0.1
            except json.JSONDecodeError:
                pass
        
        # Recency bonus
        days_old = (datetime.utcnow() - listing.created_at).days
        if days_old < 7:
            score *= 1.1  # 10% boost for recent listings
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_similar_listings(
        self,
        listing_id: int,
        limit: int = 10
    ) -> List[Tuple[Listing, float, str]]:
        """Get similar listings based on a specific listing"""
        
        # Get the reference listing
        reference = self.db.query(Listing).filter(Listing.id == listing_id).first()
        if not reference:
            return []
        
        # Extract keywords from reference
        ref_text = f"{reference.title} {reference.description} {reference.brand or ''}"
        ref_keywords = self.keyword_extractor.extract_keywords(ref_text)
        
        # Query similar listings
        similar_listings = self.db.query(Listing).filter(
            Listing.id != listing_id,
            Listing.is_active == True,
            Listing.is_approved == True,
            or_(
                Listing.category == reference.category,
                Listing.brand == reference.brand
            )
        ).all()
        
        # Score each listing
        scored_listings = []
        for listing in similar_listings:
            listing_text = f"{listing.title} {listing.description} {listing.brand or ''}"
            listing_keywords = self.keyword_extractor.extract_keywords(listing_text)
            
            # Calculate similarity
            similarity = calculate_keyword_similarity(ref_keywords, listing_keywords)
            
            # Category match bonus
            if listing.category == reference.category:
                similarity += 0.2
            
            # Brand match bonus
            if listing.brand and listing.brand == reference.brand:
                similarity += 0.15
            
            # Price similarity bonus
            if listing.price and reference.price:
                price_diff = abs(listing.price - reference.price) / reference.price
                if price_diff < 0.3:  # Within 30% price range
                    similarity += 0.15 * (1 - price_diff / 0.3)
            
            if similarity > 0.2:  # Minimum similarity threshold
                scored_listings.append((listing, min(similarity, 1.0), "similar"))
        
        # Sort by similarity
        scored_listings.sort(key=lambda x: x[1], reverse=True)
        
        return scored_listings[:limit]
    
    def _get_trending_listings(self, limit: int = 20) -> List[Tuple[Listing, float, str]]:
        """Get trending listings based on recent activity"""
        
        # Get listings with most activity in last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        trending = self.db.query(
            Listing,
            func.count(UserActivity.id).label('activity_count')
        ).join(
            UserActivity, Listing.id == UserActivity.listing_id
        ).filter(
            Listing.is_active == True,
            Listing.is_approved == True,
            UserActivity.created_at >= week_ago
        ).group_by(
            Listing.id
        ).order_by(
            desc('activity_count')
        ).limit(limit).all()
        
        # Convert to expected format
        max_count = trending[0][1] if trending else 1
        result = [
            (listing, min(count / max_count, 1.0), "trending")
            for listing, count in trending
        ]
        
        # If not enough trending, add recent listings
        if len(result) < limit:
            recent = self.db.query(Listing).filter(
                Listing.is_active == True,
                Listing.is_approved == True
            ).order_by(
                desc(Listing.created_at)
            ).limit(limit - len(result)).all()
            
            result.extend([(l, 0.5, "recent") for l in recent])
        
        return result
    
    def track_recommendation_click(
        self,
        user_id: int,
        listing_id: int,
        recommendation_type: str
    ):
        """Track when a user clicks on a recommendation"""
        
        # Find recent recommendation
        rec = self.db.query(RecommendationHistory).filter(
            RecommendationHistory.user_id == user_id,
            RecommendationHistory.listing_id == listing_id,
            RecommendationHistory.clicked == False
        ).order_by(
            desc(RecommendationHistory.shown_at)
        ).first()
        
        if rec:
            rec.clicked = True
            rec.clicked_at = datetime.utcnow()
            self.db.commit()
    
    def save_recommendations(
        self,
        user_id: int,
        recommendations: List[Tuple[Listing, float, str]]
    ):
        """Save shown recommendations to history"""
        
        for listing, score, rec_type in recommendations:
            rec_history = RecommendationHistory(
                user_id=user_id,
                listing_id=listing.id,
                recommendation_type=rec_type,
                score=score
            )
            self.db.add(rec_history)
        
        self.db.commit()
