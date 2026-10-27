import csv
import json
import math
import re
from collections import Counter, defaultdict

class ThelawalaSearchEngine:
    """
    Search Engine for Thelawala Grocery Delivery.
    
    Addresses key team constraints and domain nuances:
    1. Fast, offline, 100% local (BM25 + Behavioral Mining + Fuzzy Matching)
    2. Zero external API calls, sub-10ms response time
    3. Handles 1-thumb typing typos (fuzzy matching)
    4. Handles Hyderabadi / Telugu / Hindi colloquial synonyms
    5. Prioritizes in-stock items (Sandeep) while retaining OOS discovery (Farah)
    6. Respects brand intent (Kavya) while boosting private label on generic queries (Farah)
    7. Natural language budget query parsing (e.g. "oil under 200")
    8. Fixes catalog pricing unit discrepancies (Finance finding)
    """

    DISTINCTIVE_BRANDS = {
        "godavari": "godavari dairy",
        "godavari dairy": "godavari dairy",
        "gomatha": "gomatha",
        "annapurna": "annapurna mills",
        "annapurna mills": "annapurna mills",
        "ammas": "ammas kitchen",
        "ammas kitchen": "ammas kitchen",
        "deccan": "deccan gold",
        "deccan gold": "deccan gold",
        "golconda": "golconda grains",
        "golconda grains": "golconda grains",
        "kisanpur": "kisanpur",
        "banjara": "banjara spice",
        "banjara spice": "banjara spice",
        "purely": "purely",
        "herbaleaf": "herbaleaf",
        "biscoo": "biscoo",
        "crispo": "crispo",
        "chocomore": "chocomore",
        "snackwala": "snackwala",
        "fizzo": "fizzo",
        "cleanup": "cleanup",
        "sparkle": "sparkle",
        "thela select": "thela select",
        "thela fresh": "thela fresh",
        "chillbox": "chillbox",
        "frost fresh": "frost fresh",
        "shubhra": "shubhra",
        "pooja deep": "pooja deep",
        "morning oven": "morning oven",
        "suryakanti": "suryakanti",
        "aquaneer": "aquaneer",
        "kaapi house": "kaapi house",
        "chai bagh": "chai bagh",
        "little bee": "little bee",
        "softies": "softies",
        "ruchi andhra": "ruchi andhra",
        "henfresh": "henfresh",
        "malabar leaf": "malabar leaf"
    }

    # Regional (Telugu/Hindi) and colloquial synonyms to catalog concepts
    SYNONYM_MAP = {
        "pesara pappu": "moong dal",
        "kandi pappu": "toor dal",
        "senaga pappu": "chana dal",
        "minapa pappu": "urad dal",
        "biyyam pindi": "rice flour",
        "chawal atta": "rice flour",
        "munagakaya": "drumstick",
        "nimmakaya": "lemon",
        "nimbu": "lemon",
        "bellam": "jaggery",
        "gud": "jaggery",
        "lehsun": "garlic",
        "vellulli": "garlic",
        "tamatar": "tomato",
        "tamata": "tomato",
        "aloo": "potato",
        "bangaladumpa": "potato",
        "pyaz": "onion",
        "ullipaya": "onion",
        "dahi": "curd",
        "perugu": "curd",
        "venna": "butter",
        "makhan": "butter",
        "paalu": "milk",
        "doodh": "milk",
        "gede paalu": "buffalo milk",
        "kothmir": "coriander",
        "kothimira": "coriander",
        "mirchi": "chilli",
        "pachi mirchi": "green chilli",
        "neyyi": "ghee",
        "poha": "poha",
        "atukulu": "poha",
        "sooji": "rava",
        "bombay rava": "bombay rava",
        "idly rava": "idli rava",
        "idly": "idli",
        "mawa": "khoa",
        "khoya": "khoa",
        "red lentils": "masoor dal",
        "green gram": "moong dal",
        "pigeon pea": "toor dal",
        "refined oil": "sunflower oil",
        "cooking oil": "oil",
        "biskut": "biscuits",
        "biscuit": "biscuits",
        "biscut": "biscuits",
        "panner": "paneer",
        "chocolaate": "chocolate",
        "choclate": "chocolate",
        "tonned": "toned",
        "turmaric": "turmeric",
        "corriander": "coriander",
        "ltrime": "lime"
    }

    def __init__(self, catalog_path="thelawala-search-data/catalog.csv",
                 inventory_path="thelawala-search-data/inventory.csv",
                 search_log_path="thelawala-search-data/search_log.jsonl"):
        self.catalog_path = catalog_path
        self.inventory_path = inventory_path
        self.search_log_path = search_log_path
        
        self.products = {}          # sku_id -> product dict
        self.inventory = {}         # sku_id -> inventory dict
        self.brands = set()         # all catalog brands
        self.categories = set()     # all catalog categories
        
        # Behavioral data from search logs
        self.query_to_sku_clicks = defaultdict(Counter) # normalized_query -> {sku_id: weight}
        self.sku_overall_popularity = Counter()         # sku_id -> total_engagement
        
        # Inverted index / vocab for fast local search
        self.doc_tokens = {}        # sku_id -> list of tokens
        self.inverted_index = defaultdict(set) # token -> set of sku_ids
        self.doc_lengths = {}
        self.avg_doc_len = 0
        self.idf = {}
        
        self._load_data()
        self._build_index()

    def _normalize_price(self, price_str, supplier, name):
        """
        Fix price anomalies in catalog:
        - metro_feed (MF...) prices are in paise (e.g. 6200 paise = Rs 62.00)
        - certain produce items entered as paise (e.g. 22264 for 1kg apples, 1012 for 250g lemon)
        """
        try:
            p = float(price_str)
        except ValueError:
            return 0.0
            
        if supplier == "metro_feed":
            return round(p / 100.0, 2)
            
        # Large prices on fresh produce (apples, lemons) in paise
        name_lower = name.lower()
        if p > 1000 and any(k in name_lower for k in ["apple", "lemon", "lime"]):
            return round(p / 100.0, 2)
            
        return round(p, 2)

    def _normalize_text(self, text):
        if not text:
            return ""
        t = text.lower()
        t = re.sub(r"[_\-\/&,\(\)\.\+]", " ", t)
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    def _tokenize(self, text):
        norm = self._normalize_text(text)
        return [t for t in norm.split() if len(t) > 0]

    def _load_data(self):
        # 1. Load Inventory
        try:
            with open(self.inventory_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sku = row["sku_id"].strip()
                    self.inventory[sku] = {
                        "stock_qty": int(row.get("stock_qty", 0)),
                        "status": row.get("status", "active").strip().lower(),
                        "restock_eta": row.get("restock_eta", "").strip(),
                        "updated_at": row.get("updated_at", "").strip()
                    }
        except FileNotFoundError:
            pass

        # 2. Load Catalog
        with open(self.catalog_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row["sku_id"].strip()
                name = row.get("name", "").strip()
                brand = row.get("brand", "").strip()
                cat = row.get("category", "").strip()
                supplier = row.get("supplier", "").strip()
                raw_price = row.get("price", "0").strip()
                normalized_price = self._normalize_price(raw_price, supplier, name)
                
                inv = self.inventory.get(sku, {"stock_qty": 0, "status": "active", "restock_eta": ""})
                
                self.products[sku] = {
                    "sku_id": sku,
                    "name": name,
                    "brand": brand,
                    "category": cat,
                    "size": row.get("size", "").strip(),
                    "raw_price": raw_price,
                    "price": normalized_price,
                    "supplier": supplier,
                    "description": row.get("description", "").strip(),
                    "stock_qty": inv["stock_qty"],
                    "status": inv["status"],
                    "restock_eta": inv["restock_eta"],
                    "is_in_stock": (inv["status"] == "active" and inv["stock_qty"] > 0)
                }
                
                if brand:
                    self.brands.add(brand.lower())
                if cat:
                    self.categories.add(cat.lower())

        # 3. Mine Search Log for Behavioral Signals & Synonyms
        try:
            with open(self.search_log_path, mode="r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    q = self._normalize_text(data.get("query", ""))
                    events = data.get("events", [])
                    for ev in events:
                        sku = ev.get("sku_id")
                        if not sku or sku not in self.products:
                            continue
                        action = ev.get("action")
                        weight = 2.0 if action == "add_to_cart" else 1.0
                        self.query_to_sku_clicks[q][sku] += weight
                        self.sku_overall_popularity[sku] += weight
        except FileNotFoundError:
            pass

    def _build_index(self):
        N = len(self.products)
        total_len = 0
        df = Counter()

        for sku, p in self.products.items():
            name_tokens = self._tokenize(p["name"])
            brand_tokens = self._tokenize(p["brand"])
            cat_tokens = self._tokenize(p["category"])
            desc_tokens = self._tokenize(p["description"])
            
            # Weighted field representation
            combined = name_tokens * 4 + brand_tokens * 3 + cat_tokens * 2 + desc_tokens
            self.doc_tokens[sku] = combined
            total_len += len(combined)
            
            for t in set(combined):
                df[t] += 1
                self.inverted_index[t].add(sku)
                
        self.avg_doc_len = total_len / max(1, N)
        for t, freq in df.items():
            self.idf[t] = math.log(1 + (N - freq + 0.5) / (freq + 0.5))

    def _parse_query_intent(self, raw_query):
        clean_q = raw_query.strip()
        max_price = None
        
        # 1. Price budget regex extraction
        price_match = re.search(r"(?:under|below|less than|<=|<)\s*(?:rs\.?|inr|₹)?\s*(\d+)", clean_q, re.IGNORECASE)
        if not price_match:
            price_match = re.search(r"(?:rs\.?|inr|₹)?\s*(\d+)\s*(?:rs|rupees)?\s*(?:under|below)", clean_q, re.IGNORECASE)
            
        if price_match:
            try:
                max_price = float(price_match.group(1))
                clean_q = re.sub(price_match.group(0), "", clean_q, flags=re.IGNORECASE).strip()
            except ValueError:
                pass

        normalized_query = self._normalize_text(clean_q)
        
        # 2. Regional / Colloquial Synonym Mapping
        expanded_query = normalized_query
        for syn, canon in self.SYNONYM_MAP.items():
            if syn in expanded_query:
                expanded_query = re.sub(r"\b" + re.escape(syn) + r"\b", canon, expanded_query)

        q_tokens = self._tokenize(expanded_query)

        # 3. Detect Brand Intent
        # If user explicitly searched for a known brand, protect it (Kavya's rule)
        matched_brand = None
        for brand_key, brand_canon in self.DISTINCTIVE_BRANDS.items():
            if re.search(r"\b" + re.escape(brand_key) + r"\b", normalized_query):
                matched_brand = brand_canon
                break

        # 4. Detect Intent Hierarchy (e.g. liquid milk vs milk chocolate vs milk powder)
        is_chocolate_intent = any(w in normalized_query for w in ["chocolate", "chocolaate", "choclate", "choco", "candy"])
        is_powder_intent = any(w in normalized_query for w in ["powder", "pwdr"])
        is_biscuit_intent = any(w in normalized_query for w in ["biscuit", "biscuits", "cookie", "rusk"])
        is_hair_oil_intent = "hair oil" in normalized_query

        return {
            "original_query": raw_query,
            "search_query": clean_q,
            "normalized_query": normalized_query,
            "expanded_query": expanded_query,
            "query_tokens": q_tokens,
            "max_price": max_price,
            "matched_brand": matched_brand,
            "is_chocolate_intent": is_chocolate_intent,
            "is_powder_intent": is_powder_intent,
            "is_biscuit_intent": is_biscuit_intent,
            "is_hair_oil_intent": is_hair_oil_intent
        }

    def _bm25_score(self, query_tokens, sku):
        doc = self.doc_tokens.get(sku, [])
        doc_len = len(doc)
        if doc_len == 0:
            return 0.0
            
        doc_counts = Counter(doc)
        k1 = 1.5
        b = 0.75
        score = 0.0
        
        for q_tok in query_tokens:
            if q_tok in doc_counts:
                tf = doc_counts[q_tok]
                idf = self.idf.get(q_tok, 1.0)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
                score += idf * (numerator / denominator)
                
        return score

    def _fuzzy_token_score(self, q_tok, doc_tokens):
        import difflib
        best_ratio = 0.0
        for dt in doc_tokens:
            if dt == q_tok:
                return 1.0
            if abs(len(dt) - len(q_tok)) <= 2 and len(q_tok) >= 4:
                ratio = difflib.SequenceMatcher(None, q_tok, dt).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
        return best_ratio if best_ratio >= 0.8 else 0.0

    def search(self, query_string, top_k=10):
        if not query_string or not query_string.strip():
            return []

        intent = self._parse_query_intent(query_string)
        q_norm = intent["normalized_query"]
        q_exp = intent["expanded_query"]
        q_tokens = intent["query_tokens"]
        max_price = intent["max_price"]
        target_brand = intent["matched_brand"]

        scores = {}

        # 1. Direct Behavioral Lookups from Historical Search Log
        # If past users searched this and clicked something, that's ground-truth evidence
        historical_clicks = Counter()
        for q_key in [q_norm, q_exp]:
            if q_key in self.query_to_sku_clicks:
                historical_clicks.update(self.query_to_sku_clicks[q_key])

        # If zero exact behavioral clicks, try fuzzy matching against historical queries
        if not historical_clicks:
            for past_q, past_clicks in self.query_to_sku_clicks.items():
                if q_norm and (q_norm in past_q or past_q in q_norm):
                    for sku, c in past_clicks.items():
                        historical_clicks[sku] += c * 0.5

        # 2. Score Candidates
        for sku, p in self.products.items():
            bm25 = self._bm25_score(q_tokens, sku)
            
            # Fuzzy typo matching
            fuzzy_boost = 0.0
            p_name_tokens = self._tokenize(p["name"])
            for qt in q_tokens:
                if len(qt) >= 4 and qt not in self.doc_tokens[sku]:
                    f_ratio = self._fuzzy_token_score(qt, p_name_tokens)
                    if f_ratio > 0.8:
                        fuzzy_boost += f_ratio * 4.0

            # Historical behavioral boost
            hist_clicks = historical_clicks.get(sku, 0)
            behavior_score = math.log1p(hist_clicks) * 10.0
            
            # Overall popularity
            pop_score = math.log1p(self.sku_overall_popularity.get(sku, 0)) * 0.4

            # Exact phrase match in product name
            name_norm = self._normalize_text(p["name"])
            exact_phrase_bonus = 0.0
            if (q_norm and q_norm in name_norm) or (q_exp and q_exp in name_norm):
                exact_phrase_bonus = 12.0
                if name_norm.startswith(q_norm) or name_norm.startswith(q_exp):
                    exact_phrase_bonus += 6.0

            # --- Domain-Specific Semantic Hierarchy ---
            domain_bonus = 0.0
            
            # A. The "Milk" intent vs Milk Chocolate / Milk Powder
            if "milk" in q_tokens:
                if intent["is_chocolate_intent"]:
                    if "chocolate" in name_norm or p["category"] == "Bakery & Snacks":
                        domain_bonus += 12.0
                    else:
                        domain_bonus -= 10.0
                elif intent["is_powder_intent"]:
                    if "powder" in name_norm or "pwdr" in name_norm:
                        domain_bonus += 12.0
                    else:
                        domain_bonus -= 8.0
                elif intent["is_biscuit_intent"]:
                    if p["category"] == "Bakery & Snacks":
                        domain_bonus += 10.0
                else:
                    # User searched pure "milk" (or "godavari milk", "toned milk")
                    # Boost pure liquid milk in Dairy & Eggs
                    if p["category"] == "Dairy & Eggs" and ("milk" in name_norm and "powder" not in name_norm and "pwdr" not in name_norm):
                        domain_bonus += 15.0
                    elif "chocolate" in name_norm or "biscuit" in name_norm or "rusk" in name_norm:
                        domain_bonus -= 15.0 # Strongly suppress milk chocolate/rusks for "milk"

            # B. Hair Oil vs Cooking Oil
            if "oil" in q_tokens:
                if intent["is_hair_oil_intent"]:
                    if p["category"] == "Personal Care" or "hair oil" in name_norm:
                        domain_bonus += 12.0
                    else:
                        domain_bonus -= 10.0
                else:
                    if p["category"] == "Oils & Ghee":
                        domain_bonus += 10.0
                    elif "hair oil" in name_norm or p["category"] == "Personal Care":
                        domain_bonus -= 10.0 # Strongly suppress hair oil for "oil"

            base_score = bm25 + fuzzy_boost + behavior_score + exact_phrase_bonus + domain_bonus
            
            # Skip irrelevant products
            if base_score <= 0.5 and hist_clicks == 0:
                continue

            total_score = base_score + pop_score

            # --- Business & Policy Rules ---
            
            # 1. Brand Intent vs House Label Rule (Kavya vs Farah)
            # "Customer first, margin second. If someone searches for a brand, show that brand."
            p_brand_norm = p["brand"].lower()
            if target_brand:
                if target_brand in p_brand_norm or p_brand_norm in target_brand:
                    total_score *= 3.0 # Strong boost to the requested brand
                elif p_brand_norm == "thela select":
                    total_score *= 0.3 # Demote house brand on explicit competitor searches
            else:
                # Generic query: boost high-margin house label Thela Select (Farah)
                if p_brand_norm == "thela select":
                    total_score *= 1.3

            # 2. Natural Language Budget Filter ("under 200")
            if max_price is not None:
                if p["price"] <= max_price:
                    total_score *= 2.5 # In budget boost
                else:
                    total_score *= 0.05 # Over budget steep penalty

            # 3. Inventory & Stock Availability (Sandeep vs Farah)
            # Deliverable items come first.
            # Out of stock items are heavily demoted to the bottom of the list.
            if p["status"] == "discontinued":
                total_score *= 0.01
            elif not p["is_in_stock"]:
                total_score *= 0.05

            scores[sku] = total_score

        # Sort candidate SKUs by final score
        ranked_skus = sorted(scores.keys(), key=lambda s: scores[s], reverse=True)
        return ranked_skus[:top_k]

if __name__ == "__main__":
    engine = ThelawalaSearchEngine()
    test_queries = [
        "milk",
        "godavari milk",
        "MILK CHOCOLAATE",
        "oil under 200",
        "hair oil",
        "pesara pappu",
        "venna",
        "paalu",
        "doodh",
        "chips under 20",
        "white bread",
        "ghee under 500"
    ]
    
    print("\n===============================")
    print("THELAWALA SEARCH ENGINE RESULTS")
    print("===============================")
    for tq in test_queries:
        res = engine.search(tq, top_k=5)
        print(f"\nQuery: '{tq}'")
        for i, sku in enumerate(res, 1):
            p = engine.products[sku]
            stock_tag = "IN STOCK" if p["is_in_stock"] else f"OUT OF STOCK ({p['status']})"
            print(f"  {i}. [{sku}] {p['name']} | Rs {p['price']} | Brand: {p['brand']} | {stock_tag}")
