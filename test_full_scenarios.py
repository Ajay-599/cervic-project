import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def print_convo(title, dialogue):
    print(f"\n{'='*50}")
    print(f"SCENARIO: {title}")
    print(f"{'='*50}")
    ctx = create_context()
    for user_msg in dialogue:
        print(f"\nUser: {user_msg}")
        bot_response = get_bot_response(user_msg, ctx)
        print(f"Bot:\n{bot_response}")
    return ctx

def run_all_tests():
    # 1. "I want to buy headphones"
    print_convo("1. Buy Headphones directly", [
        "I want to buy headphones",
        "2",
        "yes"
    ])
    
    # 2. "order something" (disambiguation)
    print_convo("2. Order Something (Missing product initially)", [
        "order something",
        "4", # select "Place order"
        "Phone",
        "1",
        "yes"
    ])
    
    # 3. Invalid product
    print_convo("3. Invalid Product handling", [
        "I want to buy",
        "shoes",
        "p2",
        "1",
        "no" # test cancelling at the end
    ])
    
    # 4. Cancel midway
    print_convo("4. Cancel mid-way through ordering", [
        "I want to buy headphones",
        "nevermind"
    ])
    
    # 5. Context-based ("order it")
    print(f"\n{'='*50}")
    print(f"SCENARIO: 5. Context-based ('order it')")
    print(f"{'='*50}")
    ctx = create_context()
    ctx["product_id"] = "p3" # Phone was selected in earlier small talk
    print("\n[Context: User was previously looking at 'Phone' (p3)]")
    
    print("\nUser: I want to buy it")
    bot_response = get_bot_response("I want to buy it", ctx)
    print(f"Bot:\n{bot_response}")
    
    print("\nUser: Just 1")
    bot_response = get_bot_response("Just 1", ctx)
    print(f"Bot:\n{bot_response}")

    print("\nUser: yes")
    bot_response = get_bot_response("yes", ctx)
    print(f"Bot:\n{bot_response}")

if __name__ == "__main__":
    run_all_tests()
