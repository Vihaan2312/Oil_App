import streamlit as st
from google.cloud import firestore
import datetime as dt
from login_sidebar import show_sidebar

st.set_page_config(page_title="Admin Home - Atulit Oil", page_icon="🛠️")

# 🔐 Always show login sidebar
show_sidebar()

params = st.experimental_get_query_params()
if params.get("logged_in") == ["true"]:
    st.experimental_set_query_params()  # clear it

# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()  # stops the rest of the script from running

# Firestore Init
creds = st.secrets["firestore"]
db = firestore.Client.from_service_account_info(dict(creds))

# Title
st.title("🛠️ Admin Dashboard - Atulit Oil")

st.markdown("Welcome, Admin. Use this dashboard to manage and monitor all oil orders efficiently.")

# Divider
st.markdown("---")

# 🔹 Quick Stats
st.subheader("📊 Quick Stats")

# Load all orders
orders = list(db.collection("Orders").stream())
data = [doc.to_dict() for doc in orders]

total_orders = len(data)
today_orders = sum(1 for d in data if d.get("Date") and d["Date"].date() == dt.date.today())
delivered = sum(1 for d in data if d.get("Status") == 2)
paid = sum(1 for d in data if d.get("Status") == 3)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orders", total_orders)
col2.metric("Orders Today", today_orders)
col3.metric("Delivered", delivered)
col4.metric("Payment Done", paid)

# Divider
st.markdown("---")

# 🔹 Quick Navigation
st.subheader("📂 Navigate Quickly")

st.markdown("""
- 📋 **[Go to Orders]** to view, update, or export orders  
- 🧾 **Generate Invoices** from individual order pages  
- 🔎 Use the filters in Orders to search by name, status, or date  
- 🧑‍💼 More admin tools coming soon...
""")

# Info message
st.info("Reminder: Only admins should access this dashboard. All actions are saved in the database in real-time.")
