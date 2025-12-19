from functools import wraps
from flask import redirect, session, render_template

# -------------------------
# AUTH HELPERS
# -------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#------------------------
# CLEANS TEXT MAKE IT UNIFORM
#------------------------
def clean_text(text):
    if not text:
        return None
    clean = " ".join(text.split())
    if not clean:
        return None
    return clean[0].upper() + clean[1:].lower()

#-----------------------
#CLEANS TITLE MAKE IT UNIFORM
#-----------------------
def clean_title(title):
    if not title:
        return None
    clean = " ".join(title.split())
    
    return clean[0].upper() + clean[1:].lower() if clean else clean


# -------------------------
# CURRENCY HELPERS
# -------------------------

def get_currency_symbol():
    """Return the symbol for the current user's currency code."""
    code = session.get("currency", "GBP")  # default GBP

    symbols = {
        "GBP": "£",
        "EUR": "€",
        "USD": "$",
        "RON": "lei",
    }
    return symbols.get(code, code)


def money(amount):
    """Format a number as money with the user's currency symbol."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return amount

    symbol = get_currency_symbol()
    return f"{symbol}{amount:,.2f}"
