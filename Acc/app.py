import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ===================== App =====================
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
            "email": st.session_state.user.user.email  # 🔐 اضافه کردن ایمیل کاربر
        }

        # بررسی مقادیر خالی
        missing_fields = [k for k, v in data.items() if v in [None, "", 0] and k not in ["description"]]

        if missing_fields:
            st.warning(f"⚠️ لطفاً همه‌ی فیلدها را کامل کنید: {', '.join(missing_fields)}")
        else:
            try:
                supabase.table("transactions").insert(data).execute()
                st.success("✅ تراکنش با موفقیت ثبت شد.")
            except:
                pass  # بدون نمایش ارور

    # Load data for the current user
    try:
        response = supabase.table("transactions") \
            .select("*") \
            .eq("email", st.session_state.user.user.email) \
            .execute()
        if response.data:
            df = pd.DataFrame(response.data)
            st.subheader("📊 General Ledger")
            st.dataframe(df)

            st.subheader("📏 Trial Balance")
            df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce").fillna(0)
            df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0)
            total_debit = df["Debit"].sum()
            total_credit = df["Credit"].sum()
            st.metric("Total Debit", f"{total_debit:,.2f}")
            st.metric("Total Credit", f"{total_credit:,.2f}")
            if total_debit == total_credit:
                st.success("✅ Ledger is balanced.")
            else:
                st.error(f"❌ Unbalanced: Credit exceeds Debit by ${abs(total_credit - total_debit):,.2f}")
        else:
            st.info("ℹ️ هیچ تراکنشی ثبت نشده است.")
    except:
        st.warning("⚠️ بارگذاری اطلاعات با مشکل مواجه شد.")

# ===================== Auth =====================
st.title("🔐 Login or Sign Up")
auth_mode = st.radio("Choose:", ["Login", "Sign Up"], horizontal=True)
email = st.text_input("Email", key="email")
password = st.text_input("Password (min 4 chars)", type="password", key="password")

if st.button(auth_mode):
    if auth_mode == "Login":
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if user.session:
                st.session_state.user = user
                st.success("✅ Logged in successfully.")
            else:
                st.error("❌ Login failed. Invalid credentials.")
        except:
            st.error("❌ Login failed. Please try again.")
    else:
        try:
            user = supabase.auth.sign_up({"email": email, "password": password})
            st.success("✅ Signed up successfully. Please check your email.")
        except:
            st.error("❌ Sign-up failed. Try a different email.")

# ===================== Load App if Logged In =====================
if "user" in st.session_state:
    st.success(f"🔓 Logged in as {st.session_state.user.user.email}")
    run_ledger_app()
else:
    st.warning("Please log in to continue.")
