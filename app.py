
import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

# Keep the database in your project folder
DB_PATH = Path(__file__).parent / "expenses.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)


def add_expense(description, amount, category, expense_date):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO expenses
               (description, amount, category, expense_date)
               VALUES (?, ?, ?, ?)""",
            (description, amount, category, expense_date)
        )


def get_expenses():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC",
            conn
        )


def delete_expense(expense_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (int(expense_id),)
        )


init_db()

st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("💰 Personal Expense Tracker")
st.caption("Record, review, and manage your expenses.")

categories = [
    "Food", "Travel", "Shopping", "Bills",
    "Education", "Health", "Other"
]

with st.form("expense_form", clear_on_submit=True):
    st.subheader("Add a new expense")

    description = st.text_input("Description")
    amount = st.number_input(
        "Amount (₹)", min_value=0.0, step=10.0, format="%.2f"
    )
    category = st.selectbox("Category", categories)
    expense_date = st.date_input("Date", value=date.today())

    submitted = st.form_submit_button("Save expense")

    if submitted:
        if not description.strip():
            st.error("Please enter a description.")
        elif amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            add_expense(
                description.strip(),
                amount,
                category,
                expense_date.isoformat()
            )
            st.success("Expense saved!")
            st.rerun()

df = get_expenses()

st.divider()
st.subheader("Your spending summary")

if df.empty:
    st.info("No expenses yet. Add your first expense above.")
else:
    total = df["amount"].sum()
    count = len(df)
    average = total / count

    col1, col2, col3 = st.columns(3)
    col1.metric("Total spending", f"₹{total:,.2f}")
    col2.metric("Number of expenses", count)
    col3.metric("Average expense", f"₹{average:,.2f}")

    st.subheader("Spending by category")
    category_totals = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    st.bar_chart(category_totals)

    st.subheader("Filter expenses")
    selected_categories = st.multiselect(
        "Choose categories",
        categories,
        default=categories
    )

    filtered = df[df["category"].isin(selected_categories)]

    st.dataframe(
        filtered[
            ["expense_date", "description", "category", "amount"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Delete an expense")
    expense_options = {
        f"#{row.id} — {row.description} (₹{row.amount:.2f})": row.id
        for row in df.itertuples()
    }

    selected_expense = st.selectbox(
        "Select an expense to delete",
        options=list(expense_options.keys())
    )

    confirm_delete = st.checkbox(
        "I confirm that I want to delete this expense."
    )

    if st.button("Delete selected expense", type="secondary"):
        if confirm_delete:
            delete_expense(expense_options[selected_expense])
            st.success("Expense deleted.")
            st.rerun()
        else:
            st.warning("Please confirm before deleting.")