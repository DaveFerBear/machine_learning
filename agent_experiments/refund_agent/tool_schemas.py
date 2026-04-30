TOOL_SCHEMAS = [
    {
        "name": "get_order_status",
        "description": (
            "Look up the current status, age, amount, and refund state of a "
            "single order by its order id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order id, e.g. 'O1001'.",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_customer",
        "description": "Look up a customer's name, email, and tier by customer id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer id, e.g. 'C001'.",
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "lookup_orders_by_customer",
        "description": "List all order ids belonging to a given customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Issue a refund for an order. Fails if the order is already refunded "
            "or is outside the 30-day refund window. The order is mutated to "
            "refunded=True on success."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {
                    "type": "string",
                    "description": "Short user-facing reason for the refund.",
                },
            },
            "required": ["order_id", "reason"],
        },
    },
    {
        "name": "cancel_order",
        "description": (
            "Cancel an order. Only valid if the order has not yet been "
            "delivered (status must be 'ordered' or 'shipped')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Escalate to a human support agent when you cannot or should not "
            "handle the request yourself (e.g. policy violation, request beyond "
            "your tools, or repeated tool errors). Provide a short summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
            },
            "required": ["summary"],
        },
    },
]
