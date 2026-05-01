import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, cast, String, or_
from pydantic import BaseModel

from models.database import User, Listing, UserActivity, UserInterest, RecommendationHistory
from core.nlp_service import KeywordExtractor, calculate_keyword_similarity
from core.semantic_ai import SemanticEmbeddingService

class RecommendationEngine:
    """Generate personalized recommendations using Semantic AI and keyword fallbacks"""

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
        """Track user activity and extract semantic embeddings"""
        
        keywords = []
        embedding = None
        
        if search_query:
            keywords = self.keyword_extractor.extract_keywords(search_query)
            embedding = SemanticEmbeddingService.generate_embedding(search_query)
        elif listing_id:
            listing = self.db.query(Listing).filter(Listing.id == listing_id).first()
            if listing:
                text_to_embed = SemanticEmbeddingService.construct_listing_text(
                    listing.title, listing.description, listing.category, listing.brand
                )
                keywords = self.keyword_extractor.extract_keywords(text_to_embed)
                embedding = SemanticEmbeddingService.generate_embedding(text_to_embed)
                
                # Overwrite listing's semantic_embedding if it's missing (lazy backfill)
                if not getattr(listing, 'semantic_embedding', None) and embedding:
                    try:
                        listing.semantic_embedding = json.dumps(embedding)
                        self.db.add(listing)
                    except Exception as e:
                        pass
                
                category = listing.category
        
        activity = UserActivity(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            listing_id=listing_id,
            search_query=search_query,
            category=category,
            keywords=json.dumps(keywords) if keywords else None,
            semantic_embedding=json.dumps(embedding) if embedding else None,
            duration_seconds=duration_seconds
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        if user_id:
            self._update_user_interests(user_id)
        
        return activity

    def _update_user_interests(self, user_id: int):
        """Aggregate and update user interests from activities"""
        
        activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).all()
        
        if not activities:
            return
            
        all_keywords = []
        all_categories = []
        all_brands = []
        prices = []
        embeddings = []
        
        # Activity weights
        WEIGHTS = {
            'view': 1.0,
            'search': 2.0,
            'favorite': 3.0,
            'message': 5.0,
            'click': 1.5
        }
        
        # Time decay factor: 50% decay every 7 days
        DECAY_HALF_LIFE_DAYS = 7
        now = datetime.utcnow()
        
        for activity in activities:
            # Calculate time decay
            days_ago = (now - activity.created_at).days
            decay = 0.5 ** (days_ago / DECAY_HALF_LIFE_DAYS)
            
            # Get weight for activity type
            weight = WEIGHTS.get(activity.activity_type, 1.0) * decay
            
            if getattr(activity, 'keywords', None):
                try:
                    kws = json.loads(activity.keywords)
                    for kw in kws:
                        all_keywords.append((kw, weight))
                except json.JSONDecodeError:
                    pass
                    
            if getattr(activity, 'semantic_embedding', None):
                try:
                    # Embedding itself isn't weighted but its presence is noted
                    embeddings.append(json.loads(activity.semantic_embedding))
                except json.JSONDecodeError:
                    pass
            
            if activity.category:
                all_categories.append((activity.category, weight))
            
            if activity.listing_id:
                listing = self.db.query(Listing).filter(Listing.id == activity.listing_id).first()
                if listing:
                    if listing.brand:
                        all_brands.append((listing.brand, weight))
                    if listing.price:
                        prices.append(listing.price)
        
        # Calculate avergage embedding for user profile
        avg_embedding = None
        if embeddings:
            import numpy as np
            try:
                avg_embedding = np.mean(embeddings, axis=0).tolist()
            except Exception:
                pass

        # Aggregate weighted counts
        category_counts = {}
        for cat, w in all_categories:
            category_counts[cat] = category_counts.get(cat, 0.0) + w
            
        keyword_counts = {}
        for kw, w in all_keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0.0) + w
            
        brand_counts = {}
        for br, w in all_brands:
            brand_counts[br] = brand_counts.get(br, 0.0) + w
        
        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None
        
        user_interest = self.db.query(UserInterest).filter(
            UserInterest.user_id == user_id
        ).first()
        
        if user_interest:
            user_interest.categories = json.dumps(category_counts)
            user_interest.keywords = json.dumps(keyword_counts)
            user_interest.brands = json.dumps(brand_counts) if brand_counts else None
            if avg_embedding:
                user_interest.semantic_embedding = json.dumps(avg_embedding)
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
                semantic_embedding=json.dumps(avg_embedding) if avg_embedding else None,
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
        """Get personalized recommendations for user using Semantic AI similarity"""
        
        user_interest = self.db.query(UserInterest).filter(
            UserInterest.user_id == user_id
        ).first()
        
        if not user_interest:
            return self._get_trending_listings(limit)
            
        try:
            user_categories = json.loads(user_interest.categories) if getattr(user_interest, 'categories', None) else {}
            user_keywords = json.loads(user_interest.keywords) if getattr(user_interest, 'keywords', None) else {}
            user_embedding = json.loads(user_interest.semantic_embedding) if getattr(user_interest, 'semantic_embedding', None) else None
        except Exception:
            return self._get_trending_listings(limit)
            
        # Get listings to exclude
        exclude_ids = set()
        if exclude_viewed:
            viewed = self.db.query(UserActivity.listing_id).filter(
                UserActivity.user_id == user_id,
                UserActivity.listing_id.isnot(None)
            ).distinct().all()
            exclude_ids = {v[0] for v in viewed}
            
        own_listings = self.db.query(Listing.id).filter(
            Listing.owner_id == user_id
        ).all()
        exclude_ids.update([l[0] for l in own_listings])
        
        query = self.db.query(Listing).filter(
            Listing.is_active == True,
            Listing.approval_status == "approved",
            Listing.is_sold == False
        )
        if exclude_ids:
            query = query.filter(Listing.id.notin_(exclude_ids))
            
        all_listings = query.all()
        scored_listings = []
        
        for listing in all_listings:
            score = self._calculate_hybrid_score(
                listing, user_categories, user_keywords, user_embedding, user_interest
            )
            if score > 0.05: # Lowered threshold slightly for more diversity
                scored_listings.append((listing, score, "interest_based"))
                
        # Sort by score primarily, then by created_at for recency-based tie-breaking
        scored_listings.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
        return scored_listings[:limit]

    def _calculate_hybrid_score(
        self,
        listing: Listing,
        user_categories: Dict[str, int],
        user_keywords: Dict[str, int],
        user_embedding: Optional[List[float]],
        user_interest: UserInterest
    ) -> float:
        """Calculate score using both precise semantic similarity and behavioral fallbacks"""
        score = 0.0
        
        # 1. AI Semantic Similarity (60% Weight if embeddings exist)
        has_semantic_score = False
        listing_embedding_str = getattr(listing, 'semantic_embedding', None)
        
        if user_embedding and listing_embedding_str:
            try:
                listing_emb = json.loads(listing_embedding_str)
                sim_score = SemanticEmbeddingService.calculate_similarity(user_embedding, listing_emb)
                score += sim_score * 0.60
                has_semantic_score = True
            except Exception:
                pass
                
        # Fallback to old keyword method if model hasn't embedded the item yet
        if not has_semantic_score:
            listing_text = SemanticEmbeddingService.construct_listing_text(
                listing.title, listing.description, listing.category, listing.brand
            )
            listing_keywords = self.keyword_extractor.extract_keywords(listing_text)
            if listing_keywords:
                keyword_matches = sum(user_keywords.get(kw, 0) for kw in listing_keywords)
                total_keywords = sum(user_keywords.values())
                if total_keywords > 0:
                    score += (keyword_matches / total_keywords) * 0.60

        # 2. Category match (40% weight - PRIMARY SIGNAL)
        if listing.category in user_categories:
            category_freq = user_categories[listing.category]
            total_categories = sum(user_categories.values())
            if total_categories > 0:
                # Calculate category dominance
                category_ratio = category_freq / total_categories
                score += category_ratio * 0.40
                
                # Check if this is the user's TOP category for an extra "affinity boost"
                top_category = max(user_categories, key=user_categories.get) if user_categories else None
                if listing.category == top_category:
                    score += 0.15 # Top affinity boost

        # 3. Price range match (10% weight)
        if listing.price and user_interest.price_range_min and user_interest.price_range_max:
            price_range = user_interest.price_range_max - user_interest.price_range_min
            if price_range > 0:
                if user_interest.price_range_min <= listing.price <= user_interest.price_range_max:
                    score += 0.10
                else:
                    distance = min(
                        abs(listing.price - user_interest.price_range_min),
                        abs(listing.price - user_interest.price_range_max)
                    )
                    if distance < price_range:
                        score += 0.05

        # 4. Brand & Recency (10% context hooks)
        if listing.brand and getattr(user_interest, 'brands', None):
            try:
                user_brands = json.loads(user_interest.brands)
                if listing.brand in user_brands:
                    score += 0.10
            except Exception:
                pass
                
        # 5. Hybrid "Hotness" Score (Recency Boost)
        # 0.3 weight for recency vs 0.7 for relevance (already partly in score)
        days_old = (datetime.utcnow() - listing.created_at).days
        recency_bonus = 0.0
        if days_old < 1:
            recency_bonus = 0.3
        elif days_old < 3:
            recency_bonus = 0.2
        elif days_old < 7:
            recency_bonus = 0.1
            
        # Blend relevance (score) and recency
        # Increased weight for relevance (0.85) vs recency (0.15) to ensure categories dominate
        final_score = (score * 0.85) + (recency_bonus * 0.5)
        
        return min(final_score, 1.0)

    def get_similar_listings(
        self,
        listing_id: int,
        limit: int = 10
    ) -> List[Tuple[Listing, float, str]]:
        """Get highly similar listings using deep semantic vector search"""
        reference = self.db.query(Listing).filter(Listing.id == listing_id).first()
        if not reference:
            return []
            
        ref_text = SemanticEmbeddingService.construct_listing_text(
            reference.title, reference.description, reference.category, reference.brand
        )
        ref_embedding = None
        
        # Try to use pre-calculated embedding, otherwise generate on the fly
        if getattr(reference, 'semantic_embedding', None):
            try:
                ref_embedding = json.loads(reference.semantic_embedding)
            except Exception:
                 ref_embedding = SemanticEmbeddingService.generate_embedding(ref_text)
        else:
             ref_embedding = SemanticEmbeddingService.generate_embedding(ref_text)
             
        ref_keywords = self.keyword_extractor.extract_keywords(ref_text)
        
        similar_listings = self.db.query(Listing).filter(
            Listing.id != listing_id,
            Listing.is_active == True,
            Listing.approval_status == "approved",
            Listing.is_sold == False,
            or_(
                Listing.category == reference.category,
                Listing.brand == reference.brand
            )
        ).all()
        
        scored_listings = []
        for listing in similar_listings:
            similarity = 0.0
            
            # Use deep vector AI similarity if possible
            if ref_embedding:
                listing_emb = None
                if getattr(listing, 'semantic_embedding', None):
                    try: listing_emb = json.loads(listing.semantic_embedding)
                    except Exception: pass
                
                if not listing_emb:
                    l_text = SemanticEmbeddingService.construct_listing_text(
                        listing.title, listing.description, listing.category, listing.brand
                    )
                    listing_emb = SemanticEmbeddingService.generate_embedding(l_text)
                    
                if listing_emb:
                    similarity = SemanticEmbeddingService.calculate_similarity(ref_embedding, listing_emb)
            
            # Fallback to pure NLP Keyword mapping if ML fails or is unavailable
            if similarity == 0.0:
                 l_text = SemanticEmbeddingService.construct_listing_text(
                     listing.title, listing.description, listing.category, listing.brand
                 )
                 listing_keywords = self.keyword_extractor.extract_keywords(l_text)
                 similarity = calculate_keyword_similarity(ref_keywords, listing_keywords)
                 
            # Add hard context boosts
            if listing.category == reference.category: similarity += 0.2
            if listing.brand and listing.brand == reference.brand: similarity += 0.15
            if listing.price and reference.price:
                price_diff = abs(listing.price - reference.price) / reference.price
                if price_diff < 0.3:
                    similarity += 0.15 * (1 - price_diff / 0.3)
                    
            if similarity > 0.2:
                scored_listings.append((listing, min(similarity, 1.0), "similar"))
                
        scored_listings.sort(key=lambda x: x[1], reverse=True)
        return scored_listings[:limit]

    def _get_trending_listings(self, limit: int = 20) -> List[Tuple[Listing, float, str]]:
        """Get trending listings based on recent activity"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        trending = self.db.query(
            Listing,
            func.count(UserActivity.id).label('activity_count')
        ).join(
            UserActivity, Listing.id == UserActivity.listing_id
        ).filter(
            Listing.is_active == True,
            Listing.approval_status == "approved",
            Listing.is_sold == False,
            UserActivity.created_at >= week_ago
        ).group_by(
            Listing.id
        ).order_by(
            desc('activity_count')
        ).limit(limit).all()
        
        max_count = trending[0][1] if trending else 1
        result = [
            (listing, min(count / max_count, 1.0), "trending")
            for listing, count in trending
        ]
        
        if len(result) < limit:
            trending_ids = [l.id for l, _, _ in result]
            recent_query = self.db.query(Listing).filter(
                Listing.is_active == True,
                Listing.approval_status == "approved",
                Listing.is_sold == False
            )
            if trending_ids:
                recent_query = recent_query.filter(Listing.id.notin_(trending_ids))
            
            recent = recent_query.order_by(
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

