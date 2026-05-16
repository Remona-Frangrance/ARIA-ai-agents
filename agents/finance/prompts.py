"""
Finance Agent — LLM Prompt Templates
All prompts used by the Finance Agent for AI-powered analysis and insights.
"""

FINANCE_SYSTEM_PROMPT = """You are ARIA's Finance Intelligence Specialist. 
You help users manage their personal finances with expert advice tailored for city living in India.
You understand Indian financial products (UPI, SIP, PPF, FD, EMI), Indian expense patterns, and local terminology.
Always provide practical, actionable advice. Format numbers in Indian numbering system (lakhs, crores).
Be concise and professional. Use ₹ symbol for Indian Rupees."""


def transaction_parser_prompt(user_input):
    """Prompt to parse natural language into a structured transaction."""
    return f"""Parse this natural language input into a financial transaction.
Input: "{user_input}"

Extract and return ONLY valid JSON (no markdown, no explanation):
{{
    "amount": <number>,
    "description": "<brief description>",
    "type": "income" or "expense",
    "category": "<one of: Rent, Food, Transport, Entertainment, Groceries, Utilities, Shopping, Health, Education, Subscriptions, EMI, Investments, Personal, Salary, Freelance, Other>",
    "date": "<YYYY-MM-DD or null for today>",
    "payment_method": "<UPI, Cash, Card, NetBanking, or null>"
}}

Rules:
- If no amount is mentioned, set amount to 0
- If type is unclear, default to "expense"
- Use context clues for category (e.g., "swiggy" = Food, "uber" = Transport)
- For Indian context: "rent" = Rent, "emi" = EMI, "sip" = Investments"""


def financial_insights_prompt(summary, category_breakdown, budgets):
    """Prompt to generate personalized financial insights."""
    return f"""Analyze this financial data and provide 3-4 actionable insights:

Monthly Summary:
- Income: ₹{summary.get('income', 0):,.0f}
- Expenses: ₹{summary.get('expenses', 0):,.0f}
- Savings Rate: {summary.get('savings_rate', 0)}%
- Balance: ₹{summary.get('balance', 0):,.0f}

Category Breakdown:
{_format_categories(category_breakdown)}

Budget Status:
{_format_budgets(budgets)}

Provide insights as a JSON array (no markdown, no explanation):
[
    {{
        "type": "warning" | "tip" | "achievement" | "alert",
        "title": "<short title>",
        "message": "<actionable 1-2 line advice>",
        "icon": "<emoji>"
    }}
]

Focus on:
1. Overspending categories
2. Savings opportunities  
3. Positive achievements
4. Budget adherence"""


def ask_finance_prompt(question, summary, recent_transactions):
    """Prompt for natural language financial questions."""
    return f"""Answer this financial question based on the user's data:
Question: "{question}"

User's Current Month Summary:
- Income: ₹{summary.get('income', 0):,.0f}
- Expenses: ₹{summary.get('expenses', 0):,.0f}
- Balance: ₹{summary.get('balance', 0):,.0f}
- Savings Rate: {summary.get('savings_rate', 0)}%

Recent Transactions (last 20):
{_format_transactions(recent_transactions)}

Provide a helpful, concise answer with specific numbers from the data.
If the question cannot be answered from the available data, say so clearly."""


def budget_advice_prompt(category, spent, limit, days_remaining):
    """Prompt for category-specific budget advice."""
    return f"""The user has spent ₹{spent:,.0f} out of ₹{limit:,.0f} budget for "{category}" 
with {days_remaining} days remaining in the month.

Provide a brief, practical tip (2-3 sentences) to help them stay within budget.
Consider Indian city context (food delivery, auto-rickshaws, online shopping, etc.)."""


def _format_categories(breakdown):
    """Format category breakdown for prompts."""
    if not breakdown:
        return "No spending data available"
    return "\n".join(
        f"- {c['category']}: ₹{c['amount']:,.0f} ({c['percentage']}%)"
        for c in breakdown
    )


def _format_budgets(budgets):
    """Format budget data for prompts."""
    if not budgets:
        return "No budgets set"
    return "\n".join(
        f"- {b['category']}: ₹{b['spent']:,.0f} / ₹{b['monthly_limit']:,.0f} ({b['percentage']}%)"
        for b in budgets
    )


def _format_transactions(transactions):
    """Format transactions for prompts."""
    if not transactions:
        return "No recent transactions"
    return "\n".join(
        f"- {t['date']} | {t['type']} | ₹{t['amount']:,.0f} | {t['category']} | {t['description']}"
        for t in transactions[:20]
    )
