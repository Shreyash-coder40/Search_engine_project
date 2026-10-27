#!/usr/bin/env python3
"""
Batch Search Runner for Thelawala Search Engine.

Usage:
    python batch_search.py <queries_file> [output_file]

Example:
    python batch_search.py queries.txt results.jsonl

Reads a plain text file containing one search query per line.
Writes a JSON Lines (JSONL) file with schema:
    {"query": "...", "results": ["sku_id", "sku_id", ...]}
where 'results' holds up to 10 sku_ids ordered best first.
"""

import sys
import os
import json
from search_engine import ThelawalaSearchEngine

def run_batch_search(queries_file, output_file="results.jsonl"):
    if not os.path.exists(queries_file):
        print(f"Error: Query file '{queries_file}' not found.")
        sys.exit(1)

    print(f"Initializing Thelawala Search Engine...")
    engine = ThelawalaSearchEngine()
    print(f"Loaded {len(engine.products)} catalog products.")

    print(f"Reading queries from '{queries_file}'...")
    with open(queries_file, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    print(f"Processing {len(queries)} queries...")
    with open(output_file, "w", encoding="utf-8") as out_f:
        for q in queries:
            results = engine.search(q, top_k=10)
            record = {
                "query": q,
                "results": results
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Batch search complete. Results saved to '{output_file}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_search.py <queries_file> [output_file]")
        print("Example: python batch_search.py queries.txt results.jsonl")
        sys.exit(1)

    q_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else "results.jsonl"
    run_batch_search(q_file, out_file)
