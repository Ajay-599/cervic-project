import sys
import unittest
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import detect_intent

class TestPlaceOrder(unittest.TestCase):
    def test_buy_headphones(self):
        result = detect_intent("I want to buy headphones")
        self.assertEqual(result["intent"], "place_order")
        
    def test_order_phone(self):
        result = detect_intent("order a phone")
        self.assertEqual(result["intent"], "place_order")

if __name__ == "__main__":
    unittest.main()
