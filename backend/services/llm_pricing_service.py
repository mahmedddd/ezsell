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
        Stage 1: Comprehensive rule-based pre-filter (always runs, even without LLM).
        Stage 2: LLM validation for nuanced cases.
        """
        # NOTE: Stage 1 runs BEFORE the LLM client check intentionally —
        # so garbage titles are always rejected even during LLM downtime/rate-limiting.

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
            "nice smartphone", "nice mobile", "nice notebook", "nice computer",
            "great phone", "great laptop", "great item", "great deal",
            "best deal", "best price", "deal", "urgent sale", "quick sale",
            "used phone", "used laptop", "used item", "used furniture",
            "old phone", "old laptop", "old furniture", "old item",
            "new phone", "new laptop", "new item", "brand new",
            "contact me", "call me", "whatsapp", "test", "testing",
            "hello", "hi", "please buy", "please", "asap",
            "gaming laptop", "gaming notebook", "gaming computer",
            "cheap phone", "cheap laptop", "cheap mobile",
            "good notebook", "good computer", "good mobile",
        }
        if t in JUNK_TITLES:
            return {
                "is_valid": False,
                "message": f"'{title}' is not a valid product title. Please include the specific brand and model/type.",
                "missing_fields": [], "suggested_title": title, "extracted_specs": {}
            }

        # ── 1c. Gibberish / random chars detection ───────────────────────────
        # Reject purely numeric titles
        digits_only_title = bool(_re.match(r'^[\d\s\-]+$', t))
        if digits_only_title:
            return {
                "is_valid": False,
                "message": "Title appears to be numeric/gibberish. Please include the product name/model.",
                "missing_fields": [], "suggested_title": title, "extracted_specs": {}
            }
        # Reject titles with ≤2 words and NO recognizable word ≥4 chars
        # This catches 'abc 123', 'xyz 99', 'aa bb', etc.
        meaningful_words = [w for w in t_words if len(w) >= 4 and _re.match(r'^[a-zA-Z]', w)]
        
        # Also catch words that are >=4 chars but mean nothing
        JUNK_WORDS = {"test", "hello", "dummy", "testing", "check", "asdf"}
        valid_words = [w for w in meaningful_words if w not in JUNK_WORDS]
        
        if len(t_words) <= 2 and not valid_words:
            return {
                "is_valid": False,
                "message": "Title appears to be gibberish or too vague. Please include the product name/model.",
                "missing_fields": [], "suggested_title": title, "extracted_specs": {}
            }



        # ─────────────────────────────────────────────────────────────────────
        # STAGE 2 — LLM Validation with strict category-aware prompt
        # ─────────────────────────────────────────────────────────────────────
        # If LLM is unavailable, Stage 1 already caught garbage; pass through for genuine titles
        if not self.client:
            return {"is_valid": True, "message": "LLM validation unavailable — rule-based checks passed.", "missing_fields": [], "suggested_title": title, "extracted_specs": {}}

        prompt = f"""You are a STRICT listing moderator for OLX Pakistan (mobiles, laptops, furniture).
Your job: decide if the listing title is a REAL, SPECIFIC product in the correct category.

Category: {category}
Title: "{title}"
Description: "{description}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT INSTRUCTION REGARDING "EXISTENCE" & TYPOS:
Do NOT reject future, unreleased, or unrecognized model numbers if the format is structurally valid (e.g. "iPhone 17", "Samsung S25"). Assume the user is selling a newly released item or a pre-release. 
HOWEVER, you MUST reject incomplete words, typos, or single dangling letters (e.g., reject "iphone 17 p" and ask them to specify if they mean "Pro" or "Plus").
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
                f.write(f"--- ERROR AT {os.getenv('COMPUTERNAME')} ---\n")
                f.write(f"Model: {self.model}\n")
                f.write(f"Key: {masked_key}\n")
                f.write(traceback.format_exc())
            # When rate-limited or error occurs, allow the title through so users aren't blocked
            return {"is_valid": True, "message": "Validation temporarily unavailable, proceeding.", "missing_fields": [], "suggested_title": title, "extracted_specs": {}}


    async def _scrape_gsmarena_specs(self, title: str) -> Dict[str, List[str]]:
        """
        Stage 1: Search GSMArena directly to find the device page URL.
        Stage 2: Fetch + parse the actual spec table from that GSMArena page.
        Returns a structured dict: {'RAM': [...], 'Storage': [...], 'Color': [...]}
        """
        import httpx
        import re
        import urllib.parse

        gsmarena_url = None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # --- Stage 1: Find GSMArena URL ---
        try:
            from duckduckgo_search import DDGS
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _run_search():
                try:
                    with DDGS() as ddgs:
                        # Narrow search to exact device specs
                        q = f'site:gsmarena.com "{title}" specifications'
                        return list(ddgs.text(q, max_results=5))
                except:
                    return []
            
            search_results = await loop.run_in_executor(None, _run_search)
            for r in search_results:
                url = r.get('href', '')
                # Filter to valid device pages (e.g. https://www.gsmarena.com/samsung_galaxy_a56-13603.php)
                if re.match(r'^https://www\.gsmarena\.com/[a-zA-Z0-9_-]+-\d+\.php$', url):
                    gsmarena_url = url
                    break

            # Fallback to direct search if DDG yields nothing or is blocked
            if not gsmarena_url:
                search_url = f'https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={urllib.parse.quote_plus(title)}'
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    search_res = await client.get(search_url, headers=headers)
                    if search_res.status_code == 200:
                        links = re.findall(r'href="(.*?\.php)"', search_res.text)
                        for link in links:
                            if re.match(r'^[a-zA-Z0-9_-]+-\d+\.php$', link):
                                gsmarena_url = f"https://www.gsmarena.com/{link}"
                                break
        except Exception as e:
            print(f"GSMArena URL discovery failed: {e}")

        if not gsmarena_url:
            print(f"No GSMArena URL found for '{title}'")
            return {}

        # --- Stage 2: Fetch and parse the spec table ---
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(gsmarena_url, headers=headers)
                html = response.text

            specs: Dict[str, List[str]] = {}

            # --- Parse RAM & Storage from internalmemory ---
            memory_match = re.search(
                r'data-spec="internalmemory"[^>]*>(.*?)</td>',
                html, re.IGNORECASE | re.DOTALL
            )
            if memory_match:
                raw = memory_match.group(1)
                
                # Find all GB/TB values before "RAM"
                ram_vals = re.findall(r'(\d+)\s*GB\s*RAM', raw, re.IGNORECASE)
                if ram_vals:
                    specs["RAM"] = sorted(list(set([f"{v} GB" for v in ram_vals if 2 <= int(v) <= 24])), key=lambda x: int(re.search(r'\d+', x).group()))

                # Extract storage: it's typically the first GB/TB value in each pair, e.g. "128GB 6GB RAM"
                # So we look for numbers followed by GB or TB that are NOT immediately followed by RAM
                # Alternatively, just find all GB/TB values and filter out the RAM ones
                all_gb_tb = re.findall(r'(\d+)\s*(GB|TB)', raw, re.IGNORECASE)
                storage_set = set()
                for v, unit in all_gb_tb:
                    val = int(v)
                    if unit.upper() == 'GB' and val >= 16 and val not in [2,3,4,6,8,12,16,24]: # typical storage vs RAM disambiguation
                        storage_set.add(f"{val} GB")
                    elif unit.upper() == 'TB':
                        storage_set.add(f"{val} TB")
                    elif unit.upper() == 'GB' and val == 16 and "16GB RAM" not in raw.upper():
                        storage_set.add("16 GB")
                        
                # More robust fallback: split by comma, extract first size as storage, second as RAM
                parts = raw.split(',')
                for p in parts:
                    sizes = re.findall(r'(\d+)\s*(GB|TB)', p, re.IGNORECASE)
                    if len(sizes) >= 2:
                        s_val, s_unit = sizes[0]
                        storage_set.add(f"{s_val} {s_unit.upper()}")
                        
                if storage_set:
                    # Sort storage values properly
                    def storage_sort_key(x):
                        num = int(re.search(r'\d+', x).group())
                        return num * 1024 if 'TB' in x else num
                    specs["Storage"] = sorted(list(storage_set), key=storage_sort_key)

            # --- Parse Colors ---
            # GSMArena format: Colors  White, Blue, Violet etc (inside <td>)
            color_match = re.search(
                r'Colors?.*?<td[^>]*>(.*?)</td>',
                html, re.IGNORECASE | re.DOTALL
            )
            if color_match:
                raw = re.sub(r'<[^>]+>', ' ', color_match.group(1))  # strip HTML tags
                raw = re.sub(r'\s+', ' ', raw).strip()
                # Split on commas or semicolons
                colors = [c.strip() for c in re.split(r'[,;]', raw) if c.strip() and len(c.strip()) > 2]
                if colors:
                    specs["Color"] = colors[:8]  # max 8 colors

            print(f"GSMArena scraped specs for '{title}': {specs}")
            return specs

        except Exception as e:
            print(f"GSMArena scrape failed for '{title}': {e}")
            return {}

    async def _fetch_web_specs(self, title: str, category: str) -> str:
        """
        For mobile: tries GSMArena scraping first (returns structured JSON string).
        For laptop: uses DuckDuckGo parallel search snippets.
        Returns a string context for LLM grounding.
        """
        if category == "mobile":
            scraped = await self._scrape_gsmarena_specs(title)
            if scraped:
                # Convert to a clear, structured string the LLM can parse exactly
                parts = []
                for key, vals in scraped.items():
                    parts.append(f"{key}: {', '.join(vals)}")
                return "OFFICIAL SPECS FROM GSMARENA:\n" + "\n".join(parts)
            # Fallback: DDG snippets
            return await self._ddg_snippets(title, category)

        elif category == "laptop":
            return await self._ddg_snippets(title, category)

        return ""

    async def _ddg_snippets(self, title: str, category: str) -> str:
        """Fallback: parallel DuckDuckGo searches for spec snippets."""
        loop = asyncio.get_event_loop()
        if category == "mobile":
            queries = [
                f'"{title}" specifications RAM storage color Pakistan',
                f'site:phoneworld.com.pk "{title}" specifications',
            ]
        else:
            queries = [
                f'site:notebookcheck.net "{title}" review specifications',
                f'"{title}" laptop RAM storage processor specifications Pakistan',
            ]

        async def search_one(q: str) -> List[str]:
            try:
                def _run():
                    with DDGS() as ddgs:
                        return list(ddgs.text(q, max_results=3))
                results = await loop.run_in_executor(None, _run)
                return [f"[{r.get('title','')}] {r.get('body','')}" for r in results if r.get('body')]
            except Exception as e:
                print(f"DDG fallback error: {e}")
                return []

        all_results = await asyncio.gather(*[search_one(q) for q in queries])
        snippets: List[str] = []
        for r in all_results:
            snippets.extend(r)
        return "\n".join(snippets[:6])


    async def generate_relevant_dropdowns(self, category: str, title: str) -> Dict[str, List[str]]:
        """
        Generates contextual dropdown options based on what the user is typing.
        For mobiles/laptops: first fetches real specs from the web, then grounds LLM on those facts.
        For furniture: uses structured LLM prompts.
        """
        if not self.client or len(title.strip()) < 3:
            return {}

        # --- Web-grounded spec fetching for mobile and laptop ---
        web_context = ""
        scraped_mobile_specs = None
        if category == "mobile":
            scraped_mobile_specs = await self._scrape_gsmarena_specs(title)
            if scraped_mobile_specs and any(scraped_mobile_specs.values()):
                print(f"Returning GSMArena data directly (no LLM needed): {scraped_mobile_specs}")
                return scraped_mobile_specs
            # Fallback if GSMArena fails
            web_context = await self._ddg_snippets(title, category)
        elif category == "laptop":
            web_context = await self._fetch_web_specs(title, category)

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

        # --- For mobile: if GSMArena scrape was successful, bypass LLM entirely ---
        if category == "mobile" and web_context.startswith("OFFICIAL SPECS FROM GSMARENA:"):
            scraped = await self._scrape_gsmarena_specs(title)
            if scraped and any(scraped.values()):
                print(f"Returning GSMArena data directly (no LLM needed): {scraped}")
                return scraped

        category_guidance = {
            "mobile": (
                "You MUST include these exact keys: 'RAM', 'Storage', 'Color'.\n"
                "- RAM: actual RAM options this specific model ships with (e.g. '8 GB', '12 GB').\n"
                "- Storage: actual storage options (e.g. '128 GB', '256 GB').\n"
                "- Color: the FULL official color names for this model (e.g. 'Awesome Navy', 'Awesome Iceblue')."
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

        # Build grounding context section for the prompt

        grounding_section = ""
        if web_context:
            grounding_section = f"""
REAL SPECS FROM THE WEB (use these as your PRIMARY source — they are ground truth):
---
{web_context}
---
Copy the RAM, Storage, and Color values EXACTLY as they appear above. Do NOT paraphrase. Do NOT add extras.
"""
        else:
            grounding_section = (
                "No web data available. Use your training knowledge carefully — "
                "only include specs you are 100% certain about for this exact model. "
                "Use FULL official color names (e.g. 'Awesome Navy', not just 'Navy')."
            )

        prompt = f"""You are an expert product database for the Pakistani mobile/tech/furniture market.
Category: {category}
Product Title: "{title}"

{grounding_section}

Task: Return ONLY the exact configuration variants that this SPECIFIC product model was officially released with.

{category_guidance}

STRICT RULES:
1. If web data is provided above, copy it VERBATIM — do NOT modify, combine, or add to it.
2. Do NOT invent variants. Do NOT add options not in the web data.
3. For Color: always use the FULL official marketing name (e.g. 'Awesome Navy', 'Phantom Black', 'Sierra Blue') — never shorten to just 'Navy' or 'Black'.
4. Max 8 options per key.

Return EXCLUSIVELY a valid JSON object:
{{
  "dropdowns": {{
    "RAM": ["8 GB", "12 GB"],
    "Storage": ["128 GB", "256 GB"],
    "Color": ["Awesome Navy", "Awesome Iceblue"]
  }}
}}
"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.0,  # Zero temperature = fully deterministic, no creativity
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
        # This ensures that whether a user writes specs in the title or selects them from dropdowns,
        # the OLX search query (and thus the LLM prediction) is absolutely identical.
        spec_suffix_parts = []
        us = user_selections or {}
        t_lower = title.lower()

        import re as _re

        def _extract_num(val):
            """Extract integer from values like 6, '6', '6 GB', '256 GB'."""
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return int(val)
            m = _re.search(r'(\d+)', str(val))
            return int(m.group(1)) if m else None

        if category == 'mobile':
            ram_num = _extract_num(us.get('ram'))
            stor_num = _extract_num(us.get('storage'))
            if ram_num and ram_num != 0:
                if f"{ram_num}gb" not in t_lower and f"{ram_num} gb" not in t_lower:
                    spec_suffix_parts.append(f"{ram_num}GB")
            if stor_num and stor_num != 0:
                if f"{stor_num}gb" not in t_lower and f"{stor_num} gb" not in t_lower:
                    spec_suffix_parts.append(f"{stor_num}GB")
            if us.get('is_pta') and 'pta' not in t_lower:
                spec_suffix_parts.append("PTA")
                
        elif category == 'laptop':
            if us.get('processor') and str(us.get('processor')).lower() not in t_lower:
                spec_suffix_parts.append(str(us.get('processor')))
            ram_num = _extract_num(us.get('ram'))
            stor_num = _extract_num(us.get('storage'))
            if ram_num and ram_num != 0:
                if f"{ram_num}gb" not in t_lower and f"{ram_num} gb" not in t_lower:
                    spec_suffix_parts.append(f"{ram_num}GB")
            if stor_num and stor_num != 0:
                if f"{stor_num}gb" not in t_lower and f"{stor_num} gb" not in t_lower:
                    spec_suffix_parts.append(f"{stor_num}GB")
                
        elif category == 'furniture':
            if us.get('material') and str(us.get('material')).lower() not in t_lower:
                spec_suffix_parts.append(str(us.get('material')))
            if us.get('furniture_type') and str(us.get('furniture_type')).lower() not in t_lower:
                spec_suffix_parts.append(str(us.get('furniture_type')))

        if dynamic_specs:
            import re
            for k, v in dynamic_specs.items():
                if v and isinstance(v, str):
                    v_stripped = v.strip()
                    # Normalize: "6 GB" -> "6GB" for comparison
                    v_normalized = re.sub(r'\s+', '', v_stripped).lower()
                    t_normalized = re.sub(r'\s+', '', t_lower)
                    if v_normalized not in t_normalized:
                        # Use cleaned version in search (e.g., "6GB" not "6 GB")
                        cleaned = re.sub(r'\s*(GB|TB|MP|MHz|GHz)\s*', r'\1', v_stripped, flags=re.IGNORECASE)
                        spec_suffix_parts.append(cleaned)
                    
        spec_suffix = " ".join(spec_suffix_parts[:5]) # limit to top 5 specs to prevent overly long queries
        search_title = f"{title} {spec_suffix}".strip()

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
