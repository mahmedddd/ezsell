import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

class LLMPricingService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("WARNING: GROQ_API_KEY not found in environment. LLM features will be disabled.")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = "llama-3.3-70b-versatile"

    async def validate_listing_content(self, category: str, title: str, description: str) -> Dict[str, Any]:
        """
        Validates the title and extracts specs using the LLM.
        """
        if not self.client:
            return {"is_valid": True, "message": "LLM validation unavailable", "missing_fields": [], "suggested_title": title, "extracted_specs": {}}

        prompt = f"""You are a listing moderator for OLX Pakistan — a used goods marketplace covering mobiles, laptops, and furniture.
Your job: decide if the listing title is specific enough to identify a real product. You are NOT a spec validator.

Category: {category}
Title: "{title}"
Description: "{description}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE PRINCIPLE — Think like a human moderator:
Ask yourself: "Can a buyer look at this title and know exactly WHAT product is being sold?"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1 — MOBILES:
✅ VALID if title contains: a brand name + ANY model identifier (number, name, letter, variant, generation).
   - "iPhone 6s", "iPhone 7", "iPhone 7 Plus", "iPhone 12 Pro Max" → all VALID
   - "Samsung Galaxy S22", "Samsung Galaxy S22 256GB" → both VALID
   - "Redmi Note 13", "Redmi 14", "Redmi 14 Pro" → all VALID  
   - "Tecno Spark 20 Pro", "Infinix Hot 40", "QMobile Noir S8" → all VALID
   - Any brand + any model number/name = VALID
❌ INVALID: "iPhone" alone, "Samsung" alone, "Phone", "Mobile", "Smartphone", "Used Phone"
   — Reject ONLY if there is literally ZERO model information alongside the brand.
   — Specs like RAM/storage/color are NEVER required. "Samsung Galaxy S22" is fully valid even without "256GB".

RULE 2 — LAPTOPS:
✅ VALID if title contains: a brand + any model/series/processor hint.
   - "Dell Inspiron 15", "HP ProBook 450", "Lenovo ThinkPad", "MacBook Air", "MacBook Air M1"
   - "Asus TUF A15", "Acer Aspire i5", "Dell Latitude i7 12th Gen" → all VALID
   - A series name alone (e.g. "Lenovo ThinkPad") is VALID — model number not required.
❌ INVALID: "Dell", "HP", "Laptop", "Gaming Laptop", "Used Laptop" — brand-only or category-only.

RULE 3 — FURNITURE:
✅ VALID if title names any specific furniture piece or type (brand optional).
   - "King Size Bed", "L-Shape Sofa", "5 Seater Sofa", "Chinioti Wardrobe", "Office Chair" → all VALID
   - "Wooden Dining Table", "6 Seater Dining Set", "Steel Almirah" → all VALID
   - Size descriptors (King/Queen/Double/Single, 5-Seater, L-Shape etc.) make generic types VALID.
❌ INVALID: Just "Furniture", "Item", "Sofa" alone with no further descriptor, "Chair" alone.
   — However "Office Chair", "Dining Chair", "Gaming Chair" ARE valid (type qualifier present).

CRITICAL OVERRIDES (apply to ALL categories):
- IF VALID but incomplete → set is_valid=true, put improvement hints in missing_fields ONLY.
- NEVER fail a title for lacking specs (RAM, storage, color, size). Those come from spec dropdowns.
- NEVER fail a title just because a model isn't in your training data — if it looks like a real product name, accept it.
- Only reject truly unidentifiable titles: brand-only, category-word-only, or gibberish.

Return EXCLUSIVELY this JSON (no extra text):
{{
  "is_valid": boolean,
  "message": "Title looks good!" or brief guidance like "Please add a model name, e.g. iPhone 14 Pro",
  "missing_fields": ["Storage", "RAM"] (informational hints only — never reject based on these),
  "suggested_title": "same as input if valid, or improved version if vague",
  "extracted_specs": {{}} (any specs you can extract from title/description)
}}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(chat_completion.choices[0].message.content)
            return result
        except Exception as e:
            import traceback
            error_str = str(e)
            masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if self.api_key else "NONE"
            print(f"LLM Title Validation Error: {error_str}")
            print(f"Context: Model={self.model}, Key={masked_key}")
            print("FULL TRACEBACK:")
            traceback.print_exc()
            with open("validation_traceback.txt", "w") as f:
                f.write(f"--- ERROR AT {os.getenv('COMPUTERNAME')} ---\n")
                f.write(f"Model: {self.model}\n")
                f.write(f"Key: {masked_key}\n")
                f.write(traceback.format_exc())
            # When rate-limited or error occurs, allow the title through so users aren't blocked
            return {"is_valid": True, "message": "Validation temporarily unavailable, proceeding.", "missing_fields": [], "suggested_title": title, "extracted_specs": {}}


    async def generate_relevant_dropdowns(self, category: str, title: str) -> Dict[str, List[str]]:
        """
        Generates contextual dropdown options based on what the user is typing.
        """
        if not self.client or len(title.strip()) < 3:
            return {}

        # For furniture, detect the type from the title to give targeted guidance
        furniture_type_hint = ""
        t_lower = title.lower()
        if any(w in t_lower for w in ["sofa", "couch", "settee", "l-shape", "l shape", "sectional"]):
            furniture_type_hint = (
                "This is a SOFA. You MUST include: 'Seating Capacity', 'Material', 'Style', 'Upholstery Type'.\n"
                "- Seating Capacity: '1 Seater', '2 Seater', '3 Seater', '4 Seater', '5 Seater', '6 Seater', '7 Seater'.\n"
                "- Material: 'Velvet', 'Fabric', 'Leather', 'Rexine', 'Suede', 'Cotton Blend'.\n"
                "- Style: 'Modern', 'Traditional', 'Chinioti', 'L-Shape', 'Corner', 'Reclinable', 'Sofa Cum Bed'.\n"
                "- Upholstery Type: 'Foam Cushion', 'Spring Cushion', 'High-Density Foam', 'Memory Foam', 'Fiber Fill'.\n"
                "Also add 'Frame Material': 'Solid Wood', 'MDF', 'Metal Frame'."
            )
        elif any(w in t_lower for w in ["bed", "king", "queen", "double bed", "single bed", "bunk"]):
            furniture_type_hint = (
                "This is a BED. You MUST include: 'Size', 'Frame Material', 'Storage', 'Mattress Included'.\n"
                "- Size: 'Single (36x72)', 'Double (48x72)', 'Queen (60x72)', 'King (72x72)', 'King (72x84)'.\n"
                "- Frame Material: 'Solid Wood', 'Sheesham Wood', 'MDF', 'Metal', 'Upholstered'.\n"
                "- Storage: 'No Storage', 'Side Drawers', 'Hydraulic Storage', 'Box Storage'.\n"
                "- Mattress Included: 'Yes - Spring Mattress', 'Yes - Foam Mattress', 'Not Included'.\n"
                "Also add 'Style': 'Modern', 'Classic', 'Chinioti Carved', 'Divan Style', 'Platform Bed'."
            )
        elif any(w in t_lower for w in ["dining", "dining table", "dining set"]):
            furniture_type_hint = (
                "This is a DINING TABLE/SET. You MUST include: 'Seats', 'Shape', 'Material', 'Chair Included'.\n"
                "- Seats: '4 Seats', '6 Seats', '8 Seats', '10 Seats', '12 Seats'.\n"
                "- Shape: 'Rectangular', 'Round', 'Oval', 'Square'.\n"
                "- Material: 'Solid Wood', 'Sheesham Wood', 'Glass Top', 'Marble Top', 'MDF', 'Metal Legs'.\n"
                "- Chair Included: 'Yes - 4 Chairs', 'Yes - 6 Chairs', 'Chairs Not Included'.\n"
                "Also add 'Style': 'Modern', 'Traditional', 'Chinioti', 'Industrial'."
            )
        elif any(w in t_lower for w in ["wardrobe", "almirah", "closet", "cupboard"]):
            furniture_type_hint = (
                "This is a WARDROBE/ALMIRAH. You MUST include: 'Doors', 'Material', 'Mirror', 'Compartments'.\n"
                "- Doors: '2 Doors', '3 Doors', '4 Doors', 'Sliding Doors'.\n"
                "- Material: 'Solid Wood', 'MDF', 'Steel/Metal', 'Engineered Wood'.\n"
                "- Mirror: 'With Full Mirror', 'With Half Mirror', 'No Mirror'.\n"
                "- Compartments: 'Hanging + Shelves', 'Shelves Only', 'With Drawers', 'Full Shelves'.\n"
                "Also add 'Style': 'Modern', 'Classic', 'Walk-in Style', 'Chinioti Carved'."
            )
        elif any(w in t_lower for w in ["desk", "study desk", "office desk", "computer desk"]):
            furniture_type_hint = (
                "This is a DESK. You MUST include: 'Material', 'Size', 'Storage', 'Style'.\n"
                "- Material: 'Solid Wood', 'MDF', 'Glass Top', 'Metal Frame', 'Laminated Board'.\n"
                "- Size: 'Small (80-100cm)', 'Medium (100-120cm)', 'Large (120-150cm)', 'L-Shape'.\n"
                "- Storage: 'No Storage', 'With Drawers', 'With Shelves', 'With Cabinet'.\n"
                "- Style: 'Modern', 'Executive', 'Study', 'Gaming Desk', 'Standing Desk'."
            )
        elif any(w in t_lower for w in ["chair", "stool", "office chair"]):
            furniture_type_hint = (
                "This is a CHAIR. You MUST include: 'Type', 'Material', 'Adjustable Height', 'Armrest'.\n"
                "- Type: 'Office Chair', 'Gaming Chair', 'Dining Chair', 'Accent Chair', 'Recliner', 'Bar Stool'.\n"
                "- Material: 'Mesh', 'Fabric', 'Leather', 'Rexine', 'Velvet', 'Plastic'.\n"
                "- Adjustable Height: 'Yes - Gas Lift', 'Fixed Height'.\n"
                "- Armrest: 'With Armrests', 'No Armrests', 'Adjustable Armrests'."
            )
        else:
            furniture_type_hint = (
                "For this FURNITURE item, You MUST include: 'Material', 'Style', 'Color/Finish'.\n"
                "- Material: 'Solid Wood', 'MDF', 'Metal', 'Leather', 'Fabric', 'Velvet', 'Rattan', 'Plastic'.\n"
                "- Style: 'Modern', 'Traditional', 'Antique', 'Chinioti', 'Minimalist', 'Industrial'.\n"
                "- Color/Finish: 'Dark Walnut', 'Light Oak', 'White', 'Black', 'Beige', 'Grey'.\n"
                "Also add any other relevant specification fields for this specific furniture item."
            )

        category_guidance = {
            "mobile": (
                "You MUST include these exact keys: 'RAM', 'Storage', 'Color'.\n"
                "- RAM: actual RAM options this specific model ships with (e.g. '6 GB', '8 GB', '12 GB').\n"
                "- Storage: actual storage options (e.g. '128 GB', '256 GB', '512 GB').\n"
                "- Color: colors this exact model came in (e.g. 'Black', 'Blue', 'Gold')."
            ),
            "laptop": (
                "You MUST include these keys: 'Processor', 'RAM', 'Storage', 'GPU', 'Generation'.\n"
                "- Processor: e.g. 'Intel Core i5', 'Intel Core i7', 'AMD Ryzen 5'.\n"
                "- RAM: e.g. '8 GB', '16 GB', '32 GB'.\n"
                "- Storage: e.g. '256 GB SSD', '512 GB SSD', '1 TB SSD'.\n"
                "- GPU: e.g. 'Integrated', 'NVIDIA RTX 3050', 'AMD Radeon'.\n"
                "- Generation: e.g. '10th Gen', '11th Gen', '12th Gen', '13th Gen'."
            ),
            "furniture": furniture_type_hint,
        }.get(category, "Provide the most relevant configuration options for this product.")


        prompt = f"""You are an AI assisting in a Pakistani classifieds marketplace.
Category: {category}
Title: "{title}"

Task: Generate the realistic, buyer-facing configuration dropdown options for this specific product in the Pakistani market.

{category_guidance}

Critical Rules:
- Only list variants that ACTUALLY EXIST for this specific model in Pakistan.
- For Pakistani local brands (Tecno, Infinix, Itel, Qmobile, Voice), use their real variants.
- Do NOT hallucinate specs. Max 6-8 options per dropdown key.

Return EXCLUSIVELY a valid JSON object with this exact structure:
{{
  "dropdowns": {{
    "RAM": ["6 GB", "8 GB", "12 GB"],
    "Storage": ["128 GB", "256 GB"],
    "Color": ["Black", "Blue", "Gold"]
  }}
}}
"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(chat_completion.choices[0].message.content)
            return result.get("dropdowns", {})
        except Exception as e:
            print(f"LLM Dropdown Gen Error: {e}")
            return {}

    async def fetch_online_market_prices(self, title: str, category: str = "") -> Dict[str, Any]:
        """
        Fetches live OLX Pakistan search snippets, extracts real PKR prices,
        and filters out outliers (fake listings) using IQR method.
        Returns both raw snippets and cleaned numeric prices.
        """
        import re

        if not title:
            return {"snippets": "No title provided.", "prices": [], "price_summary": ""}

        # Build two targeted OLX-Pakistan queries
        base = title.strip()
        queries = [
            f'site:olx.com.pk "{base}" used price PKR',
            f'"{base}" used sale Pakistan price PKR -new -brand',
        ]

        all_snippets: List[str] = []
        raw_prices: List[float] = []

        loop = asyncio.get_event_loop()

        for query in queries:
            try:
                def _search(q=query):
                    with DDGS() as ddgs:
                        return list(ddgs.text(q, max_results=5))

                results = await loop.run_in_executor(None, _search)
                for res in results:
                    snippet = f"- {res.get('title','')}: {res.get('body','')}"
                    all_snippets.append(snippet)
                    # Extract all PKR-style numbers: Rs 45000 / PKR 45,000 / 45000 PKR / 45,000 Rs
                    nums = re.findall(
                        r'(?:rs\.?|pkr\.?)\s*([\d,]+)|(\b[\d,]{4,7}\b)\s*(?:rs\.?|pkr\.?)',
                        snippet.lower()
                    )
                    for match in nums:
                        raw_str = (match[0] or match[1]).replace(',', '')
                        try:
                            val = float(raw_str)
                            # Sanity range per category
                            ranges = {
                                'mobile':    (3_000,  800_000),
                                'laptop':    (20_000, 1_500_000),
                                'furniture': (2_000,  2_000_000),
                            }
                            lo, hi = ranges.get(category, (1_000, 5_000_000))
                            if lo <= val <= hi:
                                raw_prices.append(val)
                        except ValueError:
                            pass
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                continue

        # --- Outlier filtering via IQR ---
        cleaned_prices: List[float] = []
        if len(raw_prices) >= 4:
            sorted_p = sorted(raw_prices)
            q1 = sorted_p[len(sorted_p) // 4]
            q3 = sorted_p[(3 * len(sorted_p)) // 4]
            iqr = q3 - q1
            lo_bound = q1 - 1.5 * iqr
            hi_bound = q3 + 1.5 * iqr
            cleaned_prices = [p for p in raw_prices if lo_bound <= p <= hi_bound]
        elif raw_prices:
            cleaned_prices = raw_prices

        price_summary = ""
        if cleaned_prices:
            avg = sum(cleaned_prices) / len(cleaned_prices)
            price_summary = (
                f"Extracted {len(cleaned_prices)} real PKR prices from OLX listings "
                f"(after outlier removal): {[int(p) for p in cleaned_prices]}. "
                f"Average: PKR {int(avg):,}"
            )
        else:
            price_summary = "No numeric prices could be reliably extracted from OLX results."

        snippets_text = "\n".join(all_snippets) if all_snippets else "No OLX listings found."
        return {
            "snippets": snippets_text,
            "prices": [int(p) for p in cleaned_prices],
            "price_summary": price_summary,
        }

    async def estimate_market_price(
        self,
        category: str,
        extracted_specs: dict,
        user_selections: dict,
        condition: str,
        title: str = "",
        dynamic_specs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Estimates the price in PKR using live OLX price data + LLM expertise.
        Passes cleaned numeric prices to the LLM so it averages real numbers.
        """
        if not self.client:
            return {"estimated_price": 0, "confidence": 0.0, "reasoning": "LLM pricing unavailable"}

        # Build a spec-enriched search title (e.g. "iPhone 6s 64GB")
        spec_suffix = ""
        if dynamic_specs:
            spec_parts = [v for v in dynamic_specs.values() if v and isinstance(v, str)]
            if spec_parts:
                spec_suffix = " " + " ".join(spec_parts[:2])  # e.g. "8 GB 128 GB"
        search_title = f"{title}{spec_suffix}".strip()

        # Fetch live OLX data
        market_data = await self.fetch_online_market_prices(search_title, category)

        prompt = f"""You are an Expert Used-Goods Price Appraiser for the Pakistani market (OLX Pakistan).
Category: {category}
Item: "{title}"
User-selected specs: {json.dumps({**(user_selections or {}), **(dynamic_specs or {})})}
Condition (1=worst, 10=brand new): {condition}

=== LIVE OLX PAKISTAN MARKET DATA ===
{market_data['snippets']}

=== EXTRACTED REAL PRICES FROM OLX LISTINGS ===
{market_data['price_summary']}
Raw cleaned prices (PKR, outliers removed): {market_data['prices']}
=====================================

Your task — formulate a highly accurate, trustworthy (90%+ accuracy) pricing prediction.

STEP 1 — Product Research (Mental Check):
- Identify the exact product model.
- Determine its original LAUNCH YEAR.
- Determine its ORIGINAL NEW PRICE or CURRENT NEW MARKET PRICE in Pakistan (PKR).

STEP 2 — Market Price Validation:
- Use the provided extracted OLX prices as ground truth for the current USED market.
- Discard extreme outliers (e.g., Rs 5,000 for an iPhone 13).
- Compare the new price vs the used market average to gauge typical depreciation based on age.

STEP 3 — Apply Precise Condition Depreciation:
- The user specified the condition as {condition} out of 10.
- Condition 9-10 (Like New/Open Box): minimal depreciation from current market rate.
- Condition 7-8 (Good/Minor wear): standard used market rate.
- Condition 4-6 (Average/Scratches): 15-30% below standard used rate.
- Condition 1-3 (Poor/Needs Repair): 40-60% below standard used rate.
- Calculate the FINAL CONDITION-ADJUSTED PRICE.

Return EXCLUSIVELY this JSON:
{{
  "launch_year": integer (estimated, e.g. 2021),
  "new_market_price": integer (estimated original/current new price in PKR),
  "simulated_market_data": [
    {{"listing": "OLX-style ad description", "price": 55000}},
    {{"listing": "OLX-style ad description", "price": 58000}}
  ],
  "base_used_price": integer (average standard used price in PKR before condition),
  "estimated_price": integer (the FINAL condition-adjusted fair market price in PKR),
  "confidence": float (0.0 to 1.0),
  "reasoning": "Explain the launch year, original price, used market average, and exactly how condition {condition}/10 influenced the final price."
}}
"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(chat_completion.choices[0].message.content)
            return result
        except Exception as e:
            error_msg = str(e)
            
            # Handle rate limits gracefully for the user
            if "Rate limit reached" in error_msg or "429" in error_msg:
                user_friendly_reason = "API Rate Limit reached. Proceeding with aggregated historical ML data."
            else:
                user_friendly_reason = "AI Prediction Service disrupted. Proceeding with aggregated historical ML data."
                
            return {"estimated_price": 0, "confidence": 0.0, "reasoning": user_friendly_reason, "simulated_market_data": []}

llm_pricing_service = LLMPricingService()
