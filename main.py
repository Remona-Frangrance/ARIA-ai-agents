from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import os
from shared.llm_client import ask_llm
from agents.life_admin.agent import handle_task
from agents.finance.agent import handle_finance
from agents.wellness.agent import handle_task as handle_wellness, get_wellness_analytics
from agents.relationships.agent import handle_task as handle_relationships, get_social_intel

app = FastAPI(title="ARIA - AI Agent System")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "agent": "ARIA Core"}

@app.get("/api/tip")
def get_productivity_tip():
    response = ask_llm("Give me one productivity tip in one sentence.")
    return {"tip": response}

@app.get("/api/life-admin")
def life_admin(task: str):
    return {"result": handle_task(task)}

@app.get("/api/wellness")
def wellness(task: str):
    return {"result": handle_wellness(task)}

@app.get("/api/relationships")
def relationships(task: str):
    return {"result": handle_relationships(task)}

@app.get("/api/wellness/analytics")
def wellness_analytics():
    return get_wellness_analytics()

@app.get("/api/relationships/analytics")
def relationships_analytics():
    return get_social_intel()

@app.post("/api/wellness/seed")
def wellness_seed():
    from shared.wellness_db import init_db
    init_db()
    return {"message": "Wellness data seeded"}

@app.post("/api/relationships/seed")
def relationships_seed():
    from shared.relationship_db import init_db
    init_db()
    return {"message": "Relationship data seeded"}


# ═══════════════════════════════════════════════════════════
# FINANCE AGENT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/finance/seed")
def finance_seed():
    """Seed the database with sample data for demo purposes."""
    return handle_finance("seed_data")


# ─── Transactions ─────────────────────────────────────────

@app.post("/api/finance/transaction")
def add_transaction(data: dict = Body(...)):
    """Add a transaction (structured or natural language)."""
    if "text" in data:
        # Natural language input
        return handle_finance("add_transaction_nl", text=data["text"])
    else:
        return handle_finance("add_transaction", **data)


@app.get("/api/finance/transactions")
def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 100,
):
    return handle_finance(
        "get_transactions",
        start_date=start_date, end_date=end_date,
        category=category, type=type, limit=limit,
    )


@app.delete("/api/finance/transaction/{tx_id}")
def delete_transaction(tx_id: int):
    return handle_finance("delete_transaction", tx_id=tx_id)


# ─── Summary & Analytics ──────────────────────────────────

@app.get("/api/finance/summary")
def get_finance_summary(month: Optional[str] = None):
    return handle_finance("get_summary", month=month)


@app.get("/api/finance/analytics")
def get_finance_analytics():
    return handle_finance("get_analytics")


@app.get("/api/finance/category-breakdown")
def get_finance_categories(month: Optional[str] = None):
    return handle_finance("get_category_breakdown", month=month)


@app.get("/api/finance/daily-spending")
def get_finance_daily(days: int = 30):
    return handle_finance("get_daily_spending", days=days)


@app.post("/api/finance/budget")
def set_finance_budget(data: dict = Body(...)):
    return handle_finance("set_budget", **data)


@app.get("/api/finance/budgets")
def get_finance_budgets(month: Optional[str] = None):
    return handle_finance("get_budgets", month=month)


@app.post("/api/finance/goal")
def create_finance_goal(data: dict = Body(...)):
    return handle_finance("create_goal", **data)


@app.get("/api/finance/goals")
def get_finance_goals():
    return handle_finance("get_goals")


@app.get("/api/finance/subscriptions")
def get_finance_subs(active_only: bool = True):
    return handle_finance("get_subscriptions", active_only=active_only)


@app.get("/api/finance/profile")
def get_finance_profile():
    return handle_finance("get_profile")


@app.post("/api/finance/profile")
def update_finance_profile(data: dict = Body(...)):
    return handle_finance("set_profile", **data)


# ─── AI Features ──────────────────────────────────────────

@app.post("/api/finance/reset")
def finance_reset():
    """Reset all finance data."""
    return handle_finance("reset_data")


@app.get("/api/finance/forecast")
def get_forecast():
    return handle_finance("get_forecast")


@app.get("/api/finance/insights")
def get_insights():
    return handle_finance("get_insights")


@app.get("/api/finance/ask")
def ask_finance(question: str = Query(...)):
    return handle_finance("ask", question=question)


# ─── Static Files & Frontend (Production) ──────────────────

# Ensure static directory exists before mounting
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API routes to pass through
        if full_path.startswith("api/"):
            return None
        
        file_path = os.path.join("static", full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join("static", "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))