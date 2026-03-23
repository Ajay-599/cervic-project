import sys
import unittest
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import products, get_product_listing

class TestCatalog(unittest.TestCase):
    def test_products_exist(self):
        self.assertIn("p1", products)
        self.assertIn("p2", products)
        self.assertIn("p3", products)
        self.assertEqual(products["p1"]["name"], "Headphones")
        
    def test_listing_format(self):
        listing = get_product_listing()
        self.assertIn("Headphones: 1999", listing)
        self.assertIn("Laptop: 49999", listing)
        self.assertIn("Phone: 29999", listing)

if __name__ == "__main__":
    unittest.main()
