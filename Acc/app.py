import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)


st.title("📒 Simple Ledger App")

# Session state to store transactions
if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame(columns=[
        "Date", "Description", "Amount", "Transaction Type", "Account", "Debit", "Credit"
    ])

# Dropdown options
accounts = ["Cash", "Accounts Receivable", "Inventory", "Equipment",
            "Accounts Payable", "Unearned Revenue",
            "Common Stock", "Retained Earnings",
            "Sales Revenue", "Rent Expense", "Utilities Expense", "Dividends"]
txn_types = ["Paid", "Received"]

# Input Form
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
# Logic
if submitted:
    if amount > 0 and txn_type in ["Paid", "Received"] and account:
        debit = 0
        credit = 0

        if txn_type == "Paid":
            debit = 0 if account in ["Cash", "Inventory", "Equipment", "Rent Expense", "Utilities Expense", "Dividends"] else amount
            credit = amount if debit == 0 else 0
        else:  # Received
            debit = amount if account in ["Cash", "Inventory", "Equipment", "Rent Expense", "Utilities Expense", "Dividends"] else 0
            credit = 0 if debit else amount

        new_row = {
            "Date": date,
            "Description": description,
            "Amount": amount,
            "Transaction Type": txn_type,
            "Account": account,
            "Debit": debit,
            "Credit": credit
        }

        st.session_state.ledger.loc[len(st.session_state.ledger)] = new_row
        st.success("Transaction added!")

        # Send to Supabase
        data = {
            "date": str(date),
            "description": description,
            "amount": amount,
            "transaction_type": txn_type,
            "account": account,
            "debit": debit,
            "credit": credit
        }
        supabase.table("transactions").insert(data).execute()

    else:
        st.error("Please fill out all fields and enter a valid amount greater than 0.")
# -----------------------
# Trial Balance Check
# -----------------------
st.subheader("📊 Trial Balance")

df = st.session_state.ledger.copy()
df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce").fillna(0)
df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce").fillna(0)

total_debit = df["Debit"].sum()
total_credit = df["Credit"].sum()

st.write(f"**Total Debit:** ${total_debit:,.4f}")
st.write(f"**Total Credit:** ${total_credit:,.4f}")

if abs(total_debit - total_credit) < 0.0001:
    st.success("✅ Ledger is balanced.")
elif total_debit > total_credit:
    st.error(f"❌ Unbalanced: Debit exceeds Credit by {total_debit - total_credit:.4f}")
else:
    st.error(f"❌ Unbalanced: Credit exceeds Debit by {total_credit - total_debit:.4f}")

# Show Ledger Table
st.subheader("🧾 General Ledger")
st.dataframe(st.session_state.ledger)
# -----------------------
# 🗑️ Delete a Transaction (Clean Dropdown)
# -----------------------
st.subheader("🗑️ Delete Transaction")

df = st.session_state.ledger.copy()

if not df.empty:
    options = [f"{i} | {row['Date']} | {row['Account']} | {row['Amount']} {row['Transaction Type']}"
               for i, row in df.iterrows()]
    selected_option = st.selectbox("Select a transaction to delete:", options)
    selected_index = int(selected_option.split(" | ")[0])

    if st.button("Delete Selected Transaction"):
        st.session_state.ledger.drop(selected_index, inplace=True)
        st.session_state.ledger.reset_index(drop=True, inplace=True)
        st.success(f"Deleted transaction #{selected_index}")
        st.experimental_rerun()
else:
    st.info("No transactions available.")
# -----------------------
# Filter by Account
# -----------------------
st.subheader("🔍 Filter by Account")

unique_accounts = st.session_state.ledger["Account"].dropna().unique().tolist()

if unique_accounts:
    selected_account = st.selectbox("Select an account to filter:", unique_accounts)
    filtered_df = st.session_state.ledger[st.session_state.ledger["Account"] == selected_account]
    st.write(f"🔎 Transactions for **{selected_account}**:")
    st.dataframe(filtered_df)
else:
    st.info("No accounts available yet.")
# -----------------------
# Edit a Transaction
# -----------------------
st.subheader("✏️ Edit Transaction")

if not st.session_state.ledger.empty:
    row_to_edit = st.number_input("Enter row index to edit:", min_value=0, max_value=len(st.session_state.ledger)-1, step=1)
    
    if st.button("Load Row for Edit"):
        row_data = st.session_state.ledger.loc[row_to_edit]
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_account = st.selectbox("Account", accounts, index=accounts.index(row_data["Account"]))
                new_amount = st.number_input("Amount", value=float(row_data["Amount"]), format="%.2f")
                new_type = st.selectbox("Transaction Type", txn_types, index=txn_types.index(row_data["Transaction Type"]))
            with col2:
                new_date = st.date_input("Date", value=pd.to_datetime(row_data["Date"]))
                new_desc = st.text_input("Description", value=row_data["Description"])
            save_edit = st.form_submit_button("Save Changes")
        
        if save_edit:
            # Debit  Credit
            if new_type == "Paid":
                if new_account in ["Cash", "Inventory", "Equipment", "Rent Expense", "Utilities Expense", "Dividends"]:
                    debit = 0
                    credit = new_amount
                else:
                    debit = new_amount
                    credit = 0
            else:
                if new_account in ["Cash", "Inventory", "Equipment", "Rent Expense", "Utilities Expense", "Dividends"]:
                    debit = new_amount
                    credit = 0
                else:
                    debit = 0
                    credit = new_amount

            st.session_state.ledger.loc[row_to_edit] = [
                new_date, new_desc, new_amount, new_type, new_account, debit, credit
            ]
            st.success("✅ Transaction updated.")

