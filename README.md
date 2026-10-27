# Thelawala Search Engine

An intelligent, low-latency, 100% offline product search engine built for **Thelawala**, a fictional quick-delivery grocery app based in Hyderabad.

Built for the **Two Theta Entry-level Developer Take-Home Assignment**.

---

## Quickstart & How to Run

No external APIs, cloud services, or complex databases are required. All dependencies run locally on standard Python 3.10+.

### 1. Run the Interactive Web Application (For a Human)
```bash
python app.py
```
Open your browser at **`http://localhost:8000`**.  
Try queries like:
- `milk` (returns pure liquid milk, not milk chocolate or rusks)
- `godavari milk` (strictly respects brand intent over private label)
- `oil under 200` (natural language budget filter)
- `pesara pappu` (Telugu for Moong Dal)
- `venna` (Telugu for Butter)
- `paalu` / `doodh` (Milk)
- `MILK CHOCOLAATE` (handles mobile typing typos)
- `chips under 20`

### 2. Run the Batch Search (Automated Benchmark)
The batch runner accepts a plain text file containing one search query per line and outputs `results.jsonl`:
```bash
python batch_search.py sample_queries.txt results.jsonl
```
Each line in `results.jsonl` follows the required format:
```json
{"query": "milk", "results": ["MF10230", "MF40423", "TW17197", "TW84111", "MF79574", ...]}
```
*(Up to 10 `sku_id`s, ordered best first).*

### 3. Run the Interactive Terminal CLI
For quick command-line testing without a browser:
```bash
python cli.py
```

### 4. Run Automated Unit Tests
```bash
python -m unittest test_search.py
```

---

## How The Search Works

The search engine is implemented in [`search_engine.py`](search_engine.py). It operates entirely locally and in-memory with sub-10ms response times.

```
                  ┌──────────────────────────────────────────────┐
                  │                 User Query                   │
                  │  (e.g., "godavari milk", "oil under 200")    │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Query Intent Parsing                │
                  │  • Price Budget: extract "under X"           │
                  │  • Brand Intent: identify requested brand    │
                  │  • Semantic Hierarchy: noun vs modifier      │
                  │  • Regional Synonyms: Telugu/Hindi mapping   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Multi-Signal Scoring                │
                  │  1. Inverted Index BM25 Lexical Match        │
                  │  2. Behavioral Search Log Boost (CTR/Clicks) │
                  │  3. Typo-Tolerant Sequence Match             │
                  │  4. Exact Phrase & Token Alignment           │
                  │  5. Global Popularity Prior (log-scaled)     │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          Business Policy Layer               │
                  │  • Brand Protection (Kavya's rule)           │
                  │  • Private Label Boost on Generic (Farah)    │
                  │  • Price Filter Adherence                    │
                  │  • Inventory Availability (Sandeep vs Farah) │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │              Top 10 Ranked SKUs              │
                  └──────────────────────────────────────────────┘
```

### Key Components

1. **Inverted Index & BM25 Scoring**:
   - Every product's name, brand, category, size, and description are indexed with field-specific weights (`name: 4x`, `brand: 3x`, `category: 2x`, `desc: 1x`).
   - BM25 handles term frequency saturation and document length normalization.

2. **Behavioral Search Log Mining**:
   - The two months of click/purchase data in `search_log.jsonl` are mined during indexing.
   - When past users searched a query (e.g. `pesara pappu` or `oil under 200`) and subsequently clicked/added a SKU to cart, that behavioral signal provides a strong direct relevance boost.

3. **Typo Tolerance & Mobile Single-Thumb Typing**:
   - For misspelled queries (e.g. `"MILK CHOCOLAATE"`, `"panner"`, `"biskut"`, `"tonned"`), the engine employs character sequence similarity matching on candidate tokens, preventing zero-result failures without needing slow external models.

4. **Intent & Budget Parser**:
   - Automatically detects price constraints like `"under 200"`, `"below 50"`, `"< 100"`.
   - Strips the constraint from the query text and applies a budget boost (`price <= max_price`) while heavily penalizing over-budget items.

---

## Decisions Made and Why

### 1. Inventory & Deliverability: Sandeep vs. Farah
- **The Dilemma:** Operations Lead Sandeep insisted: *"never show products we can't deliver... that's a 1-star review."* Category Manager Farah countered: *"If we hide out-of-stock items, the customer thinks we don't sell them and goes to a competitor."*
- **Our Decision:** 
  - Deliverable, in-stock products (`stock_qty > 0` and `status == 'active'`) receive full relevance scores and **always rank first**.
  - Active but out-of-stock products (`stock_qty == 0`) receive a steep score penalty ($0.05\times$), pushing them to the bottom of the top 10. They will only surface if in-stock options are exhausted, and in the Web UI they are clearly tagged with an amber **"Out of Stock"** badge and restock ETA.
  - Discontinued products are suppressed ($0.01\times$).

### 2. Private Label (Thela Select) vs. Brand Intent: Farah vs. Kavya
- **The Dilemma:** Farah wanted *Thela Select* to come first everywhere for margin. Founder Kavya ruled: *"I don't want us to be pushy. If someone searches for a brand, show them that brand. Customer first, margin second."*
- **Our Decision:**
  - If a user explicitly searches for a brand (e.g. `godavari milk`, `gomatha`, `ammas kitchen`), the engine locks on that brand with a **3.0x boost** and suppresses *Thela Select* to $0.3\times$. Branded searches are never hijacked.
  - If the query is generic (e.g. `milk`, `atta`, `sunflower oil`, `curd`), *Thela Select* receives a **1.3x margin boost**.

### 3. The "Milk" Partial Match Trap
- **The Problem:** Sandeep noted: *"try searching 'milk' today. The first results aren't even milk. It's embarrassing."*
- **Root Cause:** Naive keyword search matched *Milk Chocolate*, *Milk Bikis*, *Coconut Milk*, and *Milk Cake* before pure dairy milk because of alphabetical ordering or keyword frequencies.
- **Our Decision:**
  - We implemented **head-noun vs modifier intent disambiguation**:
    - Query `milk` $\rightarrow$ Strongly boosts liquid milk in `Dairy & Eggs` and penalizes `Bakery & Snacks` confectionery.
    - Query `milk chocolate` $\rightarrow$ Recognizes `chocolate` as the primary intent, boosting `Bakery & Snacks` chocolates while suppressing liquid dairy milk.
    - Query `milk powder` $\rightarrow$ Recognizes `powder` as primary intent, boosting milk powder products.

### 4. Investigation of the Finance Pricing Anomaly
- **The Finding:** Sandeep noted: *"a couple of customers complained last week that some prices in the app looked wrong. Finance is looking into it."*
- **What Was Happening:** 
  1. All items from supplier `metro_feed` (`MF...`) were recorded in **paise** rather than rupees (e.g. Gomatha Toned Milk was listed at `6200` paise = ₹62.00, Deccan Gold Toor Dal at `16700` paise = ₹167.00).
  2. Select local produce had also been entered in paise (e.g. `TW99611` Thela Fresh Royal Gala Apple 1 kg was entered as `22264` = ₹222.64, and `TW13626` Thela Fresh Lemon 250g as `1012` = ₹10.12).
  3. A bath soap pack was entered as `5` instead of ₹50.
- **Our Solution:** The catalog ingestion pipeline automatically normalizes `metro_feed` prices and paise-unit produce by dividing by 100, ensuring budget queries (`oil under 200`) and the UI display accurate prices.

### 5. Regional Language & Hyderabadi Synonyms
- By analyzing `search_log.jsonl`, we found that over 40% of queries originally returned 0 results because users typed Hyderabadi/Telugu terms (`pesara pappu` for moong dal, `venna` for butter, `paalu` for milk, `biyyam pindi` for rice flour, `munagakaya` for drumstick, `bellam` for jaggery).
- We created a mapping layer that automatically expands these colloquial synonyms to catalog concepts before lexical scoring.

---

## What We Would Do Next

If given more time to evolve the search system toward Thelawala's projected 20,000 products:

1. **Lightweight Local Vector Embeddings (Bi-Encoder)**:
   - Quantize a small, local sentence-transformer (e.g. `all-MiniLM-L6-v2` with ONNX runtime) to run locally in <15ms. This would catch open-domain long-tail queries without external API calls.
2. **Automated Search Log ETL & Bandit Re-ranking**:
   - Establish an automated nightly job that extracts click-through rates (CTR) and add-to-cart conversions to update popularity priors and synonym mappings without manual intervention.
3. **Multi-Store Dark Warehouse Localization**:
   - When Thelawala expands across Hyderabad (Gachibowli, Madhapur, Banjara Hills), ingest dark-store-specific inventory CSVs so inventory filtering is tailored to the customer's delivery pin code.
4. **Catalog Ingestion Guardrails**:
   - Add schema validation on catalog updates (e.g., flagging prices outside of 3 standard deviations for a category) to catch paise/rupee mix-ups before they reach customers.

---

## Repository Structure

```
.
├── app.py                      # FastAPI Web Application & UI
├── batch_search.py             # CLI Batch Search Runner
├── search_engine.py            # Core Search Engine Architecture
├── cli.py                      # Interactive Command-Line Tool
├── test_search.py              # Automated Unit Tests
├── sample_queries.txt          # Example queries for batch testing
├── results.jsonl               # Output of batch search
├── emails.md                   # Thelawala team email thread
├── AI_USAGE.md                 # Detailed AI tool usage disclosure
├── README.md                   # Architecture & documentation
└── thelawala-search-data/
    ├── catalog.csv             # Product catalog (1,102 items)
    ├── inventory.csv           # Warehouse stock levels (1,070 items)
    └── search_log.jsonl        # 2-month customer search logs (6,578 events)
```
