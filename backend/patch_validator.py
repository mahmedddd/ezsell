"""
Patch script: replaces validate_listing_content in llm_pricing_service.py
"""

NEW_METHOD = '''    async def validate_listing_content(self, category: str, title: str, description: str) -> Dict[str, Any]:
        """
        Validates the title and extracts specs using the LLM.
        Includes a comprehensive rule-based pre-filter before LLM call.
        """
        if not self.client:
            return {"is_valid": True, "message": "LLM validation unavailable", "missing_fields": [], "suggested_title": title, "extracted_specs": {}}

        # ─────────────────────────────────────────────────────────────────────
        # STAGE 1 — Rule-Based Pre-Filter (fast, no LLM cost)
        # ─────────────────────────────────────────────────────────────────────
        import re as _re
        t = title.strip().lower()
        t_words = t.split()

        # ── 1a. Too short ────────────────────────────────────────────────────
        if len(t) < 4:
            return {
                "is_valid": False,
                "message": "Title is too short. Please provide more detail.",
                "missing_fields": [], "suggested_title": title, "extracted_specs": {}
            }

        # ── 1b. Generic rubbish / junk phrases (universal) ──────────────────
        JUNK_TITLES = {
            "phone", "mobile", "smartphone", "cell phone", "handphone",
            "laptop", "notebook", "computer", "pc", "macbook",
            "furniture", "item", "product", "stuff", "things", "thing",
            "for sale", "sale", "sell", "selling", "cheap", "urgent",
            "good condition", "good phone", "good laptop", "nice phone",
            "nice laptop", "nice sofa", "nice furniture", "nice item",
            "best deal", "best price", "deal", "urgent sale", "quick sale",
            "used phone", "used laptop", "used item", "used furniture",
            "old phone", "old laptop", "old furniture", "old item",
            "new phone", "new laptop", "new item", "brand new",
            "contact me", "call me", "whatsapp", "test", "testing",
            "hello", "hi", "please buy", "please", "asap",
        }
        if t in JUNK_TITLES:
            return {
                "is_valid": False,
                "message": f"\\'{title}\\' is not a valid product title. Please include the specific brand and model/type.",
                "missing_fields": [], "suggested_title": title, "extracted_specs": {}
            }

        # ── 1c. Gibberish / random chars (no real words) ─────────────────────
        # Reject if title is purely numeric or has no meaningful words ≥ 3 chars
        real_words = [w for w in t_words if _re.match(r\'^\' + \'[a-z]{3,}\' + r\'$\', w)]
        digits_only_title = bool(_re.match(r\'^[\\d\\s\\-]+$\', t))
        if digits_only_title or (len(t_words) <= 2 and not real_words):
            return {
                "is_valid": False,
                "message": "Title appears to be gibberish or too vague. Please include the product name/model.",
                "missing_fields": [], "suggested_title": title, "extracted_specs": {}
            }

        # ── 1d. Single-word brand-only (mobile/laptop) ───────────────────────
        MOBILE_BRANDS = {
            "samsung","apple","iphone","nokia","huawei","oppo","vivo","realme",
            "xiaomi","redmi","tecno","infinix","itel","qmobile","sony","motorola",
            "google","pixel","oneplus","nothing","zte","alcatel","honor"
        }
        LAPTOP_BRANDS = {
            "dell","hp","lenovo","acer","asus","apple","macbook","msi","razer",
            "alienware","microsoft","surface","lg","toshiba","gateway","medion"
        }
        ALL_BRANDS = MOBILE_BRANDS | LAPTOP_BRANDS

        if t in ALL_BRANDS:
            brand_title = title.strip().title()
            if category == "mobile":
                return {
                    "is_valid": False,
                    "message": f"Please add a model name after \'{brand_title}\', e.g. \'{brand_title} Galaxy S22\'",
                    "missing_fields": [], "suggested_title": title, "extracted_specs": {}
                }
            elif category == "laptop":
                return {
                    "is_valid": False,
                    "message": f"Please add a model/series after \'{brand_title}\', e.g. \'{brand_title} Inspiron 15 i7\'",
                    "missing_fields": [], "suggested_title": title, "extracted_specs": {}
                }

        # ── 1e. Category cross-contamination check ───────────────────────────
        MOBILE_ONLY_KEYWORDS = {
            "galaxy","note","redmi","realme","tecno","infinix","camon","spark",
            "phantom","reno","poco","iphone","s23","s22","s21","s20","a54",
            "12 pro","13 pro","14 pro","15 pro","nova","y series","f series"
        }
        LAPTOP_ONLY_KEYWORDS = {
            "inspiron","thinkpad","latitude","ideapad","probook","elitebook",
            "pavilion","vivobook","zenbook","aspire","nitro","rog","tuf",
            "macbook air","macbook pro","xps","spectre","envy","omen",
            "legion","swift","predator","chromebook","gram"
        }
        FURNITURE_KEYWORDS = {
            "sofa","couch","settee","bed","wardrobe","almirah","closet",
            "cupboard","dresser","desk","table","chair","stool","ottoman",
            "cabinet","shelf","shelves","bookcase","dining","recliner",
            "futon","armchair","loveseat","sectional","bunk","cot","mattress",
            "almirah","sideboard","hutch","credenza","console","bench"
        }
        MOBILE_BRAND_WORDS = {
            "samsung","apple","iphone","nokia","huawei","oppo","vivo",
            "realme","xiaomi","redmi","tecno","infinix","itel","qmobile",
            "oneplus","motorola","nothing","honor","pixel","google","sony"
        }
        LAPTOP_BRAND_WORDS = {
            "dell","hp","lenovo","acer","asus","msi","razer",
            "alienware","microsoft","surface","toshiba","lg"
        }

        title_has_mobile_brand  = any(b in t for b in MOBILE_BRAND_WORDS)
        title_has_laptop_brand  = any(b in t for b in LAPTOP_BRAND_WORDS)
        title_has_mobile_kw     = any(k in t for k in MOBILE_ONLY_KEYWORDS)
        title_has_laptop_kw     = any(k in t for k in LAPTOP_ONLY_KEYWORDS)
        title_has_furniture_kw  = any(k in t for k in FURNITURE_KEYWORDS)

        if category == "furniture":
            if (title_has_mobile_brand and title_has_mobile_kw) or title_has_laptop_kw:
                return {
                    "is_valid": False,
                    "message": "This looks like a mobile/laptop listing, not furniture. Please enter a furniture title like \'King Size Bed\' or \'5-Seater Sofa\'.",
                    "missing_fields": [], "suggested_title": "", "extracted_specs": {}
                }

        if category == "mobile":
            if title_has_furniture_kw and not title_has_mobile_brand:
                return {
                    "is_valid": False,
                    "message": "This looks like a furniture listing, not a mobile. Please enter a mobile title like \'Samsung Galaxy S23\' or \'iPhone 14 Pro\'.",
                    "missing_fields": [], "suggested_title": "", "extracted_specs": {}
                }
            if title_has_laptop_kw and not title_has_mobile_brand:
                return {
                    "is_valid": False,
                    "message": "This looks like a laptop listing. Please enter a mobile title like \'Samsung Galaxy S23 256GB\'.",
                    "missing_fields": [], "suggested_title": "", "extracted_specs": {}
                }

        if category == "laptop":
            if title_has_furniture_kw and not title_has_laptop_brand:
                return {
                    "is_valid": False,
                    "message": "This looks like a furniture listing, not a laptop. Please enter a laptop title like \'Dell XPS 15 i7 12th Gen\'.",
                    "missing_fields": [], "suggested_title": "", "extracted_specs": {}
                }
            if title_has_mobile_kw and title_has_mobile_brand and not title_has_laptop_brand:
                return {
                    "is_valid": False,
                    "message": "This looks like a mobile listing, not a laptop. Please enter a laptop title like \'HP ProBook 450 i5 11th Gen\'.",
                    "missing_fields": [], "suggested_title": "", "extracted_specs": {}
                }

        # ── 1f. Adjective-only / meaningless modifier junk (mobile/laptop) ───
        if category in ("mobile", "laptop"):
            ADJECTIVE_JUNK = {
                "good","nice","great","excellent","perfect","amazing","awesome",
                "best","cheap","affordable","low","price","high","end","urgent",
                "must","sell","quick","fast","powerful","slim","light","heavy",
                "big","small","mini","max","pro","ultra","plus","used","new","old",
            }
            non_adj_words = [
                w for w in t_words
                if w not in ADJECTIVE_JUNK and w not in ALL_BRANDS and len(w) >= 2
            ]
            meaningful = [
                w for w in non_adj_words
                if _re.search(r\'\\d\', w) or len(w) >= 3
            ]
            if not meaningful:
                example = "Samsung Galaxy S23 256GB" if category == "mobile" else "Dell XPS 15 i7 12th Gen"
                return {
                    "is_valid": False,
                    "message": f"Title is too vague. Please include the brand and model, e.g. \'{example}\'.",
                    "missing_fields": [], "suggested_title": title, "extracted_specs": {}
                }

        # ── 1g. Furniture-specific: no furniture keyword + all adjectives → junk
        if category == "furniture":
            FURNITURE_ADJECTIVE_JUNK = {
                "good","nice","great","cheap","affordable","best","old","new",
                "big","small","large","medium","heavy","light","wooden","metal",
                "imported","local","handmade","modern","classic","antique",
                "used","brand","urgent","for","sale","selling",
            }
            if not title_has_furniture_kw:
                all_junk = all(w in FURNITURE_ADJECTIVE_JUNK for w in t_words if len(w) > 2)
                if all_junk:
                    return {
                        "is_valid": False,
                        "message": "Please specify the type of furniture, e.g. \'King Size Bed\', \'L-Shape Sofa\', \'6-Seater Dining Table\'.",
                        "missing_fields": [], "suggested_title": title, "extracted_specs": {}
                    }

        # ─────────────────────────────────────────────────────────────────────
        # STAGE 2 — LLM Validation with strict category-aware prompt
        # ─────────────────────────────────────────────────────────────────────
        prompt = f"""You are a STRICT listing moderator for OLX Pakistan (mobiles, laptops, furniture).
Your job: decide if the listing title is a REAL, SPECIFIC product in the correct category.

Category: {category}
Title: "{title}"
Description: "{description}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CATEGORY-MISMATCH RULE (highest priority):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ A mobile/phone title submitted under "laptop" or "furniture" → INVALID.
❌ A laptop title submitted under "mobile" or "furniture" → INVALID.
❌ A furniture title submitted under "mobile" or "laptop" → INVALID.
❌ Generic sales phrases (e.g. "for sale", "cheap item", "good condition") → INVALID in ALL categories.
❌ Adjective-only or modifier-only titles (e.g. "Nice Sofa", "Good Phone", "Cheap Laptop") → INVALID.
❌ Titles with no product identity (random words, brand name alone, category word alone) → INVALID.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDATION RULES BY CATEGORY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE 1 — MOBILES (category=mobile):
✅ VALID: Brand name + ANY model identifier (number, series name, letter, variant).
   Examples: "iPhone 6s", "Samsung Galaxy S22", "Redmi Note 13", "Tecno Spark 20 Pro", "QMobile Noir S8"
❌ INVALID: Brand alone ("Samsung"), category word alone ("Phone", "Mobile"), adjective phrases ("Nice Phone", "Good Smartphone"), or any laptop/furniture-related terms without a phone brand+model.

RULE 2 — LAPTOPS (category=laptop):
✅ VALID: Brand name + model/series name or processor hint.
   Examples: "Dell Inspiron 15", "HP ProBook 450", "Lenovo ThinkPad", "MacBook Air M1", "Asus TUF A15 Ryzen 5"
❌ INVALID: Brand alone ("Dell"), category word alone ("Laptop", "Gaming Laptop"), adjective phrases ("Nice Laptop", "Fast Laptop"), or any mobile/furniture-related terms without a laptop brand+model.

RULE 3 — FURNITURE (category=furniture):
✅ VALID: Furniture TYPE clearly named, with at least ONE qualifier (size, material, style, brand, seating count).
   Examples: "King Size Bed", "L-Shape Sofa", "5 Seater Sofa", "Chinioti Wardrobe", "Office Chair", "Wooden Dining Table", "6 Seater Dining Set"
   — "Office Chair", "Gaming Chair", "Dining Chair" ARE valid (type qualifier present).
   — A bare furniture word with NO qualifier ("Sofa", "Bed", "Table", "Chair") is INVALID.
❌ INVALID: Bare type word only, adjective-only ("Nice Sofa", "Old Chair", "Big Bed"), or any mobile/laptop-related titles.

CRITICAL RULES (ALL categories):
- NEVER approve a title that is clearly from a different category.
- NEVER approve bare adjective phrases as product titles.
- NEVER approve pure sales language with no product name.
- If valid but could be more specific → set is_valid=true, add improvement hints in missing_fields only.
- Specs (RAM, storage, color, size numbers) are NEVER required to pass validation.

Return EXCLUSIVELY this JSON (no extra text, no markdown):
{{
  "is_valid": boolean,
  "message": "Title looks good! Ready to predict price." or specific rejection reason,
  "missing_fields": [] or ["Model name", "Size qualifier"] (informational hints only),
  "suggested_title": "same as input if valid, improved version if vague",
  "extracted_specs": {{}} (any specs extractable from title/description)
}}
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.0,
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
                f.write(f"--- ERROR AT {os.getenv(\'COMPUTERNAME\')} ---\\n")
                f.write(f"Model: {self.model}\\n")
                f.write(f"Key: {masked_key}\\n")
                f.write(traceback.format_exc())
            # When rate-limited or error occurs, allow the title through so users aren\'t blocked
            return {"is_valid": True, "message": "Validation temporarily unavailable, proceeding.", "missing_fields": [], "suggested_title": title, "extracted_specs": {}}
'''

with open('services/llm_pricing_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start marker
start_marker = '    async def validate_listing_content('
end_marker = '    async def _scrape_gsmarena_specs('

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1:
    print("ERROR: Could not find validate_listing_content method start")
    exit(1)

if end_idx == -1:
    print("ERROR: Could not find end marker")
    exit(1)

# Replace the old method with new one
new_content = content[:start_idx] + NEW_METHOD + '\n\n' + content[end_idx:]

with open('services/llm_pricing_service.py', 'w', encoding='utf-8', newline='') as f:
    f.write(new_content)

print("SUCCESS: validate_listing_content patched successfully")
print(f"Old length: {len(content)}, New length: {len(new_content)}")
