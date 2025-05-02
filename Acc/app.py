import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ===================== Ledger App =====================
def run_ledger_app():
    st.title("📒 Simple Ledger App")

    if "ledger" not in st.session_state:
        st.session_state.ledger = pd.DataFrame(columns=[
            "Date", "Description", "Amount", "Transaction Type",
            "Account", "Debit", "Credit"
        ])

    accounts = [
        "Cash", "Accounts Receivable", "Inventory", "Equipment",
        "Accounts Payable", "Unearned Revenue", "Common Stock", "Retained Earnings",
        "Sales Revenue", "Rent Expense", "Utilities Expense", "Dividends"
    ]
    txn_types = ["Paid", "Received"]

    # ========== Form for Data Entry ==========
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            account = st.selectbox("Account", accounts)
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            txn_type = st.selectbox("Transaction Type", txn_types)
        with col2:
            date = st.date_input("Date")
            description = st.text_input("Description")
        submitted = st.form_submit_button("Add Transaction")

    if submitted:
        debit, credit = 0, 0
        if txn_type == "Paid":
            debit = 0 if account in ["Cash", "Inventory", "Equipment", "Rent Expense", "Utilities Expense", "Dividends"] else amount
            credit = amount if debit == 0 else 0
        else:
            debit = amount if account in ["Cash", "Inventory", "Equipment", "Rent Expense", "Utilities Expense", "Dividends"] else 0
            credit = 0 if debit else amount

        data = {
            "date": str(date),
            "description": description.strip(),
            "amount": float(amount),
            "transaction_type": txn_type,
            "account": account,
            "debit": float(debit),
            "credit": float(credit),
            "user_id": st.session_state.user.user.id
        }

        required_fields = ["date", "amount", "transaction_type", "account"]
        missing_fields = [k for k in required_fields if data.get(k) in [None, "", 0]]

        if missing_fields:
            st.warning(f"⚠️ Please fill out all required fields: {', '.join(missing_fields)}")
        else:
            try:
                supabase.table("transactions").insert(data).execute()
                st.success("✅ Transaction successfully saved in Supabase.")
            except Exception as e:
                st.warning(f"⚠️ Something went wrong while saving the transaction: {e}")

    # ========== Load Transactions for Logged-in User ==========
    try:
        response = supabase.table("transactions") \
            .select("*") \
            .eq("user_id", st.session_state.user.user.id) \
            .execute()
    except:
        response = None

    if response and response.data:
        df = pd.DataFrame(response.data)
        st.subheader("📊 General Ledger")
        st.dataframe(df)

        # ========== Trial Balance ==========
        st.subheader("📏 Trial Balance")
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0)
        total_debit = df["debit"].sum()
        total_credit = df["credit"].sum()
        st.metric("Total Debit", f"{total_debit:,.2f}")
        st.metric("Total Credit", f"{total_credit:,.2f}")

        if total_debit == total_credit:
            st.success("✅ Ledger is balanced.")
        else:
            st.error(f"❌ Unbalanced: Credit exceeds Debit by ${abs(total_credit - total_debit):,.2f}")

        # ========== Delete Transaction ==========
        st.subheader("🗑️ Delete Transaction")

        options = [f"{i} | {row['date']} | {row['account']} | {row['amount']} {row['transaction_type']}"
                   for i, row in df.iterrows()]
        selected_option = st.selectbox("Select a transaction to delete:", options)
        selected_index = int(selected_option.split(" | ")[0])
        selected_row = df.iloc[selected_index]

        if st.button("Delete Selected Transaction"):
            try:
                supabase.table("transactions").delete().eq("id", selected_row["id"]).execute()
                st.success(f"✅ Deleted transaction #{selected_index}")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Failed to delete: {e}")

        # ========== Filter by Account ==========
        st.subheader("🔍 Filter by Account")

        unique_accounts = df["account"].dropna().unique().tolist()

        if unique_accounts:
            selected_account = st.selectbox("Select an account to filter:", unique_accounts)
            filtered_df = df[df["account"] == selected_account]
            st.write(f"🔎 Transactions for **{selected_account}**:")
            st.dataframe(filtered_df)
        else:
            st.info("No accounts available yet.")

# ===================== Authentication =====================
st.title("🔐 Login or Sign Up")

auth_mode = st.radio("Choose:", ["Login", "Sign Up"], horizontal=True)
email = st.text_input("Email", key="email")
password = st.text_input("Password (min 6 chars)", type="password", key="password")

if st.button(auth_mode):
    if auth_mode == "Login":
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = user
            st.success("✅ Logged in successfully.")
        except Exception as e:
            st.error(f"❌ Login failed: {e}")
    else:
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            st.success("✅ Signed up successfully. Please check your email.")
        except Exception as e:
            st.error(f"❌ Sign-up failed: {e}")

# ===================== Run App =====================
if "user" in st.session_state:
    st.success(f"🔓 Logged in as {st.session_state.user.user.email}")
    run_ledger_app()
else:
    st.warning("Please log in to continue.")
