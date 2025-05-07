import streamlit as st
import pandas as pd
import os
import hashlib
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# ✅ Custom page config
st.set_page_config(
    page_title="prhx - Simple Ledger App",
    page_icon="🐝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ✅ Background honeycomb image (faint)
st.markdown("""
<style>
/* 🐝 Background honeycomb image faint */
body::before {
    content: "";
    background-image: url('https://raw.githubusercontent.com/prhxm/ledger-app/main/assets/honeycomb.png');
    background-repeat: no-repeat;
    background-position: center;
    background-size: 300px;
    opacity: 0.03;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 0;
}

/* 🐝 Make sure content stays above */
.login-container, .stApp {
    position: relative;
    z-index: 1;
}

</style>
""", unsafe_allow_html=True)

# ✅ Styling
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Comic Sans MS", cursive, sans-serif;
    color: #f9d342;
    background-color: #111111;
}
input, textarea, select {
    background-color: #222 !important;
    color: #f9d342 !important;
    border: 1px solid #f9d342 !important;
    border-radius: 10px;
}
button[kind="primary"] {
    background-color: #f9d342 !important;
    color: #000 !important;
    border-radius: 10px;
    font-weight: bold;
}
.stTitle {
    font-size: 2.5rem;
    color: #f9d342;
    font-weight: bold;
}
.login-container {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    margin-top: 2rem;
}
.login-form {
    flex: 1;
    min-width: 300px;
}
.honeycomb-img {
    flex: 1;
    text-align: right;
}
.honeycomb-img img {
    width: 320px;
    max-width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ✅ UI Header
st.markdown("<div style='text-align:center; font-size: 3rem;'>🐝 &nbsp; 🐝</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:right; color:#f9d342; font-size: 1.1rem; font-style: italic;'>Stay sharp, stay curious — your balance begins here. 🐝</div>", unsafe_allow_html=True)

# ✅ Layout container start
st.markdown("""
<div class="login-container">
    <div class="login-form">
""", unsafe_allow_html=True)

# ✅ Supabase setup
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ✅ Auth helpers
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    with open("Acc/users.json", "r") as f:
        return json.load(f)

users = load_users()

# ✅ Login form
def simple_login():
    st.title("Easily Reach 🪄")

    st.markdown(
        """
        <div class="login-container">
            <div class="login-form">
        """,
        unsafe_allow_html=True
    )

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

#comment
   ''' st.markdown(
        """
            </div>
            <div class="honeycomb-img">
                <img src="https://raw.githubusercontent.com/prhxm/ledger-app/main/assets/honeycomb.png">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )'''

    if st.button("Login / Register"):
        if not username or not password:
            st.warning("Please Enter Both Username and Password. 🌱")
            return

        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data:
            user = response.data[0]
            if user["password"] == hash_password(password):
                st.session_state.user = user
                st.success(f"Welcome {username} 👍")
                st.rerun()
            else:
                st.error("Incorrect Password. 🖐️")
        else:
            new_user = {"username": username, "password": hash_password(password)}
            try:
                result = supabase.table("users").insert(new_user).execute()
                st.write("🧾 Insert Result:", result)
            except Exception as e:
                st.error(f"Insert failed: {e}")
                return
            if result.get("error") is None:
                st.session_state.user = result.data[0]
                st.success(f"You Just Joined Us, {username} 🫶")
                st.rerun()
            else:
                st.error("Failed to Register... ❌")


# ===================== Ledger App =====================
def run_ledger_app():
    st.title("Simple Ledger App 📒")

    if "ledger" not in st.session_state:
        st.session_state.ledger = pd.DataFrame(columns=[
            "Date", "Description", "Amount", "Transaction Type",
            "Account", "Debit", "Credit"
        ])

    accounts = [
        # Assets
        "Cash", "Bank", "Accounts Receivable", "Inventory", "Prepaid Expenses",
        "Equipment", "Buildings", "Land", "Vehicles", "Investments", "Accumulated Depreciation",
    
        # Liabilities
        "Accounts Payable", "Salaries Payable", "Taxes Payable", "Unearned Revenue",
        "Interest Payable", "Loans Payable", "Bonds Payable",
    
        # Equity
        "Common Stock", "Preferred Stock", "Retained Earnings", "Dividends",
        "Treasury Stock", "Additional Paid-In Capital",
    
        # Revenues
        "Sales Revenue", "Service Revenue", "Interest Revenue", "Rental Revenue", "Gain on Sale of Assets",
    
        # Expenses
        "Rent Expense", "Utilities Expense", "Salaries Expense", "Depreciation Expense",
        "Advertising Expense", "Supplies Expense", "Interest Expense", "Insurance Expense",
        "Cost of Goods Sold"
    ]

    txn_types = ["Reduced (-)", "Increased (+)"]
    

    # ========== Form for Data Entry ==========
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            account = st.selectbox("Account", accounts)
            amount = st.number_input("Amount", min_value=0.0, format="%.2f", key="amount_input", step= 1.0)
            txn_type = st.selectbox("Transaction Type", txn_types)
        with col2:
            date = st.date_input("Date")
            description = st.text_input("Description")
            
        submitted = st.form_submit_button("Add Transaction")

    if submitted:
        debit, credit = 0, 0
        if txn_type == "Reduced (-)":
            debit = 0 if account in  [
    # Assets
    "Cash", "Bank", "Accounts Receivable", "Inventory", "Prepaid Expenses",
    "Equipment", "Buildings", "Land", "Vehicles", "Investments",

    # Expenses
    "Rent Expense", "Utilities Expense", "Salaries Expense", "Depreciation Expense",
    "Advertising Expense", "Supplies Expense", "Interest Expense", "Insurance Expense",
    "Cost of Goods Sold",

    # Equity (Drawings)
    "Dividends", "Treasury Stock"
] else amount
            credit = amount if debit == 0 else 0
        else:
            debit = amount if account in [ 
    # Assets
    "Cash", "Bank", "Accounts Receivable", "Inventory", "Prepaid Expenses",
    "Equipment", "Buildings", "Land", "Vehicles", "Investments",

    # Expenses
    "Rent Expense", "Utilities Expense", "Salaries Expense", "Depreciation Expense",
    "Advertising Expense", "Supplies Expense", "Interest Expense", "Insurance Expense",
    "Cost of Goods Sold",

    # Equity (Drawings)
    "Dividends", "Treasury Stock"
] else 0
            credit = 0 if debit else amount

        data = {
            "date": str(date),
            "description": description.strip(),
            "amount": float(amount),
            "transaction_type": txn_type,
            "account": account,
            "debit": float(debit),
            "credit": float(credit),
            "user_id": st.session_state.user["id"]
        }
        #st.write("Current user_id from session:", st.session_state.user.user.id)
        
        required_fields = ["date", "amount", "transaction_type", "account"]
        missing_fields = [k for k in required_fields if data.get(k) in [None, "", 0]]

        if missing_fields:
            st.warning(f"Please fill out all required fields: {', '.join(missing_fields)} ⚠️")
        else:
            try:
                supabase.table("transactions").insert(data).execute()
                st.success("Transaction successfully saved in Supabase. ✅")
            except Exception as e:
                st.warning(f"Something went wrong while saving the transaction: {e} ⚠️")

    # ========== Load Transactions for Logged-in User ==========
    try:
        response = supabase.table("transactions") \
            .select("*") \
            .eq("user_id", st.session_state.user["id"]) \
            .execute()
    except:
        response = None

    if response and response.data:
        df = pd.DataFrame(response.data)
        st.subheader("General Ledger 📊")
        columns_to_display = [col for col in df.columns if col not in ["id", "user_id"]]
        st.dataframe(df[columns_to_display])

        # ========== Trial Balance ==========
        st.subheader("📏 Trial Balance")
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0)
        total_debit = df["debit"].sum()
        total_credit = df["credit"].sum()
        st.metric("Total Debit", f"{total_debit:,.2f}")
        st.metric("Total Credit", f"{total_credit:,.2f}")

        if total_debit == total_credit:
            st.success("Ledger is balanced. ✅")
        else:
            st.error(f"Unbalanced: Credit exceeds Debit by ${abs(total_credit - total_debit):,.2f} ❌")

        # ========== Delete Transaction ==========
        st.subheader("Delete Transaction 🗑️")

        options = [f"{i} | {row['date']} | {row['account']} | {row['amount']} {row['transaction_type']}"
                   for i, row in df.iterrows()]
        selected_option = st.selectbox("Select a transaction to delete:", options)
        selected_index = int(selected_option.split(" | ")[0])
        selected_row = df.iloc[selected_index]

        if st.button("Delete Selected Transaction"):
            try:
                supabase.table("transactions").delete().eq("id", selected_row["id"]).execute()
                st.success(f"Deleted transaction #{selected_index} ✅")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to delete: {e} ❌")

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

# ===================== Run App =====================
if "user" in st.session_state:
    st.success(f"You Logged in {st.session_state.user['username']} 🔓☕")
    run_ledger_app()
else:
    st.warning("Please log in to continue. 🧑‍💻")
    simple_login()
