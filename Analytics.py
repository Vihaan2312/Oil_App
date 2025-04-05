import streamlit as st
from google.cloud import firestore
import pandas as pd
import plotly.express as px

# Initialize Firestore
db = firestore.Client.from_service_account_json("Firestore.json")

st.title("📊 Sales Analytics Dashboard")

# Fetch all orders from Firestore
orders_ref = db.collection("Orders").stream()
orders = [order.to_dict() for order in orders_ref]

# Convert to DataFrame
df = pd.DataFrame(orders)

# Ensure columns exist
df["Date"] = pd.to_datetime(df["Date"])
df["Total Sales"] = (df["CQ"] * 400) + (df["GQ"] * 350) + (df["MQ"] * 350) + (df["SQ"] * 450) + (df["AQ"] * 2500)

# Total Orders & Sales
st.metric("📦 Total Orders", len(df))
st.metric("💰 Total Sales (₹)", df["Total Sales"].sum())

# Sales Over Time
sales_over_time = df.groupby(df["Date"].dt.date)["Total Sales"].sum().reset_index()
fig = px.line(sales_over_time, x="Date", y="Total Sales", title="📅 Sales Over Time", markers=True)
st.plotly_chart(fig)

# Most Popular Oil
oil_sales = {
    "Coconut": df["CQ"].sum(),
    "Groundnut": df["GQ"].sum(),
    "Mustard": df["MQ"].sum(),
    "Sesame": df["SQ"].sum(),
    "Almond": df["AQ"].sum(),
}
popular_oil = max(oil_sales, key=oil_sales.get)
st.metric("🏆 Most Popular Oil", popular_oil)

# Oil Sales Breakdown
oil_df = pd.DataFrame(oil_sales.items(), columns=["Oil", "Total Liters Sold"])
fig_oil = px.bar(oil_df, x="Oil", y="Total Liters Sold", title="🔹 Oil Sales Breakdown", text="Total Liters Sold")
st.plotly_chart(fig_oil)


