import streamlit as st
from google.cloud import firestore
import pandas as pd
import plotly.express as px
import json

# Firestore Init
creds = st.secrets["firestore"]
db = firestore.Client.from_service_account_info(dict(creds))

st.set_page_config(page_title=" Sales Analytics Dashboard", layout="wide", page_icon="📊")

st.title("📊 Sales Analytics Dashboard")

# Fetch all orders from Firestore
orders_ref = db.collection("Orders").stream()
orders = [order.to_dict() for order in orders_ref]

# Convert to DataFrame
df = pd.DataFrame(orders)

# Ensure columns exist
df["Date"] = pd.to_datetime(df["Date"])
df["Total Sales"] = (df["CQ"] * 450) + (df["GQ"] * 350) + (df["MQ"] * 350) + (df["SQ"] * 450) + (df["AQ"] * 2500)

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

# 🔻 ORDER STATUS OVERVIEW
st.subheader("📦 Order Status Overview")

# Map numeric statuses to labels
status_labels = {1: "Ordered", 2: "Delivered", 3: "Paid"}
df["Status Label"] = df["Status"].map(status_labels).fillna("Unknown")

status_counts = df["Status Label"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]

fig_status = px.bar(
    status_counts,
    x="Status",
    y="Count",
    title="📊 Order Status Distribution",
    text="Count",
    color="Status"
)
st.plotly_chart(fig_status)
