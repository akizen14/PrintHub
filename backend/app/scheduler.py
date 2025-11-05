from typing import Dict, Any
import time


def normalize_priority(order):
    """Ensure priorityIndex is always an integer"""
    try:
        order["priorityIndex"] = int(order["priorityIndex"])
    except:
        order["priorityIndex"] = int(order.get("createdAt", time.time()))
    return order


def classify_queue(order: Dict[str, Any], thresholds: Dict[str, Any]) -> str:
    """
    Classify order into queue type based on pickup time and page count.
    - urgent: pickupTime within 60 minutes
    - normal: pages <= smallPages threshold (default 15)
    - bulk: large jobs
    """
    now = int(time.time())
    
    # Check if urgent (pickup within 60 minutes)
    if order.get("pickupTime"):
        pickup_time = order["pickupTime"]
        if pickup_time - now <= 3600:  # 60 minutes in seconds
            return "urgent"
    
    # Check if normal (small job)
    pages = order.get("pages", 0)
    small_pages = thresholds.get("smallPages", 15)
    
    if pages <= small_pages:
        return "normal"
    
    # Otherwise bulk
    return "bulk"


def priority_score(order: Dict[str, Any], now: int, thresholds: Dict[str, Any]) -> float:
    """
    Calculate priority score (used as a hint, actual ordering by priorityIndex).
    score = 5*urgency + 3*(1/pages) + 2*agingBoost + 8*manualBoost
    """
    score = 0.0
    
    # Urgency component
    queue_type = order.get("queueType", "normal")
    if queue_type == "urgent":
        score += 5.0
    
    # Job size component (inverse of pages)
    pages = order.get("pages", 1)
    score += 3.0 * (1.0 / max(pages, 1))
    
    # Aging component
    created_at = order.get("createdAt", now)
    age_minutes = (now - created_at) / 60
    aging_threshold = thresholds.get("agingMinutes", 12)
    if age_minutes > aging_threshold:
        aging_boost = min((age_minutes - aging_threshold) / aging_threshold, 1.0)
        score += 2.0 * aging_boost
    
    # Manual boost is implicit in priorityIndex changes
    # We don't add it here since priorityIndex is the primary sort key
    
    return score


def apply_aging(order: Dict[str, Any], thresholds: Dict[str, Any], now: int) -> Dict[str, Any]:
    """
    Apply aging boost to order if it's been waiting too long.
    This updates the priorityScore but not priorityIndex.
    """
    order["priorityScore"] = priority_score(order, now, thresholds)
    return order


def reindex_queue(orders: list, queue_type: str) -> list:
    """
    Reindex orders in a queue to avoid collisions.
    Assigns priorityIndex in steps of 1000.
    """
    queue_orders = [o for o in orders if o.get("queueType") == queue_type]
    
    # Sort according to queue rules
    if queue_type == "urgent":
        queue_orders.sort(key=lambda x: x.get("priorityIndex", 0))
    elif queue_type == "normal":
        # SJF: sort by pages, then priorityIndex
        queue_orders.sort(key=lambda x: (x.get("pages", 0), x.get("priorityIndex", 0)))
    else:  # bulk
        # FCFS: sort by priorityIndex
        queue_orders.sort(key=lambda x: x.get("priorityIndex", 0))
    
    # Reassign priorityIndex in steps of 1000
    for i, order in enumerate(queue_orders):
        order["priorityIndex"] = (i + 1) * 1000
    
    return queue_orders
