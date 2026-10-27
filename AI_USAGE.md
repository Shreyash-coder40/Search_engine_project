# AI Usage Disclosure

In accordance with the assignment guidelines (*"AI: use AI coding tools and agents as much as you like. We expect you to."*), this document details how AI assistance was leveraged, the key instructions provided, the mistakes the AI made, and how they were detected and resolved.

---

## 1. How AI Tools Were Used

AI was used as an active pair programmer and data analysis assistant throughout the assignment:
- **Exploratory Data Analysis (EDA):** Writing quick Python analysis scripts to inspect schemas, record counts, null values, and distributions across `catalog.csv`, `inventory.csv`, and `search_log.jsonl`.
- **System Architecture & Algorithmic Design:** Formulating the hybrid ranking formula (BM25 + Behavioral search click mining + typo tolerance + category intent hierarchy).
- **Code Generation:** Authoring the modular Python classes (`search_engine.py`, `batch_search.py`, `cli.py`, `app.py`, and `test_search.py`).
- **Web UI Construction:** Building the responsive, modern FastAPI single-page search interface with vanilla CSS glassmorphism, instant debounced querying, and intent badges.
- **Test Generation:** Writing unit tests covering critical business constraints (milk vs chocolate, brand protection, budget queries, out-of-stock deprioritization).

---

## 2. Key Prompts and Instructions Given

1. **Deconstructing the Problem:**
   > *"Explain what I need to build in simple terms based on the assignment brief, team emails, and provided data files."*

2. **Analyzing the Team Emails & Clues:**
   > *"Analyze emails.md. What are the explicit and implicit technical constraints, business trade-offs (e.g. Kavya vs. Farah, Sandeep vs. Farah), and data anomalies mentioned by the team?"*

3. **Data Inspection & Behavioral Analysis:**
   > *"Write a script to analyze the search logs: find out what percentage of queries originally returned 0 results, what the most frequent zero-result queries were, and what products users clicked in those sessions."*

4. **Engine Implementation:**
   > *"Implement ThelawalaSearchEngine in Python that adheres to Arjun's constraints: 100% local, no external API calls at runtime, fast execution, automated re-indexing, with budget parsing (e.g., 'oil under 200'), brand protection, and stock-aware ranking."*

5. **Batch Runner & Verification:**
   > *"Build batch_search.py taking queries.txt and outputting results.jsonl with schema `{"query": "...", "results": ["sku_id", ...]}`, and create comprehensive unit tests."*

---

## 3. Where AI Got Things Wrong & How They Were Fixed

### Mistake 1: The "Milk Chocolate" False Penalty
- **What happened:** In attempting to solve Sandeep's complaint (*"try searching 'milk' today... the first results aren't even milk"*), the AI initially implemented a blanket rule: *if the query contains "milk", penalize any product with "chocolate" in its name by -6.0 points.*
- **Why it was wrong:** When a customer typed `"MILK CHOCOLAATE"` (a mobile typo), the search engine demoted the actual milk chocolate bars and recommended plain milk instead!
- **How it was discovered:** During manual testing of the test suite with the query `"MILK CHOCOLAATE"`, the top results were liquid milk cartons.
- **The Fix:** We refined the logic to distinguish **head-noun intent from modifier intent**. If the query explicitly mentions `"chocolate"` or `"chocolaate"`, chocolate becomes the primary intent and is boosted, while liquid dairy milk is suppressed. If the query is *only* `"milk"`, liquid milk is boosted and chocolate is suppressed.

---

### Mistake 2: Fragile Brand Detection on Multi-Word Names
- **What happened:** In implementing Kavya's rule (*"If someone searches for a brand, show them that brand"*), the AI checked if all tokens of the brand were present in the query (`all(bt in q_tokens for bt in brand_tokens)`).
- **Why it was wrong:** For the query `"godavari milk"`, the catalog brand name is `"Godavari Dairy"`. Because the word `"dairy"` was absent from the query, the AI failed to identify the brand intent and returned Gomatha milk before Godavari Dairy milk.
- **How it was discovered:** Running `python search_engine.py` on `"godavari milk"` showed `GOMATHA FULL CREAM MILK` as result #1 instead of Godavari Dairy.
- **The Fix:** We built a dictionary of distinctive brand root identifiers (e.g., `"godavari"` $\rightarrow$ `"godavari dairy"`, `"ammas"` $\rightarrow$ `"ammas kitchen"`, `"golconda"` $\rightarrow$ `"golconda grains"`), ensuring branded queries are recognized even if the user omits generic suffix words like "Dairy" or "Mills".

---

### Mistake 3: Windows Console Encoding Failures (UnicodeEncodeError)
- **What happened:** The AI added emojis (e.g., `🔍`) and printed raw Telugu/Hindi characters to standard output in CLI and test scripts.
- **Why it was wrong:** On Windows systems where the terminal default code page is `cp1252`, Python threw unhandled `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f50d'`.
- **How it was discovered:** Execution of `python search_engine.py` crashed immediately on Windows terminal output.
- **The Fix:** We removed Unicode non-ASCII emojis from console print statements, ensured all file I/O explicitly specifies `encoding="utf-8"`, and wrapped non-ASCII terminal representations in `ascii()` or safe formatting.

---

### Mistake 4: Missing the "Metro Feed" Pricing Scale
- **What happened:** The AI initially parsed all prices in `catalog.csv` as rupees directly.
- **Why it was wrong:** In `catalog.csv`, all items from supplier `metro_feed` have prices recorded in **paise** (e.g. `6200` for 1L milk, `16700` for 1kg toor dal). In addition, certain local farm items (apples at `22264`, lemons at `1012`) were also in paise. When querying `"oil under 200"`, the AI filtered out all Metro Feed cooking oils because their raw price was `16500` (> 200).
- **How it was discovered:** Correlating Sandeep's email note (*"customers complained last week that some prices in the app looked wrong. Finance is looking into it"*) with data exploration, we noticed `metro_feed` items had prices 100x higher than identical `thela_direct` items.
- **The Fix:** We added a price normalization layer during ingestion that scales `metro_feed` prices and paise-scale produce down by $\div 100$, resolving both the budget query filtering and the customer price confusion.

---

## 4. Summary of Human Judgment Applied
While AI generated code rapidly, human judgment was essential for:
1. Recognizing that the email thread contained intentional business conflicts (Sandeep vs. Farah, Kavya vs. Farah) that needed deliberate architectural decisions rather than simple syntax.
2. Spotting the Finance pricing anomaly in the raw CSV.
3. Defining the boundary between out-of-catalog search failures (e.g. `cigarette`, `phone recharge`) vs. colloquial Hyderabad grocery terms (`pesara pappu`, `venna`, `biyyam pindi`).
