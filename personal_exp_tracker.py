import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define keywords for auto-categorization
CATEGORY_KEYWORDS = {
    "Groceries": ["bigbasket", "grofers", "more", "dmart", "spencer"],
    "Eating Out": ["zomato", "swiggy", "dominos", "pizza", "restaurant", "eatery"],
    "Entertainment": ["netflix", "spotify", "hotstar", "prime", "bookmyshow"],
    "Utilities": ["electricity", "water", "gas", "bescom", "bills", "power"],
    "Transport": ["uber", "ola", "fuel", "petrol", "diesel", "metro"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "snapdeal"],
    "Healthcare": ["pharmacy", "hospital", "clinic", "apollo", "medlife"],
    "Education": ["fees", "tuition", "course", "udemy", "byjus"],
    "Salary": ["salary", "credited", "income"],
    "Rent": ["rent", "landlord"],
    "Miscellaneous": []
}

def detect_category(narration):
    narration = str(narration).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in narration:
                return category
    return "Miscellaneous"

# Streamlit Page Setup
st.set_page_config(page_title="Personal Finance Tracker", layout="wide")
st.title("📊 Personal Finance Tracker with Auto-Categorization")

# Upload bank statement CSV/XLSX
uploaded_file = st.file_uploader("Upload your bank statement", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Detect file type and read accordingly
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:  # .xlsx
        df = pd.read_excel(uploaded_file)

    # Handle narration column
    if 'Narration' not in df.columns:
        if 'Description' in df.columns:
            df['Narration'] = df['Description']
        else:
            st.error("Neither 'Narration' nor 'Description' column found in the uploaded file.")
            st.stop()

    # Handle date column
    if 'Date' not in df.columns:
        if 'Txn Date' in df.columns:
            df['Date'] = df['Txn Date']
        elif 'Value Date' in df.columns:
            df['Date'] = df['Value Date']
        else:
            st.error("No date column found. Please include 'Date', 'Txn Date', or 'Value Date' in your file.")
            st.stop()

    # ✅ Convert to datetime explicitly
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Expecting Debit and Credit columns
    try:
        df['Amount'] = df['Debit'].fillna(0) - df['Credit'].fillna(0)
        df = df[df['Amount'] > 0]  # Keep only expenses

        df['Category'] = df['Narration'].apply(detect_category)
        df = df[['Date', 'Category', 'Amount']]
        df.dropna(subset=['Date', 'Amount'], inplace=True)

        # ✅ Now safe to use .dt
        df['Month'] = df['Date'].dt.to_period('M')
        df['Year'] = df['Date'].dt.year

        # Sidebar Filters
        st.sidebar.header("Filters")
        unique_categories = df['Category'].unique()
        selected_categories = st.sidebar.multiselect("Select Categories", unique_categories, default=unique_categories)
        df = df[df['Category'].isin(selected_categories)]

        # Summary Metrics
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Spend", f"₹{df['Amount'].sum():,.2f}")
        col2.metric("Average per Transaction", f"₹{df['Amount'].mean():,.2f}")
        col3.metric("Transactions", f"{len(df)}")

        # Monthly Expense Trend
        st.subheader("📈 Monthly Expense Trend")
        monthly_trend = df.groupby('Month')['Amount'].sum().reset_index()
        monthly_trend['Month'] = monthly_trend['Month'].astype(str)

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=monthly_trend, x='Month', y='Amount', marker='o', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Category-wise Breakdown
        st.subheader("🧾 Category-wise Expense Breakdown")
        category_totals = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        category_totals.plot(kind='bar', ax=ax2)
        plt.ylabel("Amount (₹)")
        plt.xticks(rotation=45)
        st.pyplot(fig2)

        # Pie Chart
        st.subheader("📌 Pie Chart of Expenses by Category")
        fig3, ax3 = plt.subplots()
        category_totals.plot(kind='pie', autopct='%1.1f%%', ax=ax3)
        ax3.set_ylabel("")
        st.pyplot(fig3)

        # Full Data Table
        st.subheader("🧾 Full Data Table")
        st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a bank statement file (CSV or Excel) to begin.")
