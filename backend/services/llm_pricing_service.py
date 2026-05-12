import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv
try:
    from ddgs import DDGS  # new package name
except ImportError:
    from duckduckgo_search import DDGS  # legacy fallback

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
✅ VALID: Any clear furniture item name. Qualifiers (size, material, style) are HIGHLY RECOMMENDED for better pricing but NOT strictly required if the item type is clear.
   Examples: "Sofa", "Bed", "King Size Bed", "L-Shape Sofa", "Chinioti Wardrobe", "Wooden Dining Table"
❌ INVALID: Adjective-only ("Nice", "Old", "Big") without the furniture type, or any mobile/laptop-related titles.

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
  "hints": {{
    "example": "Provide an example of a good title for this specific product, e.g. 'Modern 5 Seater L-Shape Velvet Sofa'"
  }},
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

        # --- Stage 1: Find GSMArena URL via their own search ---
        try:
            title_encoded = urllib.parse.quote_plus(title)
            search_url = f'https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={title_encoded}'
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                search_res = await client.get(search_url, headers=headers)
                if search_res.status_code == 200:
                    links = re.findall(r'href="/?([a-zA-Z0-9_-]+-\d+\.php)"', search_res.text)
                    for link in links:
                        candidate = f"https://www.gsmarena.com/{link.lstrip('/')}"
                        if re.match(r'^https://www\.gsmarena\.com/[a-zA-Z0-9_-]+-\d+\.php$', candidate):
                            gsmarena_url = candidate
                            break
        except Exception as e:
            print(f"GSMArena direct search failed: {e}")

        # --- Stage 1 Fallback: DuckDuckGo (only if GSMArena search returned nothing) ---
        if not gsmarena_url:
            try:
                loop = asyncio.get_event_loop()
                def _ddg_find():
                    try:
                        with DDGS() as ddgs:
                            results = list(ddgs.text(f'site:gsmarena.com "{title}" specifications', max_results=5))
                            for r in results:
                                url = r.get('href', '')
                                if re.match(r'^https://www\.gsmarena\.com/[a-zA-Z0-9_-]+-\d+\.php$', url):
                                    return url
                    except:
                        pass
                    return None
                gsmarena_url = await loop.run_in_executor(None, _ddg_find)
                
                # Double fallback using raw HTML if ddgs fails due to rate limits
                if not gsmarena_url:
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                        ddg_html_url = f"https://html.duckduckgo.com/html/?q=site:gsmarena.com+{urllib.parse.quote_plus(title)}+specifications"
                        res = await client.get(ddg_html_url, headers=headers)
                        if res.status_code == 200:
                            urls = re.findall(r'href="([^"]+gsmarena\.com/[^"]+-\d+\.php)"', res.text)
                            for u in urls:
                                # HTML duckduckgo wraps urls in redirecters
                                decoded_match = re.search(r'uddg=(https?://www\.gsmarena\.com/[^&]+)', urllib.parse.unquote(u))
                                final_url = decoded_match.group(1) if decoded_match else u
                                if re.match(r'^https://www\.gsmarena\.com/[a-zA-Z0-9_-]+-\d+\.php$', final_url):
                                    gsmarena_url = final_url
                                    break
            except Exception as e:
                print(f"DDG fallback discovery failed: {e}")

        if not gsmarena_url:
            print(f"No GSMArena URL found for '{title}'")
            return {}

        # --- Stage 2: Fetch and parse the spec table ---
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
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

                # Extract storage: look for storage-sized values (>=32GB) not tagged as RAM
                all_gb_tb = re.findall(r'(\d+)\s*(GB|TB)', raw, re.IGNORECASE)
                storage_set = set()
                for v, unit in all_gb_tb:
                    val = int(v)
                    if unit.upper() == 'TB':
                        storage_set.add(f"{val} TB")
                    elif unit.upper() == 'GB' and val >= 32:
                        storage_set.add(f"{val} GB")

                # Fallback: split by comma, each segment's first big number is storage
                parts = raw.split(',')
                for p in parts:
                    sizes = re.findall(r'(\d+)\s*(GB|TB)', p, re.IGNORECASE)
                    if len(sizes) >= 2:
                        s_val, s_unit = sizes[0]
                        storage_set.add(f"{s_val} {s_unit.upper()}")

                if storage_set:
                    def storage_sort_key(x):
                        num = int(re.search(r'\d+', x).group())
                        return num * 1024 if 'TB' in x else num
                    specs["Storage"] = sorted(list(storage_set), key=storage_sort_key)

            # --- Parse Colors ---
            color_match = re.search(
                r'Colors?.*?<td[^>]*>(.*?)</td>',
                html, re.IGNORECASE | re.DOTALL
            )
            if color_match:
                raw = re.sub(r'<[^>]+>', ' ', color_match.group(1))
                raw = re.sub(r'\s+', ' ', raw).strip()
                colors = [c.strip() for c in re.split(r'[,;]', raw) if c.strip() and len(c.strip()) > 2]
                if colors:
                    specs["Color"] = colors[:8]

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
                print(f"DDG ddgs error, falling back to httpx: {e}")
                # Fallback to HTML DuckDuckGo
                try:
                    import httpx
                    import re
                    import urllib.parse
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                        html_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(q)}"
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                        res = await client.get(html_url, headers=headers)
                        if res.status_code == 200:
                            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', res.text, re.IGNORECASE | re.DOTALL)
                            return [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]
                except Exception as e2:
                    print(f"DDG httpx fallback error: {e2}")
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
                "- RAM: actual RAM options this specific model ships with (e.g. '8 GB', '12 GB'). CRITICAL: If the title is for a modern phone like Samsung Galaxy A55 or A56, DO NOT output 6 GB. They ship with '8 GB' and '12 GB' primarily.\n"
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
        Aggressively fetches used OLX prices and new retail prices from Pakistan.
        Runs ALL queries (not just until first hit) to gather enough data points
        for IQR outlier filtering to reject fake/dump prices.
        """
        import re

        if not title:
            return {"snippets": "No title provided.", "prices": [], "new_prices": [], "price_summary": ""}

        base = title.strip()
        loop = asyncio.get_event_loop()

        lo, hi = {
            'mobile':    (3_000,  800_000),
            'laptop':    (20_000, 1_500_000),
            'furniture': (2_000,  2_000_000),
        }.get(category, (1_000, 5_000_000))

        def _extract_pkr(text: str) -> List[float]:
            """Extract all valid PKR prices from a text snippet."""
            nums = re.findall(
                r'(?:rs\.?|pkr\.?)\s*([\d,]+)|([\d,]{4,7})\s*(?:rs\.?|pkr\.?)',
                text.lower()
            )
            result = []
            for m in nums:
                raw = (m[0] or m[1]).replace(',', '')
                try:
                    v = float(raw)
                    if lo <= v <= hi:
                        result.append(v)
                except ValueError:
                    pass
            return result

        def _iqr_filter(prices: List[float]) -> List[float]:
            """Remove statistical outliers (fake/dump prices) using IQR."""
            if len(prices) >= 4:
                s = sorted(prices)
                q1, q3 = s[len(s)//4], s[(3*len(s))//4]
                iqr = q3 - q1
                # Tighter fence (1.2x instead of 1.5x) to be stricter about fakes
                return [p for p in prices if (q1 - 1.2*iqr) <= p <= (q3 + 1.2*iqr)]
            return prices

        # --- Category-specific OLX used price queries ---
        # Run ALL of them (no early break) to gather as many real prices as possible
        if category == 'mobile':
            olx_queries = [
                f'"{base}" OLX Pakistan used price Rs',
                f'"{base}" sale Pakistan used PKR mobile',
                f'{base} used mobile for sale Pakistan',
                f'{base} second hand price Pakistan',
                f'{base} olx.com.pk price',
            ]
            new_queries = [
                f'"{base}" price Pakistan 2024 2025',
                f'"{base}" price in Pakistan new official',
                f'{base} new price PKR phoneworld priceoye hamariweb',
            ]
        elif category == 'laptop':
            olx_queries = [
                f'"{base}" OLX Pakistan used laptop price Rs',
                f'"{base}" laptop sale Pakistan used PKR',
                f'{base} used laptop Pakistan price',
                f'{base} second hand laptop price Pakistan',
                f'{base} olx.com.pk laptop',
            ]
            new_queries = [
                f'"{base}" laptop price Pakistan 2024 2025',
                f'"{base}" laptop price in Pakistan new official',
                f'{base} laptop new price PKR Pakistan symbios',
            ]
        elif category == 'furniture':
            olx_queries = [
                f'"{base}" OLX Pakistan used furniture price Rs',
                f'"{base}" furniture sale Pakistan PKR',
                f'{base} used furniture Pakistan price',
                f'{base} second hand furniture Pakistan',
                f'{base} olx.com.pk furniture',
            ]
            new_queries = [
                f'"{base}" furniture price Pakistan new',
                f'"{base}" furniture price PKR Pakistan shop',
                f'{base} furniture price Pakistan buy new',
            ]
        else:
            olx_queries = [
                f'"{base}" OLX Pakistan used price Rs',
                f'"{base}" sale Pakistan used PKR',
                f'{base} used Pakistan price olx',
            ]
            new_queries = [
                f'"{base}" price Pakistan new 2024 2025',
                f'"{base}" price in Pakistan new official',
            ]

        async def _run_all_queries(queries: List[str], max_per_query: int = 8) -> tuple:
            """Run ALL queries and collect ALL prices — no early termination."""
            all_snips, all_prices = [], []
            tasks = []

            def _search(q):
                try:
                    with DDGS() as ddgs:
                        return list(ddgs.text(q, max_results=max_per_query))
                except:
                    return []

            # Run all queries concurrently
            results_list = await asyncio.gather(
                *[loop.run_in_executor(None, _search, q) for q in queries],
                return_exceptions=True
            )

            for results in results_list:
                if isinstance(results, Exception):
                    continue
                for r in results:
                    snip = f"- {r.get('title','')}: {r.get('body','')}"
                    all_snips.append(snip)
                    all_prices.extend(_extract_pkr(snip))

            return all_snips, _iqr_filter(all_prices)

        # Run OLX and new price queries concurrently (both tracks at once)
        (olx_snips, used_prices), (new_snips, new_prices) = await asyncio.gather(
            _run_all_queries(olx_queries, max_per_query=8),
            _run_all_queries(new_queries, max_per_query=5),
        )

        all_snippets = olx_snips + new_snips

        # Build human-readable summary for LLM
        parts = []
        if used_prices:
            avg = int(sum(used_prices) / len(used_prices))
            parts.append(
                f"OLX USED prices ({len(used_prices)} listings, fake/outliers removed via IQR): "
                f"{[int(p) for p in used_prices]} — avg PKR {avg:,}"
            )
        else:
            parts.append("OLX used prices: none found (DDG may be rate-limited or no listings exist yet).")

        if new_prices:
            avg = int(sum(new_prices) / len(new_prices))
            parts.append(
                f"NEW RETAIL prices ({len(new_prices)} sources, outliers removed): "
                f"{[int(p) for p in new_prices]} — avg PKR {avg:,}"
            )
        else:
            parts.append("New retail prices: none found.")

        return {
            "snippets": "\n".join(all_snippets) if all_snippets else "No listings found.",
            "prices": [int(p) for p in used_prices],
            "new_prices": [int(p) for p in new_prices],
            "price_summary": "\n".join(parts),
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

=== LIVE PAKISTAN MARKET DATA (scraped from web) ===
{market_data['snippets']}

=== EXTRACTED PRICES (cleaned, outliers removed) ===
{market_data['price_summary']}
OLX Used prices (PKR): {market_data['prices']}
New retail prices (PKR): {market_data.get('new_prices', [])}
=====================================================

Your task — produce a highly accurate, trustworthy pricing prediction.

STEP 1 — Anchor to Real Data:
- If new retail prices are provided above, use them as the authoritative "current new price" in Pakistan.
- If OLX used prices are provided, use their average as the authoritative "current used market" baseline.
- If either is missing, use your knowledge of the Pakistani market to estimate — but ALWAYS prefer scraped data.

STEP 2 — Validate:
- Cross-check: does the OLX used price make sense relative to the new price? (used should be 30-70% below new for items 1-3 years old)
- Discard any obvious fake listings (e.g., Rs 5,000 for an iPhone 13).

STEP 3 — Apply Precise Condition Depreciation from the USED market baseline:
- Condition 9-10 (Like New/Open Box): used market rate or slightly above.
- Condition 7-8 (Good/Minor wear): standard used market rate (0-15% discount).
- Condition 4-6 (Average/Scratches): 15-30% below standard used rate.
- Condition 1-3 (Poor/Needs Repair): 40-60% below standard used rate.

Return EXCLUSIVELY this JSON:
{{
  "launch_year": integer,
  "new_market_price": integer (the current new price in PKR — anchor to scraped data if available),
  "simulated_market_data": [
    {{"listing": "OLX-style ad description", "price": 55000}},
    {{"listing": "OLX-style ad description", "price": 58000}}
  ],
  "base_used_price": integer (average standard used price in PKR — anchor to OLX scraped data if available),
  "estimated_price": integer (FINAL condition-adjusted fair market price in PKR),
  "confidence": float (0.0 to 1.0 — lower if no scraped data was available),
  "reasoning": "Explain: scraped new price used, scraped OLX used price used, how condition {condition}/10 was applied."
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
