#!/usr/bin/env python3
"""
FastAPI Web Application for Thelawala Product Search.

Provides a rich, human-friendly web interface for testing and exploring queries.
Run with:
    python app.py
or:
    uvicorn app:app --port 8000 --reload
"""

import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from search_engine import ThelawalaSearchEngine

app = FastAPI(title="Thelawala Product Search", version="1.0.0")

# Initialize Search Engine once on server start
engine = ThelawalaSearchEngine()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thelawala Search · Hyderabad Quick Commerce</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(22, 28, 45, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #10b981;
      --primary-glow: rgba(16, 185, 129, 0.25);
      --accent: #f59e0b;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --badge-oos: rgba(239, 68, 68, 0.15);
      --badge-oos-text: #f87171;
      --badge-stock: rgba(16, 185, 129, 0.15);
      --badge-stock-text: #34d399;
      --badge-thela: rgba(99, 102, 241, 0.18);
      --badge-thela-text: #818cf8;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    body {
      background-color: var(--bg);
      background-image: 
        radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.1) 0px, transparent 50%);
      color: var(--text);
      min-height: 100vh;
      padding: 2.5rem 1.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .container {
      width: 100%;
      max-width: 900px;
    }

    header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .logo-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.85rem;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 9999px;
      font-size: 0.82rem;
      color: var(--primary);
      font-weight: 600;
      margin-bottom: 0.8rem;
    }

    h1 {
      font-size: 2.5rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      color: var(--text-muted);
      font-size: 1rem;
      max-width: 580px;
      margin: 0 auto;
      line-height: 1.5;
    }

    .search-section {
      margin-bottom: 2rem;
      position: sticky;
      top: 1rem;
      z-index: 50;
    }

    .search-box {
      position: relative;
      display: flex;
      align-items: center;
    }

    .search-icon {
      position: absolute;
      left: 1.25rem;
      width: 1.25rem;
      height: 1.25rem;
      color: var(--text-muted);
      pointer-events: none;
    }

    input[type="text"] {
      width: 100%;
      padding: 1.15rem 1.25rem 1.15rem 3.25rem;
      font-size: 1.1rem;
      background: rgba(18, 24, 40, 0.85);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      color: var(--text);
      outline: none;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 0 0 1px var(--card-border);
      transition: all 0.2s ease;
    }

    input[type="text"]:focus {
      border-color: var(--primary);
      box-shadow: 0 10px 30px -5px var(--primary-glow), 0 0 0 2px var(--primary);
    }

    .suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.85rem;
      align-items: center;
    }

    .sugg-label {
      font-size: 0.78rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin-right: 0.25rem;
    }

    .pill {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #cbd5e1;
      padding: 0.3rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.82rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .pill:hover {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border-color: rgba(16, 185, 129, 0.3);
    }

    .intent-banner {
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.2);
      border-radius: 0.75rem;
      padding: 0.75rem 1rem;
      margin-bottom: 1.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
      font-size: 0.85rem;
    }

    .intent-tag {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.2rem 0.5rem;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 0.35rem;
      font-weight: 600;
      color: #e2e8f0;
    }

    .results-count {
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-bottom: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .results-grid {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    .product-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(10px);
      border-radius: 0.85rem;
      padding: 1.1rem 1.25rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .product-card:hover {
      border-color: rgba(255, 255, 255, 0.18);
      transform: translateY(-2px);
      box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.35);
    }

    .product-card.oos {
      opacity: 0.65;
      border-style: dashed;
    }

    .card-left {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      flex: 1;
    }

    .rank-number {
      font-size: 1.1rem;
      font-weight: 800;
      color: #475569;
      min-width: 1.5rem;
      padding-top: 0.1rem;
    }

    .card-info {
      flex: 1;
    }

    .item-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 0.3rem;
    }

    .product-name {
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
    }

    .thela-badge {
      background: var(--badge-thela);
      color: var(--badge-thela-text);
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.5rem;
      border-radius: 0.35rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }

    .item-meta {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-bottom: 0.35rem;
      flex-wrap: wrap;
    }

    .meta-brand {
      color: #e2e8f0;
      font-weight: 600;
    }

    .meta-sku {
      font-family: monospace;
      color: #64748b;
    }

    .card-right {
      text-align: right;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 0.4rem;
      min-width: 140px;
    }

    .price-tag {
      font-size: 1.35rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.02em;
    }

    .stock-pill {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }

    .stock-pill.in-stock {
      background: var(--badge-stock);
      color: var(--badge-stock-text);
    }

    .stock-pill.out-of-stock {
      background: var(--badge-oos);
      color: var(--badge-oos-text);
    }

    .empty-state {
      text-align: center;
      padding: 4rem 1rem;
      color: var(--text-muted);
    }

    .empty-icon {
      font-size: 3rem;
      margin-bottom: 1rem;
      opacity: 0.5;
    }
  </style>
</head>
<body>

  <div class="container">
    <header>
      <div class="logo-badge">⚡ THELAWALA SEARCH ENGINE</div>
      <h1>Hyderabad Grocery Search</h1>
      <p class="subtitle">Search 1,100+ local groceries with instant typo tolerance, regional synonyms, brand protection, and budget filtering.</p>
    </header>

    <div class="search-section">
      <div class="search-box">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
        <input type="text" id="searchInput" placeholder="Type here: 'milk', 'oil under 200', 'pesara pappu', 'godavari milk'..." autocomplete="off" autofocus>
      </div>

      <div class="suggestions">
        <span class="sugg-label">Try:</span>
        <button class="pill" onclick="runSearch('milk')">milk</button>
        <button class="pill" onclick="runSearch('godavari milk')">godavari milk</button>
        <button class="pill" onclick="runSearch('oil under 200')">oil under 200</button>
        <button class="pill" onclick="runSearch('pesara pappu')">pesara pappu (moong dal)</button>
        <button class="pill" onclick="runSearch('venna')">venna (butter)</button>
        <button class="pill" onclick="runSearch('MILK CHOCOLAATE')">MILK CHOCOLAATE</button>
        <button class="pill" onclick="runSearch('chips under 20')">chips under 20</button>
        <button class="pill" onclick="runSearch('atta under 300')">atta under 300</button>
      </div>
    </div>

    <div id="intentBanner" class="intent-banner" style="display: none;"></div>

    <div class="results-count">
      <span id="resultsHeader">Showing top products</span>
      <span id="searchTime" style="font-family: monospace; color: #64748b;"></span>
    </div>

    <div class="results-grid" id="resultsContainer">
      <div class="empty-state">
        <div class="empty-icon">🛒</div>
        <h3>Type a search query above</h3>
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">Test single-thumb mobile queries, regional terms, and price limits.</p>
      </div>
    </div>
  </div>

  <script>
    const searchInput = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('resultsContainer');
    const intentBanner = document.getElementById('intentBanner');
    const resultsHeader = document.getElementById('resultsHeader');
    const searchTime = document.getElementById('searchTime');

    let debounceTimer = null;

    function runSearch(query) {
      searchInput.value = query;
      performSearch(query);
    }

    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();
      if (!query) {
        resultsContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🛒</div>
            <h3>Type a search query above</h3>
            <p style="margin-top: 0.5rem; font-size: 0.9rem;">Test single-thumb mobile queries, regional terms, and price limits.</p>
          </div>
        `;
        intentBanner.style.display = 'none';
        resultsHeader.textContent = "Showing top products";
        searchTime.textContent = "";
        return;
      }
      debounceTimer = setTimeout(() => {
        performSearch(query);
      }, 120);
    });

    async function performSearch(query) {
      const startTime = performance.now();
      try {
        const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await resp.json();
        const duration = (performance.now() - startTime).toFixed(1);

        renderResults(data, duration);
      } catch (err) {
        console.error("Search error:", err);
      }
    }

    function renderResults(data, latencyMs) {
      const { query, intent, results } = data;
      searchTime.textContent = `${latencyMs}ms`;

      // Render Intent Banner
      const tags = [];
      if (intent.max_price !== null) {
        tags.push(`<span class="intent-tag">💰 Budget: &le; &#8377;${intent.max_price}</span>`);
      }
      if (intent.matched_brand) {
        tags.push(`<span class="intent-tag">🏷️ Brand Protected: ${intent.matched_brand.toUpperCase()}</span>`);
      }
      if (intent.expanded_query && intent.expanded_query !== intent.normalized_query) {
        tags.push(`<span class="intent-tag">🌐 Synonym: "${intent.normalized_query}" &rarr; "${intent.expanded_query}"</span>`);
      }

      if (tags.length > 0) {
        intentBanner.innerHTML = `<span style="color: var(--primary); font-weight: 700;">Parsed Query Intent:</span> ` + tags.join(' ');
        intentBanner.style.display = 'flex';
      } else {
        intentBanner.style.display = 'none';
      }

      if (results.length === 0) {
        resultsHeader.textContent = `0 results for "${query}"`;
        resultsContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>No products found</h3>
            <p style="margin-top: 0.5rem; font-size: 0.9rem;">We couldn't find items matching "${query}". Check spelling or try a broader term.</p>
          </div>
        `;
        return;
      }

      resultsHeader.textContent = `Top ${results.length} results for "${query}"`;

      resultsContainer.innerHTML = results.map((item, idx) => {
        const isHouse = item.brand.toLowerCase() === 'thela select';
        const houseBadge = isHouse ? `<span class="thela-badge">Thela Select</span>` : '';
        const oosClass = !item.is_in_stock ? 'oos' : '';
        const stockBadge = item.is_in_stock 
          ? `<span class="stock-pill in-stock">● In Stock (${item.stock_qty})</span>`
          : `<span class="stock-pill out-of-stock">○ Out of Stock ${item.restock_eta ? '(ETA: ' + item.restock_eta + ')' : ''}</span>`;

        return `
          <div class="product-card ${oosClass}">
            <div class="card-left">
              <div class="rank-number">#${idx + 1}</div>
              <div class="card-info">
                <div class="item-header">
                  <span class="product-name">${item.name}</span>
                  ${houseBadge}
                </div>
                <div class="item-meta">
                  <span class="meta-brand">${item.brand}</span>
                  <span>&bull;</span>
                  <span>${item.category}</span>
                  <span>&bull;</span>
                  <span>${item.size}</span>
                  <span>&bull;</span>
                  <span class="meta-sku">${item.sku_id}</span>
                </div>
              </div>
            </div>
            <div class="card-right">
              <div class="price-tag">&#8377;${item.price.toFixed(2)}</div>
              ${stockBadge}
            </div>
          </div>
        `;
      }).join('');
    }
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_CONTENT

@app.get("/api/search")
def api_search(q: str = Query(..., description="Search query")):
    intent = engine._parse_query_intent(q)
    top_sku_ids = engine.search(q, top_k=10)
    
    results = []
    for sku in top_sku_ids:
        p = engine.products.get(sku)
        if p:
            results.append({
                "sku_id": p["sku_id"],
                "name": p["name"],
                "brand": p["brand"],
                "category": p["category"],
                "size": p["size"],
                "price": p["price"],
                "raw_price": p["raw_price"],
                "supplier": p["supplier"],
                "is_in_stock": p["is_in_stock"],
                "stock_qty": p["stock_qty"],
                "status": p["status"],
                "restock_eta": p["restock_eta"]
            })
            
    return {
        "query": q,
        "intent": {
            "normalized_query": intent["normalized_query"],
            "expanded_query": intent["expanded_query"],
            "max_price": intent["max_price"],
            "matched_brand": intent["matched_brand"]
        },
        "count": len(results),
        "results": results
    }

if __name__ == "__main__":
    print("Starting Thelawala Web Server on http://127.0.0.1:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
