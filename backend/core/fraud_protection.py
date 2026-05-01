import hashlib
import json
import re
from typing import List, Optional, Tuple, Dict
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    HAS_AI = True
except ImportError:
    HAS_AI = False
from PIL import Image
from sqlalchemy.orm import Session
from models.database import Listing, User

class FraudProtectionService:
    """
    Advanced Fraud Protection for EZSell.
    Enforces:
    - Email verification for posting
    - Duplicate ad detection (content hashing)
    - Image-Category mismatch detection (CLIP AI)
    - Price anomaly detection (relative to predicted price)
    - Scam keyword filtering
    """
    
    _clip_model = None
    _clip_processor = None
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu") if HAS_AI else "cpu"
    
    # Map internal categories to valid descriptors for CLIP comparison
    # If the AI's best guess contains any of these, it's a match
    VALID_DESCRIPTORS = {
        "mobile": ["phone", "smartphone", "cellular", "telephone", "tablet", "ipad", "iphone", "samsung", "android"],
        "laptop": ["laptop", "notebook", "macbook", "chromebook", "computer"],
        "furniture": ["furniture", "chair", "sofa", "couch", "table", "bed", "wardrobe", "desk", "cabinet", "bookshelf", "mirror", "drawer", "closet"]
    }

    # All labels used for search. This allows identifying "Mismatch: a car" correctly.
    GLOBAL_IDENTIFY_LABELS = [
        # Mobile
        "a mobile phone", "a smartphone", "a cellular phone", "a telephone", "a tablet", "an iPad", "an iPhone",
        # Laptops
        "a laptop computer", "a notebook computer", "a macbook", "a chromebook",
        # Furniture
        "a bed", "a sofa", "a couch", "a dining table", "a coffee table", "a chair", "an armchair", "a wardrobe", "a closet", "a desk", "a cabinet", "a bookshelf", "a mirror",
        # Vehicles (Common mismatches)
        "a car", "a motorcycle", "a bike", "a truck", "a bicycle",
        # Appliances
        "a refrigerator", "a washing machine", "a microwave", "an oven", "a television", "a monitor", "an air conditioner",
        # Fashion & Jewelry
        "clothing", "a shoe", "a watch", "a handbag", "jewelry", "a ring", "a necklace",
        # Other / Noise
        "a person", "an animal", "a cat", "a dog", "a plant", "food", "text only", "a screenshot", "a landscape", "a building", "a box", "empty space"
    ]
    
    SCAM_KEYWORDS = [
        r"advance\s*payment", r"pay\s*first", r"gift\s*card",
        r"whatsapp\s*only", r"contact\s*on\s*whatsapp",
        r"bank\s*transfer\s*first", r"courier\s*charges\s*needed"
    ]

    @classmethod
    def load_clip(cls):
        """Lazy load CLIP model for image validation"""
        if not HAS_AI:
            return None, None
            
        if cls._clip_model is None:
            print(f"Loading CLIP model for fraud prevention on {cls._device}...")
            model_id = "openai/clip-vit-base-patch32"
            cls._clip_processor = CLIPProcessor.from_pretrained(model_id)
            cls._clip_model = CLIPModel.from_pretrained(model_id).to(cls._device)
            cls._clip_model.eval() # Set to evaluation mode
        return cls._clip_model, cls._clip_processor

    @staticmethod
    def check_email_verified(user: User) -> bool:
        """Verify if the user is verified to post ads"""
        return user.is_verified is True

    @staticmethod
    def generate_listing_hash(title: str, description: str, price: float) -> str:
        """
        Generate a unique hash for a listing (Global - ignore owner).
        Normalizes whitespace, case, and rounds price to handle minor tweaks.
        """
        clean_title = " ".join(title.lower().split())
        clean_desc = " ".join(description.lower().split())
        # Round price to nearest 100 to catch minor price spam
        rounded_price = round(price / 100) * 100
        payload = f"{clean_title}|{clean_desc}|{rounded_price}"
        return hashlib.md5(payload.encode()).hexdigest()

    @staticmethod
    def calculate_image_hash(image_path: str) -> Optional[str]:
        """
        Calculate a perceptual hash (dHash) for an image.
        dHash is resistant to resizing and minor quality changes.
        """
        try:
            img = Image.open(image_path).convert("L") # Grayscale
            img = img.resize((9, 8), Image.Resampling.LANCZOS)
            
            pixels = list(img.getdata())
            diff = []
            for row in range(8):
                for col in range(8):
                    pixel_left = pixels[row * 9 + col]
                    pixel_right = pixels[row * 9 + col + 1]
                    diff.append(pixel_left > pixel_right)
            
            # Convert boolean array to hex string
            decimal_value = 0
            for bit in diff:
                decimal_value = (decimal_value << 1) | int(bit)
            
            return hex(decimal_value)[2:].zfill(16)
        except Exception as e:
            print(f"Image hashing error: {e}")
            return None

    @staticmethod
    def is_duplicate(db: Session, listing_hash: str, image_hashes: List[str] = None) -> Optional[Listing]:
        """
        Check if this listing (content or image) already exists GLOBALLY.
        Returns the matching listing if found.
        """
        # 1. Check Content Hash
        match = db.query(Listing).filter(
            Listing.listing_hash == listing_hash,
            Listing.is_active == True,
            Listing.is_sold == False
        ).first()
        
        if match:
            return match
            
        # 2. Check ANY of the Image Hashes (if provided)
        if image_hashes:
            for img_h in image_hashes:
                if not img_h: continue
                match = db.query(Listing).filter(
                    Listing.image_hash == img_h,
                    Listing.is_active == True,
                    Listing.is_sold == False
                ).first()
                if match:
                    return match
            
        return None

    @staticmethod
    def is_nonsense(text: str) -> Tuple[bool, str]:
        """
        Comprehensive gibberish/nonsense detection for descriptions.
        Uses heuristics like Shannon Entropy, character diversity, and unpronounceable patterns.
        Returns: (is_nonsense, reason)
        """
        if not text or len(text.strip()) < 5:
            return False, "ok"
            
        text_lower = text.lower()
        # Remove whitespace for global repetition check
        stripped_text = "".join(text_lower.split())
        
        # 1. Repeated Character Sequences (e.g. "!!!!!!" or "aaaaa")
        import itertools
        for char, group in itertools.groupby(text_lower if len(text) < 20 else stripped_text):
            if len(list(group)) > 5:
                return True, f"excessive_repetition_of_{char}"

        words = text_lower.split()
        if not words: return False, "ok"
        
        # 1. Long string detection (e.g. the user's example)
        for word in words:
            if len(word) > 25:
                return True, "excessively_long_word"
        
        # 2. Shannon Entropy (Randomness Check)
        import math
        def calculate_entropy(data):
            if not data: return 0
            entropy = 0
            for x in set(data):
                p_x = data.count(x) / len(data)
                entropy += - p_x * math.log2(p_x)
            return entropy

        entropy = calculate_entropy(text_lower)
        # Highly random strings (gibberish keys) or zero-diversity strings (aaaaa)
        if entropy > 4.5 and len(text) > 40:
            return True, f"high_entropy_detected_{entropy:.2f}"
        if entropy < 1.5 and len(text) > 20:
            return True, "low_diversity_repetitive"

        # 3. Consonant-to-Vowel Ratio (Phonetic Check)
        vowels = set("aeiou")
        consonants = set("bcdfghjklmnpqrstvwxyz")
        
        # Furniture-specific bypass: If common furniture words are found, be more lenient
        furniture_keywords = {"bed", "sofa", "chair", "table", "wood", "size", "queen", "king", "double", "new"}
        has_keywords = any(kw in text_lower for kw in furniture_keywords)
        
        for word in words:
            # Skip very short words or those containing numbers/symbols
            if len(word) <= 5 or not word.isalpha():
                continue
                
            v_count = sum(1 for c in word if c in vowels)
            c_count = sum(1 for c in word if c in consonants)
            
            # Blatant button mash (e.g. "vnlknvlkfv")
            if v_count == 0 and c_count > 6:
                return True, f"unpronounceable_word_{word}"
            
            # Vowel distribution check - relaxed if keywords are present
            ratio_threshold = 0.10 if has_keywords else 0.15
            if c_count > 0 and (v_count / (v_count + c_count)) < ratio_threshold and len(word) > 15:
                # Still check for repeating patterns
                return True, "unusual_vowel_distribution"

        # 4. Global character diversity
        if len(set(stripped_text)) < 4 and len(stripped_text) > 15:
            return True, "too_few_unique_characters"

        return False, "ok"

    @classmethod
    async def validate_image_category(cls, image_path: str, expected_category: str) -> Tuple[bool, float, str]:
        """
        Use CLIP to verify if the image content matches the selected category.
        Returns: (is_match, confidence, best_label)
        """
        if not HAS_AI:
            return True, 1.0, "ai_disabled_on_server"

        try:
            model, processor = cls.load_clip()
            if not model or not processor:
                return True, 1.0, "ai_load_failed"
                
            from PIL import Image
            image = Image.open(image_path).convert("RGB")
            
            # Optimization: Resize for faster inference
            if image.width > 512 or image.height > 512:
                image.thumbnail((512, 512))
            
            # Perform global search across all labels
            labels = cls.GLOBAL_IDENTIFY_LABELS
            
            with torch.no_grad():
                inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
                inputs = {k: v.to(cls._device) for k, v in inputs.items()}
                outputs = model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)[0]
            
            # Find the best match
            max_idx = probs.argmax().item()
            best_label = labels[max_idx]
            confidence = float(probs[max_idx])
            
            # Verification Logic:
            best_label_lower = best_label.lower()
            
            # 1. HARD REJECTION: If the AI identifies a person, text, or noise as the TOP match
            # we never want humans or screenshots verified as marketplace items.
            blacklist_terms = ["person", "animal", "text only", "screenshot", "empty space", "cat", "dog", "food"]
            for term in blacklist_terms:
                if term in best_label_lower:
                    return False, confidence, best_label

            # 2. Category Verification:
            # Does the best label match the expected category?
            is_match = False
            valid_words = cls.VALID_DESCRIPTORS.get(expected_category, [])
            
            for word in valid_words:
                if word in best_label_lower:
                    is_match = True
                    break
            
            # 3. Special Case: Mirror Selfies
            # Mirrors match "furniture", but if there's a strong chance of a "person", reject it.
            if "mirror" in best_label_lower and is_match:
                # Check if "a person" was the second choice or very close
                person_idx = -1
                for idx, lbl in enumerate(labels):
                    if "person" in lbl:
                        person_idx = idx
                        break
                
                if person_idx != -1:
                    person_prob = float(probs[person_idx])
                    # If person probability is significant (e.g., > 15%), it's likely a selfie
                    if person_prob > 0.15:
                        return False, confidence, "mirror selfie (person detected)"
            
            # Threshold Check: If confidence is very low, treat as mismatch
            if confidence < 0.25:
                is_match = False

            return is_match, confidence, best_label
            
        except Exception as e:
            print(f"CLIP validation error: {e}")
            return True, 0.0, "error"

    @staticmethod
    def check_price_anomaly(price: float, predicted_price: Optional[float]) -> Tuple[bool, str]:
        """Flag ads that are suspiciously cheap (scam risk)"""
        if not predicted_price or predicted_price <= 0:
            return False, "no_prediction"
        
        # If price is less than 40% of the predicted (market) value, it's an anomaly
        if price < (predicted_price * 0.4):
            return True, "suspiciously_low"
        
        # If price is more than 3x the predicted value
        if price > (predicted_price * 3.0):
            return True, "suspiciously_high"
            
        return False, "normal"

    @classmethod
    def scan_for_scam_keywords(cls, text: str) -> List[str]:
        """Check for known scam phrases in title/description"""
        found = []
        text_lower = text.lower()
        for pattern in cls.SCAM_KEYWORDS:
            if re.search(pattern, text_lower):
                found.append(pattern)
        return found
