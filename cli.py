#!/usr/bin/env python3
"""
Interactive CLI for Thelawala Search Engine.

Allows team members to type any search query and see formatted results in terminal.
Usage:
    python cli.py
"""

from search_engine import ThelawalaSearchEngine

def main():
    print("=" * 60)
    print("      THELAWALA PRODUCT SEARCH (Interactive CLI)")
    print("=" * 60)
    print("Initializing search engine...")
    engine = ThelawalaSearchEngine()
    print(f"Index loaded: {len(engine.products)} items ready.\n")
    print("Type your query (or 'exit' to quit). Try things like:")
    print("  - 'milk'")
    print("  - 'godavari milk'")
    print("  - 'oil under 200'")
    print("  - 'pesara pappu'")
    print("  - 'venna'")
    print("-" * 60)

    while True:
        try:
            query = input("\nSearch > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Exiting. Bye!")
                break

            results = engine.search(query, top_k=10)
            if not results:
                print(f"No results found for '{query}'.")
                continue

            print(f"\nTop {len(results)} results for '{query}':")
            print("-" * 60)
            for i, sku in enumerate(results, 1):
                p = engine.products[sku]
                stock_tag = "[IN STOCK]" if p["is_in_stock"] else f"[OUT OF STOCK: {p['status'].upper()}]"
                brand_tag = f"({p['brand']})" if p['brand'] else ""
                print(f" {i:2d}. {sku} | Rs {p['price']:<7.2f} | {p['name']} {brand_tag} {stock_tag}")
            print("-" * 60)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Bye!")
            break

if __name__ == "__main__":
    main()
