"""
Finance Agent — Analytics Engine
Calculates financial metrics, trends, and derived insights from transaction data.
"""

from datetime import date, timedelta
from agents.finance.database import (
    get_transactions, get_summary, get_category_breakdown,
    get_daily_spending, get_subscriptions, get_profile, get_budgets
)


def get_burn_rate():
    """Calculate how many days until money runs out at current spending rate."""
    summary = get_summary()
    daily_spending = get_daily_spending(30)

    # Average daily spend (excluding zero days)
    non_zero_days = [d for d in daily_spending if d["amount"] > 0]
    if not non_zero_days:
        return {"days_remaining": float("inf"), "avg_daily_spend": 0}

    avg_daily = sum(d["amount"] for d in non_zero_days) / len(non_zero_days)
    remaining_balance = summary["balance"]

    days_remaining = round(remaining_balance / avg_daily, 1) if avg_daily > 0 else float("inf")

    return {
        "days_remaining": days_remaining if days_remaining > 0 else 0,
        "avg_daily_spend": round(avg_daily, 2),
        "remaining_balance": remaining_balance,
    }


def get_needs_vs_wants():
    """Classify spending into needs vs wants (50/30/20 rule)."""
    breakdown = get_category_breakdown()

    NEEDS = {"Rent", "Utilities", "Groceries", "Health", "EMI", "Transport", "Education"}
    WANTS = {"Food", "Entertainment", "Shopping", "Subscriptions", "Personal"}

    needs_total = sum(c["amount"] for c in breakdown if c["category"] in NEEDS)
    wants_total = sum(c["amount"] for c in breakdown if c["category"] in WANTS)
    savings_investments = sum(c["amount"] for c in breakdown if c["category"] == "Investments")
    other = sum(c["amount"] for c in breakdown if c["category"] not in NEEDS and c["category"] not in WANTS and c["category"] != "Investments")

    total = needs_total + wants_total + savings_investments + other
    if total == 0:
        total = 1  # avoid division by zero

    summary = get_summary()
    income = summary.get("income", 0) or 1

    return {
        "needs": {
            "amount": needs_total,
            "percentage": round((needs_total / income) * 100, 1),
            "target": 50,
            "categories": [c for c in breakdown if c["category"] in NEEDS],
        },
        "wants": {
            "amount": wants_total,
            "percentage": round((wants_total / income) * 100, 1),
            "target": 30,
            "categories": [c for c in breakdown if c["category"] in WANTS],
        },
        "savings": {
            "amount": savings_investments,
            "percentage": round((savings_investments / income) * 100, 1),
            "target": 20,
        },
    }


def get_eating_out_vs_home():
    """Compare restaurant/delivery spending vs groceries."""
    breakdown = get_category_breakdown()

    eating_out = sum(c["amount"] for c in breakdown if c["category"] == "Food")
    groceries = sum(c["amount"] for c in breakdown if c["category"] == "Groceries")
    total = eating_out + groceries or 1

    return {
        "eating_out": {"amount": eating_out, "percentage": round((eating_out / total) * 100, 1)},
        "groceries": {"amount": groceries, "percentage": round((groceries / total) * 100, 1)},
        "total_food_cost": total,
        "recommendation": "Consider meal prepping!" if eating_out > groceries * 1.5 else "Good balance!",
    }


def get_total_subscriptions_cost():
    """Calculate total monthly subscription cost."""
    subs = get_subscriptions()
    monthly_cost = 0

    for s in subs:
        if s["frequency"] == "monthly":
            monthly_cost += s["amount"]
        elif s["frequency"] == "yearly":
            monthly_cost += s["amount"] / 12
        elif s["frequency"] == "weekly":
            monthly_cost += s["amount"] * 4.33
        elif s["frequency"] == "daily":
            monthly_cost += s["amount"] * 30

    return {
        "total_monthly": round(monthly_cost, 2),
        "total_yearly": round(monthly_cost * 12, 2),
        "count": len(subs),
        "subscriptions": subs,
    }


def get_weekend_vs_weekday():
    """Compare weekend vs weekday spending."""
    transactions = get_transactions(
        start_date=(date.today() - timedelta(days=30)).isoformat()
    )

    weekend_total = 0
    weekday_total = 0
    weekend_count = 0
    weekday_count = 0

    for tx in transactions:
        if tx["type"] != "expense":
            continue
        tx_date = date.fromisoformat(tx["date"])
        if tx_date.weekday() >= 5:  # Saturday/Sunday
            weekend_total += tx["amount"]
            weekend_count += 1
        else:
            weekday_total += tx["amount"]
            weekday_count += 1

    return {
        "weekend": {"total": weekend_total, "count": weekend_count, "avg": round(weekend_total / max(weekend_count, 1), 2)},
        "weekday": {"total": weekday_total, "count": weekday_count, "avg": round(weekday_total / max(weekday_count, 1), 2)},
    }


def get_payment_method_breakdown():
    """Break down spending by payment method."""
    transactions = get_transactions(
        start_date=(date.today().replace(day=1)).isoformat()
    )

    methods = {}
    for tx in transactions:
        if tx["type"] != "expense":
            continue
        method = tx.get("payment_method", "Other")
        if method not in methods:
            methods[method] = {"total": 0, "count": 0}
        methods[method]["total"] += tx["amount"]
        methods[method]["count"] += 1

    return [
        {"method": k, "total": v["total"], "count": v["count"]}
        for k, v in sorted(methods.items(), key=lambda x: x[1]["total"], reverse=True)
    ]


def get_forecast():
    """Predict end-of-month spending based on current trajectory."""
    today = date.today()
    days_passed = today.day
    days_in_month = 30  # Approximation
    days_remaining = days_in_month - days_passed

    summary = get_summary()
    breakdown = get_category_breakdown()

    if days_passed == 0:
        days_passed = 1

    daily_rate = summary["expenses"] / days_passed
    projected_total = round(daily_rate * days_in_month, 2)

    budgets = get_budgets()
    budget_map = {b["category"]: b for b in budgets}

    category_forecasts = []
    for cat in breakdown:
        cat_daily_rate = cat["amount"] / days_passed
        cat_projected = round(cat_daily_rate * days_in_month, 2)
        budget = budget_map.get(cat["category"])

        forecast = {
            "category": cat["category"],
            "current_spent": cat["amount"],
            "projected_total": cat_projected,
            "daily_rate": round(cat_daily_rate, 2),
        }
        if budget:
            forecast["budget_limit"] = budget["monthly_limit"]
            forecast["will_exceed"] = cat_projected > budget["monthly_limit"]
            forecast["excess_amount"] = round(max(0, cat_projected - budget["monthly_limit"]), 2)

        category_forecasts.append(forecast)

    return {
        "days_passed": days_passed,
        "days_remaining": days_remaining,
        "current_expenses": summary["expenses"],
        "daily_rate": round(daily_rate, 2),
        "projected_monthly_total": projected_total,
        "income": summary["income"],
        "projected_savings": round(summary["income"] - projected_total, 2),
        "category_forecasts": category_forecasts,
    }


def get_full_analytics():
    """Get comprehensive analytics data for the dashboard."""
    return {
        "summary": get_summary(),
        "category_breakdown": get_category_breakdown(),
        "daily_spending": get_daily_spending(30),
        "budgets": get_budgets(),
        "burn_rate": get_burn_rate(),
        "needs_vs_wants": get_needs_vs_wants(),
        "subscriptions": get_total_subscriptions_cost(),
        "forecast": get_forecast(),
        "payment_methods": get_payment_method_breakdown(),
    }
