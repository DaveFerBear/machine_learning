from .data import CUSTOMERS, ORDERS, REFUND_WINDOW_DAYS

class ToolError(Exception):
    """Raised by tool implementations on user-facing failures.

    The agent loop catches these and returns them as ``is_error: true`` tool
    results so the model can recover instead of crashing.
    """

def get_order_status(order_id: str) -> dict:
    if order_id not in ORDERS:
        raise ToolError(f"No order found with id {order_id!r}.")
    o = ORDERS[order_id]
    return {
        "order_id": order_id,
        "item": o["item"],
        "status": o["status"],
        "ordered_days_ago": o["ordered_days_ago"],
        "amount": o["amount"],
        "refunded": o["refunded"],
    }


def get_customer(customer_id: str) -> dict:
    if customer_id not in CUSTOMERS:
        raise ToolError(f"No customer found with id {customer_id!r}.")
    return {"customer_id": customer_id, **CUSTOMERS[customer_id]}


def lookup_orders_by_customer(customer_id: str) -> dict:
    if customer_id not in CUSTOMERS:
        raise ToolError(f"No customer found with id {customer_id!r}.")
    order_ids = [oid for oid, o in ORDERS.items() if o["customer_id"] == customer_id]
    return {"customer_id": customer_id, "order_ids": order_ids}


def issue_refund(order_id: str, reason: str) -> dict:
    if order_id not in ORDERS:
        raise ToolError(f"No order found with id {order_id!r}.")
    o = ORDERS[order_id]
    if o["refunded"]:
        raise ToolError(f"Order {order_id} has already been refunded.")
    if o["ordered_days_ago"] > REFUND_WINDOW_DAYS:
        raise ToolError(
            f"Order {order_id} was placed {o['ordered_days_ago']} days ago, "
            f"which is outside the {REFUND_WINDOW_DAYS}-day refund window."
        )
    o["refunded"] = True
    return {
        "order_id": order_id,
        "refunded_amount": o["amount"],
        "reason": reason,
        "status": "refund_issued",
    }


def cancel_order(order_id: str) -> dict:
    if order_id not in ORDERS:
        raise ToolError(f"No order found with id {order_id!r}.")
    o = ORDERS[order_id]
    if o["status"] not in ("ordered", "shipped"):
        raise ToolError(
            f"Order {order_id} is in status {o['status']!r} and cannot be cancelled."
        )
    o["status"] = "cancelled"
    return {"order_id": order_id, "status": "cancelled"}


def escalate_to_human(summary: str) -> dict:
    return {"status": "escalated", "summary": summary}


TOOL_FUNCTIONS = {
    "get_order_status": get_order_status,
    "get_customer": get_customer,
    "lookup_orders_by_customer": lookup_orders_by_customer,
    "issue_refund": issue_refund,
    "cancel_order": cancel_order,
    "escalate_to_human": escalate_to_human,
}
