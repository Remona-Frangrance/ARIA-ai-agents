"""
Finance Agent — SQLite Database Layer
Handles all CRUD operations for transactions, budgets, goals, subscriptions, and profile.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "finance.db")


def get_connection():
    """Get a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT DEFAULT 'Other',
            type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            payment_method TEXT DEFAULT 'UPI',
            is_recurring INTEGER DEFAULT 0,
            tags TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            month TEXT NOT NULL,
            UNIQUE(category, month)
        );

        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT CHECK(frequency IN ('daily','weekly','monthly','yearly')) DEFAULT 'monthly',
            next_due TEXT,
            category TEXT DEFAULT 'Subscriptions',
            auto_detected INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            monthly_income REAL DEFAULT 0,
            city TEXT DEFAULT '',
            rent REAL DEFAULT 0,
            currency TEXT DEFAULT 'INR'
        );
    """)

    # Ensure profile row exists
    cursor.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")
    conn.commit()
    conn.close()


# ─── Transaction CRUD ──────────────────────────────────────

def add_transaction(amount, description, tx_type, tx_date=None, category=None,
                    payment_method="UPI", tags=None, notes=None, time=None):
    """Add a new transaction. Returns the created transaction dict."""
    conn = get_connection()
    if tx_date is None:
        tx_date = date.today().isoformat()
    if time is None:
        time = datetime.now().strftime("%H:%M")

    cursor = conn.execute(
        """INSERT INTO transactions (amount, description, category, type, date, time,
           payment_method, tags, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (amount, description, category or "Other", tx_type, tx_date, time,
         payment_method, tags, notes)
    )
    tx_id = cursor.lastrowid
    conn.commit()

    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
    conn.close()
    return dict(row)


def get_transactions(start_date=None, end_date=None, category=None,
                     tx_type=None, limit=100, offset=0):
    """Get transactions with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category:
        query += " AND category = ?"
        params.append(category)
    if tx_type:
        query += " AND type = ?"
        params.append(tx_type)

    query += " ORDER BY date DESC, time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_transaction(tx_id):
    """Delete a transaction by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()


# ─── Budget CRUD ───────────────────────────────────────────

def set_budget(category, monthly_limit, month=None):
    """Set or update a monthly budget for a category."""
    conn = get_connection()
    if month is None:
        month = date.today().strftime("%Y-%m")

    conn.execute(
        """INSERT INTO budgets (category, monthly_limit, month)
           VALUES (?, ?, ?)
           ON CONFLICT(category, month) DO UPDATE SET monthly_limit = ?""",
        (category, monthly_limit, month, monthly_limit)
    )
    conn.commit()
    conn.close()
    return {"category": category, "monthly_limit": monthly_limit, "month": month}


def get_budgets(month=None):
    """Get all budgets for a given month, with spent amounts."""
    conn = get_connection()
    if month is None:
        month = date.today().strftime("%Y-%m")

    budgets = conn.execute(
        "SELECT * FROM budgets WHERE month = ?", (month,)
    ).fetchall()

    result = []
    for b in budgets:
        spent_row = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as spent FROM transactions
               WHERE category = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?""",
            (b["category"], month)
        ).fetchone()

        result.append({
            **dict(b),
            "spent": spent_row["spent"],
            "remaining": b["monthly_limit"] - spent_row["spent"],
            "percentage": round((spent_row["spent"] / b["monthly_limit"]) * 100, 1) if b["monthly_limit"] > 0 else 0
        })

    conn.close()
    return result


# ─── Savings Goals CRUD ────────────────────────────────────

def create_goal(name, target_amount, deadline=None, priority="Medium"):
    """Create a new savings goal."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO savings_goals (name, target_amount, deadline, priority)
           VALUES (?, ?, ?, ?)""",
        (name, target_amount, deadline, priority)
    )
    goal_id = cursor.lastrowid
    conn.commit()

    row = conn.execute("SELECT * FROM savings_goals WHERE id = ?", (goal_id,)).fetchone()
    conn.close()
    return dict(row)


def get_goals():
    """Get all savings goals with progress info."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM savings_goals ORDER BY status ASC, priority DESC"
    ).fetchall()
    conn.close()

    goals = []
    for r in rows:
        d = dict(r)
        d["progress"] = round((d["current_amount"] / d["target_amount"]) * 100, 1) if d["target_amount"] > 0 else 0
        goals.append(d)
    return goals


def update_goal(goal_id, current_amount=None, status=None):
    """Update a savings goal (add to savings or change status)."""
    conn = get_connection()
    if current_amount is not None:
        conn.execute(
            "UPDATE savings_goals SET current_amount = ? WHERE id = ?",
            (current_amount, goal_id)
        )
    if status is not None:
        conn.execute(
            "UPDATE savings_goals SET status = ? WHERE id = ?",
            (status, goal_id)
        )
    conn.commit()

    row = conn.execute("SELECT * FROM savings_goals WHERE id = ?", (goal_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_goal(goal_id):
    """Delete a savings goal."""
    conn = get_connection()
    conn.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()


# ─── Subscriptions CRUD ───────────────────────────────────

def add_subscription(name, amount, frequency="monthly", next_due=None, category="Subscriptions"):
    """Add a subscription/recurring payment."""
    conn = get_connection()
    if next_due is None:
        next_due = date.today().isoformat()

    cursor = conn.execute(
        """INSERT INTO subscriptions (name, amount, frequency, next_due, category)
           VALUES (?, ?, ?, ?, ?)""",
        (name, amount, frequency, next_due, category)
    )
    sub_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
    conn.close()
    return dict(row)


def get_subscriptions(active_only=True):
    """Get all subscriptions."""
    conn = get_connection()
    query = "SELECT * FROM subscriptions"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY amount DESC"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_subscription(sub_id):
    """Delete a subscription."""
    conn = get_connection()
    conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()


# ─── Profile CRUD ─────────────────────────────────────────

def set_profile(monthly_income=None, city=None, rent=None, currency=None):
    """Update user financial profile."""
    conn = get_connection()
    updates = []
    params = []

    if monthly_income is not None:
        updates.append("monthly_income = ?")
        params.append(monthly_income)
    if city is not None:
        updates.append("city = ?")
        params.append(city)
    if rent is not None:
        updates.append("rent = ?")
        params.append(rent)
    if currency is not None:
        updates.append("currency = ?")
        params.append(currency)

    if updates:
        query = f"UPDATE profile SET {', '.join(updates)} WHERE id = 1"
        conn.execute(query, params)
        conn.commit()

    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def get_profile():
    """Get user financial profile."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


# ─── Summary & Analytics Queries ───────────────────────────

def get_summary(month=None):
    """Get financial summary for a given month."""
    conn = get_connection()
    if month is None:
        month = date.today().strftime("%Y-%m")

    # Previous month for comparison
    current_date = datetime.strptime(month + "-01", "%Y-%m-%d")
    prev_month = (current_date - timedelta(days=1)).strftime("%Y-%m")

    # Current month totals
    income_row = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE type = 'income' AND strftime('%Y-%m', date) = ?""", (month,)
    ).fetchone()

    expense_row = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE type = 'expense' AND strftime('%Y-%m', date) = ?""", (month,)
    ).fetchone()

    # Previous month totals
    prev_income = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE type = 'income' AND strftime('%Y-%m', date) = ?""", (prev_month,)
    ).fetchone()

    prev_expense = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE type = 'expense' AND strftime('%Y-%m', date) = ?""", (prev_month,)
    ).fetchone()

    # Transaction count
    tx_count = conn.execute(
        """SELECT COUNT(*) as count FROM transactions
           WHERE strftime('%Y-%m', date) = ?""", (month,)
    ).fetchone()

    # Profile info
    profile = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()

    income = income_row["total"]
    expenses = expense_row["total"]
    balance = income - expenses
    savings_rate = round(((income - expenses) / income) * 100, 1) if income > 0 else 0

    # Rent status
    rent_amount = profile["rent"] if profile else 0
    rent_paid_row = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE category = 'Rent' AND type = 'expense' AND strftime('%Y-%m', date) = ?""",
        (month,)
    ).fetchone()
    rent_paid = rent_paid_row["total"] >= rent_amount if rent_amount > 0 else True

    conn.close()

    return {
        "month": month,
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "savings_rate": savings_rate,
        "prev_income": prev_income["total"],
        "prev_expenses": prev_expense["total"],
        "income_change": income - prev_income["total"],
        "expense_change": expenses - prev_expense["total"],
        "transaction_count": tx_count["count"],
        "rent_amount": rent_amount,
        "rent_paid": rent_paid,
        "monthly_income": profile["monthly_income"] if profile else 0,
    }


def get_category_breakdown(month=None):
    """Get category-wise spending breakdown for a month."""
    conn = get_connection()
    if month is None:
        month = date.today().strftime("%Y-%m")

    rows = conn.execute(
        """SELECT category, SUM(amount) as total, COUNT(*) as count
           FROM transactions
           WHERE type = 'expense' AND strftime('%Y-%m', date) = ?
           GROUP BY category ORDER BY total DESC""",
        (month,)
    ).fetchall()

    total_expense = sum(r["total"] for r in rows)
    conn.close()

    return [{
        "category": r["category"],
        "amount": r["total"],
        "count": r["count"],
        "percentage": round((r["total"] / total_expense) * 100, 1) if total_expense > 0 else 0
    } for r in rows]


def get_daily_spending(days=30):
    """Get daily spending for the last N days."""
    conn = get_connection()
    start = (date.today() - timedelta(days=days)).isoformat()

    rows = conn.execute(
        """SELECT date, SUM(amount) as total
           FROM transactions
           WHERE type = 'expense' AND date >= ?
           GROUP BY date ORDER BY date ASC""",
        (start,)
    ).fetchall()

    conn.close()

    # Fill in missing dates with 0
    result = []
    current = date.today() - timedelta(days=days)
    expense_map = {r["date"]: r["total"] for r in rows}

    for i in range(days + 1):
        d = (current + timedelta(days=i)).isoformat()
        result.append({
            "date": d,
            "amount": expense_map.get(d, 0)
        })

    return result


def get_monthly_trend(months=6):
    """Get monthly income/expense trends."""
    conn = get_connection()
    results = []

    for i in range(months - 1, -1, -1):
        d = date.today() - timedelta(days=i * 30)
        m = d.strftime("%Y-%m")

        income = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
               WHERE type = 'income' AND strftime('%Y-%m', date) = ?""", (m,)
        ).fetchone()["total"]

        expense = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
               WHERE type = 'expense' AND strftime('%Y-%m', date) = ?""", (m,)
        ).fetchone()["total"]

        results.append({
            "month": m,
            "income": income,
            "expenses": expense,
            "savings": income - expense
        })

    conn.close()
    return results


# ─── Seed Sample Data ──────────────────────────────────────

def seed_sample_data():
    """Populate DB with realistic sample data for demonstration."""
    conn = get_connection()

    # Check if data already exists
    count = conn.execute("SELECT COUNT(*) as c FROM transactions").fetchone()["c"]
    if count > 0:
        conn.close()
        return

    # Set profile
    conn.execute(
        "UPDATE profile SET monthly_income = 85000, city = 'Bangalore', rent = 18000, currency = 'INR' WHERE id = 1"
    )

    # Sample transactions for current month and last month
    today = date.today()
    current_month = today.strftime("%Y-%m")
    prev_month_date = today - timedelta(days=30)
    prev_month = prev_month_date.strftime("%Y-%m")

    transactions = [
        # Current month income
        (85000, "Monthly salary credited", "Salary", "income", f"{current_month}-01", "10:00", "NetBanking"),
        (5000, "Freelance project payment", "Freelance", "income", f"{current_month}-05", "14:30", "UPI"),

        # Current month expenses
        (18000, "Monthly house rent June", "Rent", "expense", f"{current_month}-01", "09:00", "NetBanking"),
        (2500, "Electricity bill BESCOM", "Utilities", "expense", f"{current_month}-03", "11:00", "UPI"),
        (1200, "Airtel broadband payment", "Utilities", "expense", f"{current_month}-02", "16:00", "UPI"),
        (450, "Swiggy lunch order", "Food", "expense", f"{current_month}-02", "13:15", "UPI"),
        (380, "Zomato dinner biryani", "Food", "expense", f"{current_month}-03", "20:30", "UPI"),
        (650, "Restaurant dinner with friends", "Food", "expense", f"{current_month}-05", "21:00", "Card"),
        (220, "Tea and snacks at cafe", "Food", "expense", f"{current_month}-06", "16:00", "UPI"),
        (180, "Uber ride to office", "Transport", "expense", f"{current_month}-02", "08:30", "UPI"),
        (250, "Ola auto HSR to Koramangala", "Transport", "expense", f"{current_month}-04", "09:15", "UPI"),
        (60, "Metro card recharge", "Transport", "expense", f"{current_month}-05", "08:00", "UPI"),
        (150, "Rapido bike taxi", "Transport", "expense", f"{current_month}-07", "19:00", "UPI"),
        (649, "Netflix subscription renewal", "Subscriptions", "expense", f"{current_month}-08", "00:00", "Card"),
        (119, "Spotify premium monthly", "Subscriptions", "expense", f"{current_month}-08", "00:00", "Card"),
        (1499, "Amazon Prime annual (monthly)", "Subscriptions", "expense", f"{current_month}-01", "00:00", "Card"),
        (2800, "Bigbasket weekly groceries", "Groceries", "expense", f"{current_month}-03", "10:00", "UPI"),
        (1500, "DMart monthly groceries", "Groceries", "expense", f"{current_month}-07", "11:00", "Card"),
        (3200, "Amazon headphones purchase", "Shopping", "expense", f"{current_month}-04", "15:00", "Card"),
        (1800, "Myntra clothes order", "Shopping", "expense", f"{current_month}-06", "22:00", "UPI"),
        (500, "Gym membership monthly", "Health", "expense", f"{current_month}-01", "07:00", "UPI"),
        (350, "Pharmacy medicines", "Health", "expense", f"{current_month}-05", "18:00", "UPI"),
        (799, "Udemy course purchase", "Education", "expense", f"{current_month}-04", "20:00", "Card"),
        (300, "Movie tickets PVR", "Entertainment", "expense", f"{current_month}-06", "19:00", "UPI"),
        (1200, "Weekend pub with friends", "Entertainment", "expense", f"{current_month}-07", "22:00", "Card"),
        (15000, "Home loan EMI", "EMI", "expense", f"{current_month}-05", "10:00", "NetBanking"),
        (5000, "SIP mutual fund monthly", "Investments", "expense", f"{current_month}-05", "10:00", "NetBanking"),
        (400, "Laundry and dry cleaning", "Personal", "expense", f"{current_month}-06", "12:00", "Cash"),
        (500, "Haircut at salon", "Personal", "expense", f"{current_month}-03", "16:00", "UPI"),

        # Previous month
        (85000, "Monthly salary credited", "Salary", "income", f"{prev_month}-01", "10:00", "NetBanking"),
        (18000, "Monthly house rent", "Rent", "expense", f"{prev_month}-01", "09:00", "NetBanking"),
        (3500, "Electricity + water bills", "Utilities", "expense", f"{prev_month}-03", "11:00", "UPI"),
        (4200, "Food delivery orders total", "Food", "expense", f"{prev_month}-15", "12:00", "UPI"),
        (2800, "Groceries monthly", "Groceries", "expense", f"{prev_month}-10", "10:00", "UPI"),
        (1800, "Transport costs", "Transport", "expense", f"{prev_month}-15", "09:00", "UPI"),
        (2000, "Shopping expenses", "Shopping", "expense", f"{prev_month}-12", "15:00", "Card"),
        (2267, "All subscriptions", "Subscriptions", "expense", f"{prev_month}-08", "00:00", "Card"),
        (15000, "Home loan EMI", "EMI", "expense", f"{prev_month}-05", "10:00", "NetBanking"),
        (5000, "SIP mutual fund", "Investments", "expense", f"{prev_month}-05", "10:00", "NetBanking"),
        (800, "Entertainment", "Entertainment", "expense", f"{prev_month}-20", "19:00", "UPI"),
        (500, "Health expenses", "Health", "expense", f"{prev_month}-18", "16:00", "UPI"),
    ]

    for tx in transactions:
        conn.execute(
            """INSERT INTO transactions (amount, description, category, type, date, time, payment_method)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            tx
        )

    # Sample budgets
    budgets = [
        ("Food", 8000, current_month),
        ("Transport", 3000, current_month),
        ("Shopping", 5000, current_month),
        ("Entertainment", 3000, current_month),
        ("Groceries", 6000, current_month),
        ("Utilities", 4000, current_month),
        ("Health", 2000, current_month),
        ("Personal", 2000, current_month),
    ]
    for b in budgets:
        conn.execute(
            "INSERT OR IGNORE INTO budgets (category, monthly_limit, month) VALUES (?, ?, ?)", b
        )

    # Sample savings goals
    goals = [
        ("Emergency Fund", 100000, 25000, "2026-12-31", "High"),
        ("Vacation Trip", 50000, 12000, "2026-09-30", "Medium"),
        ("New Laptop", 80000, 35000, "2026-11-30", "Medium"),
        ("Investment Portfolio", 200000, 60000, None, "Low"),
    ]
    for g in goals:
        conn.execute(
            """INSERT INTO savings_goals (name, target_amount, current_amount, deadline, priority)
               VALUES (?, ?, ?, ?, ?)""",
            g
        )

    # Sample subscriptions
    subs = [
        ("Netflix", 649, "monthly", f"{current_month}-08", "Entertainment"),
        ("Spotify Premium", 119, "monthly", f"{current_month}-08", "Entertainment"),
        ("Amazon Prime", 1499, "yearly", f"{current_month}-01", "Shopping"),
        ("YouTube Premium", 149, "monthly", f"{current_month}-15", "Entertainment"),
        ("Gym Membership", 500, "monthly", f"{current_month}-01", "Health"),
        ("Cloud Storage", 130, "monthly", f"{current_month}-20", "Utilities"),
    ]
    for s in subs:
        conn.execute(
            """INSERT INTO subscriptions (name, amount, frequency, next_due, category)
               VALUES (?, ?, ?, ?, ?)""",
            s
        )

    conn.commit()
    conn.close()


def clear_all_data():
    """Wipe all user data from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM budgets")
    cursor.execute("DELETE FROM savings_goals")
    cursor.execute("DELETE FROM subscriptions")
    cursor.execute("UPDATE profile SET monthly_income = 0, city = '', rent = 0, currency = 'INR' WHERE id = 1")
    conn.commit()
    conn.close()
    return {"message": "All data cleared successfully"}


# Initialize on import
init_db()
