import streamlit as st
from google.cloud import firestore
import pandas as pd

# Firestore connection
db = firestore.Client.from_service_account_json("Firestore.json")

st.title("👥 Customer Profiles")

# Status mapping
status_map = {
    1: "Ordered",
    2: "Delivered",
    3: "Payment Done"
}

# Fetch all customer profiles
profiles_ref = db.collection("Profiles").stream()
customer_data = []

for doc in profiles_ref:
    data = doc.to_dict()
    phone = doc.id
    name = data.get("Name", "N/A")

    # Fetch number of orders
    orders_ref = db.collection("Orders").where("Phone", "==", phone).stream()
    orders = list(orders_ref)
    order_count = len(orders)

    customer_data.append({
        "Name": name,
        "Phone": phone,
        "Order Count": order_count
    })

df = pd.DataFrame(customer_data)

st.subheader("📋 Customer List")

# Add view button to each row
for i, row in df.iterrows():
    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
    col1.write(row["Name"])
    col2.write(row["Phone"])
    col3.write(f'{row["Order Count"]} orders')
    if col4.button("📄 View Orders", key=row["Phone"]):
        orders_ref = db.collection("Orders").where("Phone", "==", row["Phone"]).stream()
        orders = []

        for doc in orders_ref:
            order = doc.to_dict()
            order["Order ID"] = doc.id
            order["Status"] = status_map.get(order.get("Status"), "Unknown")
            order["Name"] = row["Name"]
            order["Phone"] = row["Phone"]
            order["GA"] = order.get("GQ", 0) * 350
            order["MA"] = order.get("MQ", 0) * 350
            order["CA"] = order.get("CQ", 0) * 450
            order["SA"] = order.get("SQ", 0) * 450
            order["AA"] = order.get("AQ", 0) * 2500
            order["Total"] = (
                order["GA"] + order["MA"] + order["CA"] + order["SA"] + order["AA"]
            )
            orders.append(order)

        if orders:
            order_df = pd.DataFrame(orders)
            order_df["Date"] = pd.to_datetime(order_df["Date"])
            order_df["Order Date"] = order_df["Date"].dt.date
            order_df["Order Time"] = order_df["Date"].dt.time

            final_cols = [
                "Order ID", "Name", "Phone", "Order Date", "Order Time", "Status",
                "GQ", "GA", "MQ", "MA", "CQ", "CA", "SQ", "SA", "AQ", "AA", "DC", "Total"
            ]
            for col in final_cols:
                if col not in order_df.columns:
                    order_df[col] = 0

            order_df = order_df[final_cols]

            st.markdown(f"#### 🧾 Orders by {row['Name']} ({row['Phone']})")
            st.dataframe(order_df, use_container_width=True)
        else:
            st.info("No orders found for this customer.")
