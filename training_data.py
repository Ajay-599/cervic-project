import random

TRAINING_SCENARIOS = [
    {
        "intent": "greeting",
        "examples": [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "hiya"
        ],
        "responses": [
            "Hello! Welcome to Cervic Support 👋",
            "Hi there! How can I help you today?",
            "Greetings! Welcome to Cervic Support. 😊",
            "Hey! What can I assist you with today?"
        ]
    },
    {
        "intent": "track_order",
        "examples": [
            "track my order", "where is my order", "check order status", "track shipment", 
            "where's my package", "order tracking", "has my order shipped", "track", "status"
        ],
        "responses": [
            "Got it! Switching to tracking. Could you provide your order ID? 😊",
            "Understood. Let's track your order! What is the order ID? 📦",
            "Sure, I can track that for you now ✨ Please share the order ID."
        ]
    },
    {
        "intent": "cancel_order",
        "examples": [
            "cancel my order", "cancel order", "stop my order", "i want to cancel", 
            "cancel shipment", "cancel purchase", "abort order", "cancel"
        ],
        "responses": [
            "Got it! Switching to cancelling. Could you provide your order ID? 🛑",
            "Understood. Let's cancel your order. What is the order ID?",
            "I can help you cancel that. Please enter your order ID."
        ]
    },
    {
        "intent": "billing",
        "examples": [
            "check billing", "billing query", "billing issue", "invoice", "receipt", 
            "payment details", "billing information", "my bill", "billing"
        ],
        "responses": [
            "Switching to billing queries. Could you provide your order ID? 💳",
            "Let's look up your billing info. What is the order ID?",
            "I can check your payment details! Please share your order ID."
        ]
    },
    {
        "intent": "place_order",
        "examples": [
            "place order", "i want to buy", "get product", "order something", "purchase", "shopping", "buy"
        ],
        "responses": [
            "Let's get a new order started!"
        ]
    },
    {
        "intent": "small_talk",
        "examples": [
            "how are you", "who are you", "are you a bot", "what's your name", "tell me a joke",
            "what can you do", "help me", "you are awesome", "thanks", "thank you"
        ],
        "responses": [
            "I'm Cervic Support's AI assistant. I can help you with your orders and billing!",
            "I'm an AI chatbot here to make your life easier! How can I help?",
            "I am just a friendly bot! Ask me about your orders or let me help you purchase something. 😊",
            "You're very welcome! Let me know if you need anything else."
        ]
    },
    {
        "intent": "fallback",
        "examples": [],
        "responses": [
            "I'm still learning and not quite sure what you mean. Could you rephrase that?",
            "Hmm, I didn't quite catch that. Would you mind saying it differently?",
            "I'm sorry, I don't understand. Could you try explaining it another way?",
            "My apologies, I missed that. Can we try again?"
        ]
    }
]

def get_training_responses(intent_name: str) -> list:
    for scenario in TRAINING_SCENARIOS:
        if scenario["intent"] == intent_name and "responses" in scenario and scenario["responses"]:
            return scenario["responses"]
    return ["I am not sure how to respond to that."]
