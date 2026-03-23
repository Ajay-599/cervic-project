import sys
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_product_selection():
    ctx = create_context()
    
    # Trigger place order
    get_bot_response("I want to buy", ctx)
    
    # 1. Invalid input
    reply1 = get_bot_response("shoes", ctx)
    print("User: shoes")
    print("Bot:\n", reply1, "\n")
    assert "couldn't find that product" in reply1.lower()
    assert ctx["product_id"] is None
    
    # 2. Product name ("headphones")
    reply2 = get_bot_response("headphones", ctx)
    print("User: headphones")
    print("Bot:\n", reply2, "\n")
    assert ctx["product_id"] == "p1"
    
    # Reset for ID test
    ctx = create_context()
    get_bot_response("I want to buy", ctx)
    
    # 3. Product ID ("p2") -> laptop
    reply3 = get_bot_response("p2", ctx)
    print("User: p2")
    print("Bot:\n", reply3, "\n")
    assert ctx["product_id"] == "p2"

    print("All product selection tests passed!")

if __name__ == "__main__":
    test_product_selection()
