import streamlit as st
from google.cloud import firestore
import pandas as pd
import plotly.express as px
import json
from login_sidebar import show_sidebar
import Database as mdb

st.set_page_config(page_title=" Sales Analytics Dashboard", layout="wide", page_icon="📊")

# 🔐 Always show login sidebar
show_sidebar()

# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()  # stops the rest of the script from running

db = mdb.init()
rates = mdb.oil_load()

st.title("📊 Sales Analytics Dashboard")

# Fetch all orders from Firestore
orders = mdb.load()

# Convert to DataFrame
df = pd.DataFrame(orders)

# Ensure columns exist
df["Date"] = pd.to_datetime(df["Date"])
df["Total Sales"] = df["TotalAmount"]

# Total Orders & Sales
st.metric("📦 Total Orders", len(df))
st.metric("💰 Total Sales (₹)", df["Total Sales"].sum())

# Sales Over Time
sales_over_time = df.groupby(df["Date"].dt.date)["Total Sales"].sum().reset_index()
fig = px.line(sales_over_time, x="Date", y="Total Sales", title="📅 Sales Over Time", markers=True)
st.plotly_chart(fig)

# Most Popular Oil
a=0
oil_sales = {}
for oil in rates:
    name = oil.id
    for order in orders:
        try:
            a=a+int(order[str(name)]) 
        except:
            a=a  
    oil_sales[name] = a
    a=0
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
