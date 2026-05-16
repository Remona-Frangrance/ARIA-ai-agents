"""
Spending Anomaly Detector
Uses statistical methods (Z-score based) to detect unusual spending patterns.
No pre-training needed — works on the user's own transaction history.
"""

import math
from collections import defaultdict
from datetime import date, timedelta


def detect_anomalies(transactions, threshold=2.0):
    """
    Detect spending anomalies using Z-score on daily category spending.
    
    Args:
        transactions: List of transaction dicts
        threshold: Z-score threshold (default 2.0 = ~95th percentile)
    
    Returns:
        List of anomaly alerts
    """
    if not transactions:
        return []

    # Group daily spending by category
    category_daily = defaultdict(lambda: defaultdict(float))
    for tx in transactions:
        if tx.get("type") != "expense":
            continue
        cat = tx.get("category", "Other")
        tx_date = tx.get("date", "")
        category_daily[cat][tx_date] += tx.get("amount", 0)

    anomalies = []

    for category, daily_amounts in category_daily.items():
        values = list(daily_amounts.values())
        if len(values) < 5:
            continue  # Need enough data points

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance) if variance > 0 else 1

        for tx_date, amount in daily_amounts.items():
            z_score = (amount - mean) / std_dev if std_dev > 0 else 0

            if z_score > threshold:
                anomalies.append({
                    "date": tx_date,
                    "category": category,
                    "amount": amount,
                    "average": round(mean, 2),
                    "z_score": round(z_score, 2),
                    "multiplier": round(amount / mean, 1) if mean > 0 else 0,
                    "message": f"₹{amount:,.0f} on {category} — that's {amount / mean:.1f}x your daily average!"
                })

    # Sort by z_score descending (most unusual first)
    anomalies.sort(key=lambda x: x["z_score"], reverse=True)
    return anomalies[:10]  # Top 10 anomalies


def get_spending_health_score(transactions, budgets=None):
    """
    Calculate an overall spending health score (0-100).
    Higher is better (more disciplined spending).
    """
    if not transactions:
        return {"score": 50, "grade": "N/A", "factors": []}

    expenses = [tx for tx in transactions if tx.get("type") == "expense"]
    if not expenses:
        return {"score": 100, "grade": "A+", "factors": ["No expenses recorded"]}

    factors = []
    score = 100

    # Factor 1: Anomaly frequency (fewer anomalies = better)
    anomalies = detect_anomalies(transactions)
    if len(anomalies) > 5:
        score -= 20
        factors.append("Many spending anomalies detected")
    elif len(anomalies) > 2:
        score -= 10
        factors.append("Some unusual spending patterns")
    else:
        factors.append("Consistent spending patterns ✓")

    # Factor 2: Budget adherence
    if budgets:
        over_budget = sum(1 for b in budgets if b.get("percentage", 0) > 100)
        near_budget = sum(1 for b in budgets if 80 <= b.get("percentage", 0) <= 100)
        if over_budget > 0:
            score -= over_budget * 10
            factors.append(f"{over_budget} categories over budget")
        if near_budget > 0:
            score -= near_budget * 3
            factors.append(f"{near_budget} categories near budget limit")
        if over_budget == 0 and near_budget == 0:
            factors.append("All budgets under control ✓")

    # Factor 3: Spending diversity (not blowing money on one category)
    category_totals = defaultdict(float)
    total_expense = 0
    for tx in expenses:
        category_totals[tx.get("category", "Other")] += tx.get("amount", 0)
        total_expense += tx.get("amount", 0)

    if total_expense > 0:
        max_category_pct = max(v / total_expense for v in category_totals.values()) * 100
        if max_category_pct > 50:
            score -= 10
            factors.append("Spending too concentrated in one category")

    # Clamp score
    score = max(0, min(100, score))

    grade = "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C" if score >= 60 else "D" if score >= 50 else "F"

    return {"score": score, "grade": grade, "factors": factors}
