import unittest
from search_engine import ThelawalaSearchEngine

class TestThelawalaSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ThelawalaSearchEngine()

    def test_milk_query_returns_liquid_milk_first(self):
        """Sandeep's complaint: Searching 'milk' should return milk, not milk chocolate or rusks."""
        results = self.engine.search("milk", top_k=5)
        self.assertGreater(len(results), 0)
        
        # Verify top results are Dairy & Eggs and not chocolate
        for sku in results[:3]:
            p = self.engine.products[sku]
            self.assertEqual(p["category"], "Dairy & Eggs")
            self.assertIn("milk", p["name"].lower())
            self.assertNotIn("chocolate", p["name"].lower())

    def test_brand_protection_kavya_rule(self):
        """Kavya's rule: If someone searches for a brand, show that brand. Customer first, margin second."""
        results = self.engine.search("godavari milk", top_k=5)
        self.assertGreater(len(results), 0)
        top_product = self.engine.products[results[0]]
        self.assertEqual(top_product["brand"].lower(), "godavari dairy")
        self.assertIn("milk", top_product["name"].lower())

    def test_milk_chocolate_intent(self):
        """When user types 'MILK CHOCOLAATE' (typo), should return chocolate, not dairy milk."""
        results = self.engine.search("MILK CHOCOLAATE", top_k=5)
        self.assertGreater(len(results), 0)
        top_product = self.engine.products[results[0]]
        self.assertIn("chocolate", top_product["name"].lower())
        self.assertEqual(top_product["category"], "Bakery & Snacks")

    def test_price_constraint_oil_under_200(self):
        """Farah's request: 'oil under 200' should only return oils under Rs 200."""
        results = self.engine.search("oil under 200", top_k=5)
        self.assertGreater(len(results), 0)
        for sku in results:
            p = self.engine.products[sku]
            self.assertLessEqual(p["price"], 200.0)
            self.assertIn("oil", p["name"].lower())

    def test_regional_synonyms_telugu(self):
        """Colloquial Hyderabad Telugu queries should map to right products."""
        # 'pesara pappu' -> moong dal
        res_pesara = self.engine.search("pesara pappu", top_k=3)
        for sku in res_pesara:
            self.assertIn("moong dal", self.engine.products[sku]["name"].lower())

        # 'venna' -> butter
        res_venna = self.engine.search("venna", top_k=3)
        for sku in res_venna:
            self.assertIn("butter", self.engine.products[sku]["name"].lower())

        # 'paalu' -> milk
        res_paalu = self.engine.search("paalu", top_k=3)
        for sku in res_paalu:
            self.assertIn("milk", self.engine.products[sku]["name"].lower())

    def test_stock_priority_sandeep_vs_farah(self):
        """In-stock deliverable items must always rank before out-of-stock items."""
        results = self.engine.search("curd", top_k=10)
        self.assertGreater(len(results), 0)
        # Top 3 must be in stock if there are in-stock items
        for sku in results[:3]:
            self.assertTrue(self.engine.products[sku]["is_in_stock"])

    def test_chips_under_20(self):
        """Budget chips test: should return chips <= 20."""
        results = self.engine.search("chips under 20", top_k=5)
        self.assertGreater(len(results), 0)
        for sku in results:
            p = self.engine.products[sku]
            self.assertLessEqual(p["price"], 20.0)

if __name__ == "__main__":
    unittest.main()
