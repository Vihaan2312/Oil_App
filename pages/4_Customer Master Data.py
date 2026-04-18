
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

# --- Add Customer Button ---
if "show_add_customer" not in st.session_state:
    st.session_state.show_add_customer = False

if st.button("➕ Add Customer"):
    st.session_state.show_add_customer = not st.session_state.show_add_customer

# --- Add Customer Form ---
if st.session_state.show_add_customer:

    st.subheader("➕ Add New Customer")

    with st.form("add_customer_form"):

        new_name = st.text_input("Customer Name")

        new_phone = st.text_input(
            "📞 Phone Number",
            max_chars=10,
            placeholder="Enter 10 digit mobile number"
        )

        new_address = st.text_input("Address")

        submitted = st.form_submit_button("💾 Save Customer")

        if submitted:

            if not new_name or not new_phone:
                st.error("Please enter both name and phone number.")

            elif not new_phone.isdigit() or len(new_phone) != 10:
                st.error("Phone number must be exactly 10 digits.")

            else:
                db.collection("Profiles").document(new_phone).set({
                    "Name": new_name,
                    "Phone no.": new_phone,
                    "Address": new_address
                })

                st.success(f"✅ Customer '{new_name}' added successfully!")

                # Hide form after saving
                st.session_state.show_add_customer = False

                st.rerun()

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

    address = data.get("Address", "")

    customer_data.append({
        "Name": name,
        "Phone": phone,
        "Address": address,
        "Order Count": order_count
    })

df = pd.DataFrame(customer_data)

# 👉 Excel Export of Customer List
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df[["Name","Phone","Address","Order Count"]].to_excel(
        writer,
        index=False,
        sheet_name='Customers'
    )

st.download_button(
    label="📥 Download Customer List as Excel",
    data=excel_buffer.getvalue(),
    file_name=f"Customer_List_{datetime.now().date()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Show each customer with a "View Orders" button
for i, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([3, 3, 4, 2, 2])
    col1.write(row["Name"])
    col2.write(row["Phone"])
    col3.write(row["Address"])
    col4.write(f'{row["Order Count"]} orders')

    if col5.button("✏️ Edit", key=f"edit_{row['Phone']}"):
        st.session_state["edit_customer"] = row["Phone"]

    if "edit_customer" in st.session_state:

        phone = st.session_state["edit_customer"]

        profile_doc = db.collection("Profiles").document(phone).get()
        profile = profile_doc.to_dict()

        st.divider()
        st.subheader(f"✏️ Edit Customer: {profile.get('Name')}")

        with st.form("edit_customer_form"):

            new_name = st.text_input("Customer Name", value=profile.get("Name", ""))
            new_address = st.text_input("Address", value=profile.get("Address", ""))

            col1, col2 = st.columns(2)

            save = col1.form_submit_button("💾 Save Changes")
            cancel = col2.form_submit_button("Cancel")

            if save:
                db.collection("Profiles").document(phone).update({
                    "Name": new_name,
                    "Address": new_address
                })

                st.success("Customer updated successfully")

                del st.session_state["edit_customer"]
                st.rerun()

            if cancel:
                del st.session_state["edit_customer"]
                st.rerun()

        
