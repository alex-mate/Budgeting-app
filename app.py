from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
import os,sys

from datetime import datetime
from helper import login_required, clean_text, clean_title, money, get_currency_symbol

# Configure app name
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

CATEGORIES = ["Food", "Shopping", "Transport", "Bills",
              "Entertainment", "Health", "Other"]

# Configure CS50 Library to use SQLite database
def exe_dir():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(exe_dir(), "budget.db")
db = SQL(f"sqlite:///{DB_PATH}")


# -------------------------
# MAKE HELPERS AVAILABLE IN TEMPLATES
# -------------------------
@app.context_processor
def inject_helpers():
    return dict(
        money=money,
        currency_symbol=get_currency_symbol,
    )

@app.context_processor
def inject_user():
    if "user_id" in session:
        user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        if user:
            return dict(username = user[0]["username"])
    return dict(username = None)    


# -------------------------
# PROFILE RENDER HELPER
# (kept in app.py so it can use db)
# -------------------------
def render_profile(success_message=None, error_message=None):
    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]

    return render_template(
        "profile.html",
        user=user,
        success_message=success_message,
        error_message=error_message,
        active="profile"
    )

#--------------------
# HOMEPAGE
#--------------------
@app.route("/")
@login_required
def index():
    username = db.execute("SELECT username FROM users where id = ?",session["user_id"])[0]["username"]
    user_id = session["user_id"]
    user_row = db.execute("SELECT savings_goal FROM users WHERE id = ?", user_id)[0]
   
    # SAVINGS
    savings_goal = user_row["savings_goal"]
    row=db.execute("SELECT IFNULL(SUM(CASE WHEN type = 'savings' THEN amount ELSE 0 END), 0) AS saved, IFNULL(SUM(CASE WHEN type='savingswithdrawn' THEN amount ELSE 0 END), 0) as withdrawn FROM transactions WHERE user_id = ?",user_id)[0]
    total_savings = row["saved"] - row["withdrawn"]
    if savings_goal and float(savings_goal) > 0:
        savings_progress = round((float(total_savings) / float(savings_goal)) * 100, 1)
        savings_progress_clamped = max(0, min(100, savings_progress))
    else:
        savings_progress = None
        savings_progress_clamped = 0
    #MONTHLY SNAPSHOT
    today = datetime.today()
    month = today.strftime("%m")
    year = today.strftime("%Y")
    totals = db.execute("SELECT IFNULL(SUM(CASE WHEN lower(type)='income'  THEN amount END), 0) AS total_income,IFNULL(SUM(CASE WHEN lower(type)='expense' THEN amount END), 0) AS total_expense FROM transactions WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ? ", user_id, year, month)[0]

    row=db.execute("SELECT IFNULL(SUM(CASE WHEN type = 'savings' THEN amount ELSE 0 END), 0) AS saved, IFNULL(SUM(CASE WHEN type='savingswithdrawn' THEN amount ELSE 0 END), 0) as withdrawn FROM transactions WHERE user_id = ?",user_id)[0]
   
    total_income  = float(totals["total_income"])
    total_expense = float(totals["total_expense"])
    saved = float(row["saved"] - row["withdrawn"])
    budget_row = db.execute("SELECT IFNULL(SUM(amount), 0) AS total_budget FROM budgets WHERE user_id = ? AND year = ? AND month  = ?", user_id, year, month)[0]

    total_budget = float(budget_row["total_budget"])

    remaining_budget = float(total_budget - total_expense)
    #BIGGEST PURCHASE
    row = db.execute("SELECT * FROM transactions WHERE type='expense' AND user_id = ? AND strftime('%Y', date) = ? AND strftime('%m',date) = ?", user_id, year, month)
    if row:
        biggest = max(row, key=lambda r: r["amount"])
        merchant = biggest["merchant"] 
        biggest_purchase = biggest["amount"] 
        category = biggest["category"] 
        notes =biggest["notes"] 
    else:
        biggest = "No purchases yet."
        merchant = "-"
        category = "-"
        biggest_purchase = 0
        notes = "-"
    # TOP CATEGORY
    top = db.execute("SELECT category,SUM(amount) AS total FROM transactions WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m',date) = ? AND type='expense' GROUP BY category ORDER BY total DESC LIMIT 1", user_id,year,month)
    if top :
        top_category=top[0]["category"]
        spent=top[0]["total"]
    else:
        top_category = None
        spent = 0

    #LAST 5 TRANSACTIONS
    recent = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5",user_id)    
   
    return render_template("index.html", active="home",username=username,savings_goal=savings_goal,
        total_savings=total_savings,
        savings_progress=savings_progress,
        savings_progress_clamped=savings_progress_clamped,total_income=total_income,total_expense=total_expense,saved=saved,remaining_budget=remaining_budget, merchant=merchant, biggest_purchase=biggest_purchase, category=category,notes=notes,top_category=top_category,spent=spent,recent=recent)


#-------------------
# LOGIN/REGISTER PAGE
#-------------------
@app.route("/auth")
def auth():
    if "user_id" in session:
        return redirect("/")
    return render_template("auth.html", login_error=None, register_error=None)

#--------------------
# LOGIN
#--------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("auth.html", login_error="Please provide an username", register_error=None)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("auth.html", login_error="Please enter your password", register_error=None)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return render_template("auth.html", login_error="Invalid username and or password", register_error=None)

        # Remember which user has logged in and remember currency
        user = db.execute("SELECT * FROM users WHERE id = ?", rows[0]["id"])[0]
        session["user_id"] = user["id"]
        session["currency"] = user.get("currency", "GBP")  # default GBP if missing

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("auth.html", login_error=None, register_error=None)

#-----------------
# REGISTER
#-----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("auth.html", login_error=None, register_error="Please enter an username")
        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("auth.html", login_error=None, register_error="Please enter a password")
        # Ensure retype password was submitted
        elif not request.form.get("confirm"):
            return render_template("auth.html", login_error=None, register_error="Please retype your password for verification")

        # Ensure password is the same as retyped password
        if request.form.get("password") != request.form.get("confirm"):
            return render_template("auth.html", login_error=None, register_error="Passwords are not matching")

        # Ensure it has a unique username
        user = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(user) > 0:
            return render_template("auth.html", login_error=None, register_error="Username already taken")

        username = request.form.get("username")
        password = request.form.get("password")
        hash = generate_password_hash(password)

        # If your users table has currency column with default, it will auto-fill
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        user = db.execute("SELECT * FROM users WHERE username = ?", username)[0]
        session["user_id"] = user["id"]
        session["currency"] = user.get("currency", "GBP")

        return redirect("/")

    return render_template("auth.html", login_error=None, register_error=None)

#---------------
# LOGOUT
#---------------
@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

#-------------------------
# ADD TRANSACTIONS TAB
#-------------------------
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    user_id = session["user_id"]
    today = datetime.now().strftime("%Y-%m-%d")

    if request.method == "GET":
        return render_template(
            "add.html",
            current_date=today,
            success_message=None,
            error_message=None,
            active="add"
        )

    # POST
    t_type = request.form.get("type")
    amount_raw = request.form.get("amount")
    date = request.form.get("date") or today
    category = clean_title(request.form.get("category")) or None
    merchant = clean_title(request.form.get("merchant")) or None
    notes = clean_text(request.form.get("notes")) or None

    # Basic validation
    if t_type not in ("expense", "income", "savings", "savingswithdrawn"):
        return render_template(
            "add.html",
            current_date=date,
            error_message="Invalid transaction type.",
            success_message=None,
            active="add"
        )

    if not category and t_type == "savings":
        category = "Savings"
    if not category and t_type == "savingswithdrawn":
        category = "Savings Withdrawn"    

    if not amount_raw:
        return render_template(
            "add.html",
            current_date=date,
            error_message="Please enter an amount.",
            success_message=None,
            active="add"
        )

    try:
        amount = float(amount_raw)
    except ValueError:
        return render_template(
            "add.html",
            current_date=date,
            error_message="Amount must be a number.",
            success_message=None,
            active="add"
        )

    if amount <= 0:
        return render_template(
            "add.html",
            current_date=date,
            error_message="Amount must be greater than zero.",
            success_message=None,
            active="add"
        )
    row = db.execute("SELECT IFNULL(SUM(CASE WHEN type = 'savings' THEN amount ELSE 0 END), 0) AS saved, IFNULL(SUM(CASE WHEN type='savingswithdrawn' THEN amount ELSE 0 END), 0) as withdrawn FROM transactions WHERE user_id = ?",user_id)[0]
    current_savings = row["saved"] - row["withdrawn"]
    if t_type == "savingswithdrawn":
        if amount>current_savings:
            return render_template(
                "add.html",
                current_date=date,
                error_message="You cannot withdrawn more than your current savings.",
                success_message=None,
                active="add"
            )

    # Insert into DB
    db.execute(
        """
        INSERT INTO transactions (user_id, type, category, merchant, amount, date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        user_id, t_type, category, merchant, amount, date, notes
    )
    

    # Success message depending on type
    if t_type == "expense":
        msg = "Expense successfully added."
    elif t_type == "income":
        msg = "Income successfully added."
    elif t_type == 'savings':
        msg = "Savings successfully recorded."
    else:
        msg= "Savings Withdrawn succesfully recorded."

    return render_template(
        "add.html",
        current_date=date,
        success_message=msg,
        error_message=None,
        active="add"
    )

#--------------------
# ANALYTICS TAB
#--------------------
@app.route("/analytics")
@login_required
def analytics():
    user_id = session["user_id"]

    # --------- dropdown lists ----------
    months_for_select = [
        ("01", "January"), ("02", "February"), ("03", "March"),
        ("04", "April"), ("05", "May"), ("06", "June"),
        ("07", "July"), ("08", "August"), ("09", "September"),
        ("10", "October"), ("11", "November"), ("12", "December"),
    ]
    years_for_select = ["2023", "2024", "2025", "2026", "2027"]

    # --------- main month/year (monthly pie) ----------
    month = request.args.get("month") or datetime.now().strftime("%m")
    year = request.args.get("year") or datetime.now().strftime("%Y")
    month_label = next((lab for val, lab in months_for_select if val == month), month)

    # --------- user goal + total savings ----------
    user_row = db.execute("SELECT savings_goal FROM users WHERE id = ?", user_id)[0]
    savings_goal = user_row["savings_goal"]

    row = row = db.execute("SELECT IFNULL(SUM(CASE WHEN type = 'savings' THEN amount ELSE 0 END), 0) AS saved, IFNULL(SUM(CASE WHEN type='savingswithdrawn' THEN amount ELSE 0 END), 0) as withdrawn FROM transactions WHERE user_id = ?",user_id)[0]
    total_savings = row["saved"] - row["withdrawn"]

    if savings_goal and float(savings_goal) > 0:
        savings_progress = round((float(total_savings) / float(savings_goal)) * 100, 1)
        savings_progress_clamped = max(0, min(100, savings_progress))
    else:
        savings_progress = None
        savings_progress_clamped = 0

    # --------- monthly spending pie (expenses grouped by category) ----------
    monthly_rows = db.execute("""
        SELECT category, IFNULL(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND type = 'expense'
          AND strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
        GROUP BY category
        ORDER BY total DESC
    """, user_id, year, month)

    monthly_category_data = {
        "labels": [r["category"] for r in monthly_rows],
        "values": [float(r["total"]) for r in monthly_rows],
    }

    # --------- yearly overview (income/expense/savings per month) ----------
    labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    income = [0.0]*12
    expenses = [0.0]*12
    savings = [0.0]*12

    yearly_rows = db.execute("""
        SELECT strftime('%m', date) AS m, type, IFNULL(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND strftime('%Y', date) = ?
        GROUP BY m, type
    """, user_id, year)

    for r in yearly_rows:
        idx = int(r["m"]) - 1
        t = r["type"]
        total = float(r["total"])
        if t == "income":
            income[idx] = total
        elif t == "expense":
            expenses[idx] = total
        elif t == "savings":
            savings[idx] = total

    yearly_overview_data = {
        "labels": labels,
        "income": income,
        "expenses": expenses,
        "savings": savings,
    }

    # --------- top merchants (monthly, expenses) ----------
    top_merchants = db.execute("""
        SELECT merchant, IFNULL(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND type = 'expense'
          AND strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
          AND merchant IS NOT NULL AND merchant != ''
        GROUP BY merchant
        ORDER BY total DESC
        LIMIT 3
    """, user_id, year, month)

    # --------- 2-month comparison ----------
    c_year = request.args.get("c_year") or year
    c_month1 = request.args.get("c_month1") or datetime.now().strftime("%m")
    c_month2 = request.args.get("c_month2") or datetime.now().strftime("%m")

    def totals_for_month(m):
        rows = db.execute("""
            SELECT type, IFNULL(SUM(amount), 0) AS total
            FROM transactions
            WHERE user_id = ?
              AND strftime('%Y', date) = ?
              AND strftime('%m', date) = ?
            GROUP BY type
        """, user_id, c_year, m)

        out = {"income": 0.0, "expense": 0.0, "savings": 0.0}
        for rr in rows:
            out[rr["type"]] = float(rr["total"])
        return out

    m1 = totals_for_month(c_month1)
    m2 = totals_for_month(c_month2)

    def pct_change(a, b):
        # change from a -> b
        a = float(a)
        b = float(b)
        if a == 0 and b == 0:
            return 0.0
        if a == 0:
            return 100.0
        return round(((b - a) / a) * 100, 1)

    compare_totals = {
        "month1": m1,
        "month2": m2,
        "pct": {
            "income": pct_change(m1["income"], m2["income"]),
            "expense": pct_change(m1["expense"], m2["expense"]),
            "savings": pct_change(m1["savings"], m2["savings"]),
        }
    }

    # --------- category comparison (expenses by category) ----------
    c1_rows = db.execute("""
        SELECT category, IFNULL(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND type='expense'
          AND strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
        GROUP BY category
    """, user_id, c_year, c_month1)

    c2_rows = db.execute("""
        SELECT category, IFNULL(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
          AND type='expense'
          AND strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
        GROUP BY category
    """, user_id, c_year, c_month2)

    c1_map = {r["category"]: float(r["total"]) for r in c1_rows}
    c2_map = {r["category"]: float(r["total"]) for r in c2_rows}

    all_cats = sorted(set(list(c1_map.keys()) + list(c2_map.keys())))

    category_compare = []
    for cat in all_cats:
        a = c1_map.get(cat, 0.0)
        b = c2_map.get(cat, 0.0)
        category_compare.append({
            "category": cat,
            "month1": a,
            "month2": b,
            "pct": pct_change(a, b)
        })

    compare_data = {
        "labels": ["Income", "Expenses", "Savings"],
        "month1_label": f"{next((lab for val, lab in months_for_select if val == c_month1), c_month1)} {c_year}",
        "month2_label": f"{next((lab for val, lab in months_for_select if val == c_month2), c_month2)} {c_year}",
        "month1_values": [m1["income"], m1["expense"], m1["savings"]],
        "month2_values": [m2["income"], m2["expense"], m2["savings"]],
    }

    return render_template(
        "analytics.html",
        active="analytics",
        # selectors
        month=month, year=year, month_label=month_label,
        months_for_select=months_for_select, years_for_select=years_for_select,
        c_year=c_year, c_month1=c_month1, c_month2=c_month2,
        # cards
        savings_goal=savings_goal,
        total_savings=total_savings,
        savings_progress=savings_progress,
        savings_progress_clamped=savings_progress_clamped,
        top_merchants=top_merchants,
        # data for charts
        monthly_category_data=monthly_category_data,
        yearly_overview_data=yearly_overview_data,
        compare_data=compare_data,
        compare_totals=compare_totals,
        category_compare=category_compare,
    )

#----------------------
# BUDGETS TAB
# #-------------------- 
@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    user_id = session["user_id"]

    message = None
    message_type = "success"

    # ---- determine selected month/year ----
    if request.method == "GET":
        month = request.args.get("month")
        year = request.args.get("year")
    else:
        month = request.form.get("month")
        year = request.form.get("year")

    if not month or not year:
        today = datetime.today()
        month = today.strftime("%m")
        year = today.strftime("%Y")

    # ---- handle POST actions (updates) ----
    if request.method == "POST":
        # Update ALL budgets with same amount
        if "update_all" in request.form:
            raw = request.form.get("all_budget")
            if not raw:
                message = "Please enter an amount to update all budgets."
                message_type = "error"
            else:
                try:
                    amount = float(raw)
                except ValueError:
                    message = "Amount for all budgets must be a number."
                    message_type = "error"
                else:
                    existing = db.execute(
                        "SELECT COUNT(*) AS c FROM budgets "
                        "WHERE user_id = ? AND month = ? AND year = ?",
                        user_id, month, year
                    )[0]["c"]

                    if existing > 0:
                        db.execute(
                            "UPDATE budgets SET amount = ? "
                            "WHERE user_id = ? AND month = ? AND year = ?",
                            amount, user_id, month, year
                        )
                    else:
                        for cat in CATEGORIES:
                            db.execute(
                                "INSERT INTO budgets (user_id, category, amount, month, year) "
                                "VALUES (?, ?, ?, ?, ?)",
                                user_id, cat, amount, month, year
                            )
                    message = "All budgets were successfully updated."
                    message_type = "success"

        # Update ONE category budget
        elif "update_category" in request.form:
            category = request.form.get("update_category")
            field_name = f"amount_{category.lower()}"
            raw = request.form.get(field_name)

            if not raw:
                message = f"Please enter a budget amount for {category}."
                message_type = "error"
            else:
                try:
                    amount = float(raw)
                except ValueError:
                    message = f"Budget amount for {category} must be a number."
                    message_type = "error"
                else:
                    row = db.execute(
                        "SELECT id FROM budgets "
                        "WHERE user_id = ? AND month = ? AND year = ? AND category = ?",
                        user_id, month, year, category
                    )
                    if row:
                        db.execute(
                            "UPDATE budgets SET amount = ? "
                            "WHERE user_id = ? AND month = ? AND year = ? AND category = ?",
                            amount, user_id, month, year, category
                        )
                    else:
                        db.execute(
                            "INSERT INTO budgets (user_id, category, amount, month, year) "
                            "VALUES (?, ?, ?, ?, ?)",
                            user_id, category, amount, month, year
                        )
                    message = f"{category} budget updated successfully."
                    message_type = "success"

    # ---- get budgets + spent for selected month/year ----
    budget_rows = db.execute(
        """
        SELECT 
            b.category,
            b.amount AS budget_amount,
            IFNULL(SUM(t.amount), 0) AS spent
        FROM budgets b
        LEFT JOIN transactions t
            ON b.user_id = t.user_id
            AND b.category = t.category
            AND t.type = 'expense'
            AND strftime('%m', t.date) = b.month
            AND strftime('%Y', t.date) = b.year
        WHERE b.user_id = ? AND b.month = ? AND b.year = ?
        GROUP BY b.category, b.amount
        ORDER BY b.category
        """,
        user_id, month, year
    )

    existing_map = {row["category"]: row for row in budget_rows}

    budgets_list = []
    total_budget = 0

    for cat in CATEGORIES:
        row = existing_map.get(cat)
        budget_amount = (row["budget_amount"] if row else 0) or 0
        spent = (row["spent"] if row else 0) or 0
        remaining = budget_amount - spent
        if budget_amount > 0:
            percent_used = min(100, max(0, int(round(spent / budget_amount * 100))))
        else:
            percent_used = 0

        total_budget += budget_amount

        budgets_list.append({
            "category": cat,
            "budget": round(budget_amount, 2),
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "percent_used": percent_used,
        })

    no_data_message = None
    if all(b["budget"] == 0 and b["spent"] == 0 for b in budgets_list):
        no_data_message = "No current data for the selected month and year."

    return render_template(
        "budgets.html",
        active="budgets",
        month=month,
        year=year,
        budgets=budgets_list,
        total_budget=round(total_budget, 2),
        message=message,
        message_type=message_type,
        no_data_message=no_data_message,
    )

#-------------------
# TRANSACTIONS
#-------------------
@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    user_id = session["user_id"]
    

    # Filters from query string
    month = request.args.get("month", "")
    year = request.args.get("year", "")
    merchant_search = (request.args.get("merchant") or "").strip()
    sort_by = request.args.get("sort_by", "newest")

    if not year:
        year = datetime.now().strftime("%Y")

    months = [
        ("01", "January"),
        ("02", "February"),
        ("03", "March"),
        ("04", "April"),
        ("05", "May"),
        ("06", "June"),
        ("07", "July"),
        ("08", "August"),
        ("09", "September"),
        ("10", "October"),
        ("11", "November"),
        ("12", "December"),
    ]
    years = ["2023", "2024", "2025", "2026", "2027"]

    base_query = """
        SELECT id, type, category, merchant, amount, date, notes
        FROM transactions
        WHERE user_id = ?
    """
    params = [user_id]

    if year:
        base_query += " AND strftime('%Y', date) = ?"
        params.append(year)

    if month:
        base_query += " AND strftime('%m', date) = ?"
        params.append(month)

    if merchant_search:
        base_query += " AND merchant LIKE ?"
        params.append(f"%{merchant_search}%")

    if sort_by == "oldest":
        order_clause = " ORDER BY date ASC, id ASC"
    elif sort_by == "amount_asc":
        order_clause = " ORDER BY amount ASC"
    elif sort_by == "amount_desc":
        order_clause = " ORDER BY amount DESC"
    elif sort_by == "merchant":
        order_clause = " ORDER BY merchant COLLATE NOCASE ASC, date DESC"
    else:
        order_clause = " ORDER BY date DESC, id DESC"

    transactions_rows = db.execute(base_query + order_clause, *params)

    sum_query = """
        SELECT type, IFNULL(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = ?
    """
    sum_params = [user_id]

    if year:
        sum_query += " AND strftime('%Y', date) = ?"
        sum_params.append(year)

    if month:
        sum_query += " AND strftime('%m', date) = ?"
        sum_params.append(month)

    if merchant_search:
        sum_query += " AND merchant LIKE ?"
        sum_params.append(f"%{merchant_search}%")

    sum_query += " GROUP BY type"

    totals = db.execute(sum_query, *sum_params)

    total_expenses = 0.0
    total_income = 0.0
    total_savings = 0.0

    for row in totals:
        if row["type"] == "expense":
            total_expenses = row["total"]
        elif row["type"] == "income":
            total_income = row["total"]
        elif row["type"] == "savings":
            total_savings = row["total"]
    row = row = db.execute("SELECT IFNULL(SUM(CASE WHEN type='savingswithdrawn' THEN amount ELSE 0 END), 0) as withdrawn FROM transactions WHERE user_id = ?",user_id)[0]
    total_savings_witdrawn = row["withdrawn"]        
    savings = total_savings - total_savings_witdrawn
    net = total_income - total_expenses - total_savings 

    month_label = None
    if month:
        for value, label in months:
            if value == month:
                month_label = label
                break

    return render_template(
        "transactions.html",
        active="transactions",
        transactions=transactions_rows,
        total_expenses=total_expenses,
        total_income=total_income,
        total_savings=savings,
        net=net,
        month=month,
        year=year,
        months=months,
        years=years,
        merchant_search=merchant_search,
        sort_by=sort_by,
        month_label=month_label,
        success_message=None,
        error_message=None,
    )

#---------------
# PROFILE
#---------------
# -------- GET /profile --------
@app.route("/profile")
@login_required
def profile():
    return render_profile()


# -------- UPDATE CURRENCY --------
@app.route("/profile/currency", methods=["POST"])
@login_required
def profile_currency():
    currency = request.form.get("currency")

    if currency not in ("GBP", "EUR", "USD", "RON"):
        return render_profile(error_message="Invalid currency selected.")

    db.execute(
        "UPDATE users SET currency = ? WHERE id = ?",
        currency,
        session["user_id"]
    )

    session["currency"] = currency  # keep session in sync

    return render_profile(success_message="Currency successfully updated.")


# -------- UPDATE SAVINGS GOAL --------
@app.route("/profile/goal", methods=["POST"])
@login_required
def profile_goal():
    raw_goal = request.form.get("savings_goal")

    if not raw_goal:
        return render_profile(error_message="Please enter a savings goal.")

    try:
        goal = float(raw_goal)
    except ValueError:
        return render_profile(error_message="Savings goal must be a number.")

    db.execute(
        "UPDATE users SET savings_goal = ? WHERE id = ?",
        goal,
        session["user_id"]
    )

    return render_profile(success_message="Savings goal updated successfully.")


# -------- UPDATE MONTHLY BUDGET --------
@app.route("/profile/budget", methods=["POST"])
@login_required
def profile_budget():
    raw_budget = request.form.get("monthly_budget")

    if not raw_budget:
        return render_profile(error_message="Please enter a monthly budget.")

    try:
        budget = float(raw_budget)
    except ValueError:
        return render_profile(error_message="Monthly budget must be a number.")

    db.execute(
        "UPDATE users SET monthly_budget = ? WHERE id = ?",
        budget,
        session["user_id"]
    )

    return render_profile(success_message="Monthly budget updated successfully.")


# -------- CHANGE USERNAME --------
@app.route("/profile/username", methods=["POST"])
@login_required
def profile_username():
    user_id = session["user_id"]
    new_username = request.form.get("new_username")

    if not new_username or not new_username.strip():
        return render_profile(error_message="Please enter a new username.")

    rows = db.execute("SELECT id FROM users WHERE username = ?", new_username.strip())
    if rows:
        return render_profile(error_message="Username already taken.")

    db.execute(
        "UPDATE users SET username = ? WHERE id = ?",
        new_username.strip(),
        user_id
    )

    return render_profile(success_message="Username successfully updated.")


# -------- CHANGE PASSWORD --------
@app.route("/profile/password", methods=["POST"])
@login_required
def profile_password():
    user_id = session["user_id"]

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not current_password or not new_password or not confirm_password:
        return render_profile(error_message="Please fill in all password fields.")

    rows = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
    if len(rows) != 1:
        return render_profile(error_message="User not found.")

    stored_hash = rows[0]["hash"]

    if not check_password_hash(stored_hash, current_password):
        return render_profile(error_message="You entered an invalid current password.")

    if new_password != confirm_password:
        return render_profile(error_message="New passwords do not match.")

    new_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, user_id)

    return render_profile(success_message="Password successfully changed.")
