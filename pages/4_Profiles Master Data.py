import streamlit as st
from google.cloud import firestore
import pandas as pd
import io
from datetime import datetime
from login_sidebar import show_sidebar
import Database as mdb

st.set_page_config(page_title="Customer Master Data", page_icon="👥", layout="wide")

# 🔐 Always show login sidebar
show_sidebar()

# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()  # stops the rest of the script from running

db = mdb.init()

st.title("👥 Customer Profiles")

# Status mapping
status_map = {
    1: "Ordered",
    2: "Delivered",
    3: "Payment Done"
}

# Fetch all customer profiles
profiles_ref = mdb.pro_load()
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

# 👉 Excel Export of Customer List
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='Customers')

st.download_button(
    label="📥 Download Customer List as Excel",
    data=excel_buffer.getvalue(),
    file_name=f"Customer_List_{datetime.now().date()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Show each customer with a "View Orders" button
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

            gq = order.get("GQ", 0)
            mq = order.get("MQ", 0)
            cq = order.get("CQ", 0)
            sq = order.get("SQ", 0)
            aq = order.get("AQ", 0)
            dc = order.get("DC", 0)

            ga = gq * 350
            ma = mq * 350
            ca = cq * 450
            sa = sq * 450
            aa = aq * 2500
            total = ga + ma + ca + sa + aa

            order.update({
                "GA": f"₹{ga}/-",
                "MA": f"₹{ma}/-",
                "CA": f"₹{ca}/-",
                "SA": f"₹{sa}/-",
                "AA": f"₹{aa}/-",
                "DC": dc,
                "Total": f"₹{total}/-"
            })

            orders.append(order)

        if orders:
            order_df = pd.DataFrame(orders)
            order_df["Date"] = pd.to_datetime(order_df["Date"])
            order_df["Order Date"] = order_df["Date"].dt.date
            order_df["Order Time"] = order_df["Date"].dt.time

            order_df = order_df.sort_values(by="Date", ascending=False).head(10)

            cols_order = [
                "Order ID", "Name", "Phone", "Order Date", "Order Time", "Status",
                "GQ", "GA", "MQ", "MA", "CQ", "CA", "SQ", "SA", "AQ", "AA", "DC", "Total"
            ]
            for col in cols_order:
                if col not in order_df.columns:
                    order_df[col] = 0

            order_df = order_df[cols_order]

            st.markdown(f"#### 🧾 Last 10 Orders by {row['Name']} ({row['Phone']})")
            st.dataframe(order_df, use_container_width=True)
        else:
            st.info("No orders found for this customer.")
