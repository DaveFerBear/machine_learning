CUSTOMERS = {
    "C001": {"name": "Alice Chen", "email": "alice@example.com", "tier": "gold"},
    "C002": {"name": "Bob Patel", "email": "bob@example.com", "tier": "standard"},
    "C003": {"name": "Cleo Ortiz", "email": "cleo@example.com", "tier": "standard"},
}

ORDERS = {
    "O1001": {
        "customer_id": "C001",
        "item": "Wireless headphones",
        "amount": 199.00,
        "status": "delivered",
        "ordered_days_ago": 12,
        "refunded": False,
    },
    "O1002": {
        "customer_id": "C002",
        "item": "Standing desk",
        "amount": 450.00,
        "status": "delivered",
        "ordered_days_ago": 45,
        "refunded": False,
    },
    "O1003": {
        "customer_id": "C003",
        "item": "Coffee subscription",
        "amount": 35.00,
        "status": "shipped",
        "ordered_days_ago": 3,
        "refunded": False,
    },
}

REFUND_WINDOW_DAYS = 30
