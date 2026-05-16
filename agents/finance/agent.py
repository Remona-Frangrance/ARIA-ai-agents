"""
Finance Agent — Main Agent Logic
Handles financial operations: transaction management, AI analysis, insights generation.
"""

import json
from datetime import date, timedelta
from agents.finance.database import (
    add_transaction, get_transactions, delete_transaction,
    set_budget, get_budgets, create_goal, get_goals, update_goal, delete_goal,
    add_subscription, get_subscriptions, delete_subscription,
    set_profile, get_profile, get_summary, get_category_breakdown,
    get_daily_spending, get_monthly_trend, seed_sample_data, init_db
)
from agents.finance.analytics import (
    get_burn_rate, get_needs_vs_wants, get_eating_out_vs_home,
    get_total_subscriptions_cost, get_forecast, get_full_analytics,
    get_payment_method_breakdown
)
from agents.finance.prompts import (
    FINANCE_SYSTEM_PROMPT, transaction_parser_prompt,
    financial_insights_prompt, ask_finance_prompt
)
from shared.llm_client import ask_llm
from models.expense_categorizer.predict import predict_category


def handle_finance(action: str, **kwargs):
    """Main dispatcher for all finance operations."""

    # Ensure DB is ready
    init_db()

    handlers = {
        "add_transaction": _handle_add_transaction,
        "add_transaction_nl": _handle_natural_language_transaction,
        "get_transactions": _handle_get_transactions,
        "delete_transaction": _handle_delete_transaction,
        "get_summary": _handle_get_summary,
        "get_analytics": _handle_get_analytics,
        "get_category_breakdown": _handle_get_category_breakdown,
        "get_daily_spending": _handle_get_daily_spending,
        "get_monthly_trend": _handle_get_monthly_trend,
        "set_budget": _handle_set_budget,
        "get_budgets": _handle_get_budgets,
        "create_goal": _handle_create_goal,
        "get_goals": _handle_get_goals,
        "update_goal": _handle_update_goal,
        "delete_goal": _handle_delete_goal,
        "add_subscription": _handle_add_subscription,
        "get_subscriptions": _handle_get_subscriptions,
        "delete_subscription": _handle_delete_subscription,
        "set_profile": _handle_set_profile,
        "get_profile": _handle_get_profile,
        "get_forecast": _handle_get_forecast,
        "get_insights": _handle_get_insights,
        "ask": _handle_ask,
        "seed_data": _handle_seed_data,
        "reset_data": _handle_reset_data,
    }

    handler = handlers.get(action)
    if handler:
        return handler(**kwargs)

    return {"error": f"Unknown action: {action}"}


# ─── Transaction Handlers ─────────────────────────────────

def _handle_add_transaction(**kwargs):
    """Add a manually structured transaction."""
    description = kwargs.get("description", "")
    category = kwargs.get("category")

    # Auto-categorize if no category provided
    if not category or category == "Auto":
        category = predict_category(description)

    return add_transaction(
        amount=kwargs.get("amount", 0),
        description=description,
        tx_type=kwargs.get("type", "expense"),
        tx_date=kwargs.get("date"),
        category=category,
        payment_method=kwargs.get("payment_method", "UPI"),
        tags=kwargs.get("tags"),
        notes=kwargs.get("notes"),
    )


def _handle_natural_language_transaction(**kwargs):
    """Parse a natural language input into a transaction using LLM."""
    text = kwargs.get("text", "")
    if not text:
        return {"error": "No text provided"}

    prompt = transaction_parser_prompt(text)
    try:
        response = ask_llm(prompt, system=FINANCE_SYSTEM_PROMPT)

        # Parse JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")

        parsed = json.loads(response[start:end])

        # Validate and fill defaults
        amount = float(parsed.get("amount", 0))
        description = parsed.get("description", text)
        tx_type = parsed.get("type", "expense")
        category = parsed.get("category", predict_category(description))
        tx_date = parsed.get("date") or date.today().isoformat()
        payment_method = parsed.get("payment_method", "UPI")

        if amount <= 0:
            return {"error": "Could not extract a valid amount from the input", "parsed": parsed}

        transaction = add_transaction(
            amount=amount,
            description=description,
            tx_type=tx_type,
            tx_date=tx_date,
            category=category,
            payment_method=payment_method,
        )

        return {
            "type": "transaction_added",
            "transaction": transaction,
            "parsed_from": text,
        }

    except Exception as e:
        # Fallback: try keyword-based extraction
        return {"error": f"Failed to parse: {str(e)}", "input": text}


def _handle_get_transactions(**kwargs):
    return get_transactions(
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
        category=kwargs.get("category"),
        tx_type=kwargs.get("type"),
        limit=kwargs.get("limit", 100),
    )


def _handle_delete_transaction(**kwargs):
    tx_id = kwargs.get("id")
    if tx_id:
        delete_transaction(int(tx_id))
        return {"deleted": True, "id": tx_id}
    return {"error": "No ID provided"}


# ─── Summary & Analytics ──────────────────────────────────

def _handle_get_summary(**kwargs):
    return get_summary(month=kwargs.get("month"))


def _handle_get_analytics(**kwargs):
    return get_full_analytics()


def _handle_get_category_breakdown(**kwargs):
    return get_category_breakdown(month=kwargs.get("month"))


def _handle_get_daily_spending(**kwargs):
    return get_daily_spending(days=kwargs.get("days", 30))


def _handle_get_monthly_trend(**kwargs):
    return get_monthly_trend(months=kwargs.get("months", 6))


# ─── Budget Handlers ──────────────────────────────────────

def _handle_set_budget(**kwargs):
    return set_budget(
        category=kwargs.get("category"),
        monthly_limit=float(kwargs.get("monthly_limit", 0)),
        month=kwargs.get("month"),
    )


def _handle_get_budgets(**kwargs):
    return get_budgets(month=kwargs.get("month"))


# ─── Goal Handlers ────────────────────────────────────────

def _handle_create_goal(**kwargs):
    return create_goal(
        name=kwargs.get("name"),
        target_amount=float(kwargs.get("target_amount", 0)),
        deadline=kwargs.get("deadline"),
        priority=kwargs.get("priority", "Medium"),
    )


def _handle_get_goals(**kwargs):
    return get_goals()


def _handle_update_goal(**kwargs):
    goal_id = kwargs.get("id")
    if not goal_id:
        return {"error": "No goal ID provided"}
    return update_goal(
        goal_id=int(goal_id),
        current_amount=kwargs.get("current_amount"),
        status=kwargs.get("status"),
    )


def _handle_delete_goal(**kwargs):
    goal_id = kwargs.get("id")
    if goal_id:
        delete_goal(int(goal_id))
        return {"deleted": True, "id": goal_id}
    return {"error": "No goal ID provided"}


# ─── Subscription Handlers ────────────────────────────────

def _handle_add_subscription(**kwargs):
    return add_subscription(
        name=kwargs.get("name"),
        amount=float(kwargs.get("amount", 0)),
        frequency=kwargs.get("frequency", "monthly"),
        next_due=kwargs.get("next_due"),
        category=kwargs.get("category", "Subscriptions"),
    )


def _handle_get_subscriptions(**kwargs):
    return get_subscriptions()


def _handle_delete_subscription(**kwargs):
    sub_id = kwargs.get("id")
    if sub_id:
        delete_subscription(int(sub_id))
        return {"deleted": True, "id": sub_id}
    return {"error": "No ID provided"}


# ─── Profile Handlers ─────────────────────────────────────

def _handle_set_profile(**kwargs):
    return set_profile(
        monthly_income=kwargs.get("monthly_income"),
        city=kwargs.get("city"),
        rent=kwargs.get("rent"),
        currency=kwargs.get("currency"),
    )


def _handle_get_profile(**kwargs):
    return get_profile()


# ─── AI-Powered Handlers ──────────────────────────────────

def _handle_get_forecast(**kwargs):
    return get_forecast()


def _handle_get_insights(**kwargs):
    """Generate AI-powered financial insights."""
    try:
        summary = get_summary()
        breakdown = get_category_breakdown()
        budgets = get_budgets()

        prompt = financial_insights_prompt(summary, breakdown, budgets)
        response = ask_llm(prompt, system=FINANCE_SYSTEM_PROMPT)

        # Try to parse JSON array
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > 0:
            insights = json.loads(response[start:end])
        else:
            insights = [
                {
                    "type": "tip",
                    "title": "Financial Summary",
                    "message": response,
                    "icon": "💡"
                }
            ]

        return {"insights": insights}

    except Exception as e:
        return {"insights": [
            {
                "type": "tip",
                "title": "Keep Tracking",
                "message": "Continue logging your expenses to get personalized AI insights!",
                "icon": "📊"
            }
        ]}


def _handle_ask(**kwargs):
    """Answer natural language financial questions."""
    question = kwargs.get("question", "")
    if not question:
        return {"error": "No question provided"}

    try:
        summary = get_summary()
        recent = get_transactions(limit=20)

        prompt = ask_finance_prompt(question, summary, recent)
        response = ask_llm(prompt, system=FINANCE_SYSTEM_PROMPT)

        return {
            "question": question,
            "answer": response,
            "type": "ai_response",
        }
    except Exception as e:
        return {"error": str(e)}


def _handle_seed_data(**kwargs):
    """Seed the database with sample data."""
    seed_sample_data()
    return {"message": "Sample data seeded successfully!"}


def _handle_reset_data(**kwargs):
    """Reset all data in the database."""
    from agents.finance.database import clear_all_data
    return clear_all_data()
