import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
from login_sidebar import show_sidebar
import Database as mdb

st.set_page_config(page_title="🛢️ Create Order", page_icon="🛒", layout="centered")

# 🔐 Always show login sidebar
show_sidebar()

# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()  # stops the rest of the script from running

db = mdb.init()

# --- Fetch Rates Dynamically ---
rate_docs = db.collection("Rates").stream()
rates = {doc.id: doc.to_dict().get("Rate", 0) for doc in rate_docs}
oil_names = list(rates.keys())

# --- Fetch Customer Profiles ---
profiles_ref = mdb.pro_load()
customer_data = {doc.id: doc.to_dict() for doc in profiles_ref}
customer_names = [data["Name"] for data in customer_data.values()]
customer_phones = list(customer_data.keys())

# --- Page Title ---
st.title("🛒 Atulit Pure Cold Pressed Oil - Create   Order")
st.caption("Quickly place a customer order.")

# --- Customer Details ---
st.subheader("👤 Customer Details")

customer_type = st.radio(
    "Select Customer Type",
    ["Existing Customer", "New Customer"]
)

# --- EXISTING CUSTOMER ---
if customer_type == "Existing Customer":

    selected_name = st.selectbox(
        "Select Customer",
        options=customer_names
    )

    # Fetch profile data
    profile = next(
        data for data in customer_data.values()
        if data["Name"] == selected_name
    )

    name = profile["Name"]

    phone = next(
        phone for phone, data in customer_data.items()
        if data["Name"] == selected_name
    )

    saved_address = profile.get("Address", "")

    # Locked fields
    st.text_input("Customer Name", value=name, disabled=True)
    st.text_input("📞 Phone Number", value=phone, disabled=True)

    # Editable address
    address = st.text_input("Address", value=saved_address)

    # Checkbox to update profile
    update_profile_address = st.checkbox("Save this address as the default for this customer")
# --- NEW CUSTOMER ---
else:

    name = st.text_input("Customer Name")

    phone = st.text_input(
        "📞 Phone Number",
        max_chars=10,
        placeholder="Enter 10 digit mobile number"
    )

    address = st.text_input("Address")

    # Phone validation
    phone_valid = False
    if phone:
        if not phone.isdigit():
            st.error("Phone number should contain only digits.")
        elif len(phone) != 10:
            st.warning("Phone number must be exactly 10 digits.")
        else:
            phone_valid = True
            
# --- Date and Time ---
st.subheader("📅 Order Date & Time")
date = st.date_input("Date", value=dt.date.today())
time = st.time_input("Time", value=dt.datetime.now().time())

# --- Oil Order Section ---
st.subheader("🛢️ Oil Order Details")
quantities = {}
amounts = {}

for oil in oil_names:
    qty = st.number_input(f"{oil} Quantity (Litres)", min_value=0.0, step=0.5, key=oil)
    quantities[oil] = qty
    amounts[oil] = qty * rates[oil]

# --- Delivery Charge ---
dc = st.number_input("🚚 Delivery Charge (Rs.)", min_value=0.0, step=10.0)

# --- Order Summary ---
st.divider()
st.subheader("📊 Order Summary")

st.write(f"**👤 Name:** {name}")
st.write(f"**📞 Phone Number:** {phone}")
st.write(f"**🗓️ Date & Time:** {date} {time}")
st.write(f"**📄 Address:** {address}")

# --- Summary Table ---
summary = []
grand_total = 0
total_liters = 0

for oil in oil_names:
    rate = rates[oil]
    qty = quantities[oil]
    total = rate * qty
    grand_total += total
    total_liters += qty
    summary.append({
        "Oil": oil,
        "Rate (Rs./Litre)": f"Rs. {rate}/-",
        "Quantity (Litre)": qty,
        "Total (Rs.)": f"Rs. {total}/-"
    })

# Add delivery charge and grand total
summary.append({"Oil": "🚚 Delivery Charge", "Total (Rs.)": f"Rs. {dc}/-"})
summary.append({"Oil": "💰 Total", "Quantity (Litre)": total_liters, "Total (Rs.)": f"Rs. {grand_total + dc}/-"})

st.dataframe(pd.DataFrame(summary), use_container_width=True)

# --- Submit Button ---
st.divider()
if st.button("✅ Submit Order"):
    if not name or not phone:
        st.error("⚠️ Please enter both Customer Name and Phone Number.")
    else:
        date_time = dt.datetime.combine(date, time)

        existing_orders = db.collection("Orders").stream()
        new_id = max([int(doc.id) for doc in existing_orders] + [0]) + 1

        order_data = {
            "Phone": phone,
            "Name": name,
            "Date": date_time,
            "DC": dc,
            "Address": address,
            "Status": 1,
            "TotalAmount": round(grand_total + dc, 2)
        }

        for oil in oil_names:
            order_data[oil] = quantities[oil]
            order_data[f"{oil}_Amount"] = round(amounts[oil], 2)

        db.collection("Orders").document(str(new_id)).set(order_data)

        # Update address in profile if checkbox selected
        if customer_type == "Existing Customer" and update_profile_address:
            db.collection("Profiles").document(phone).update({
                "Address": address
            })

        # --- Update/Create Profile if New Customer selected ---
        if customer_type == "New Customer":

            db.collection("Profiles").document(phone).set({
                "Name": name,
                "Phone no.": phone,
                "Address": address
            })

            st.success(f"👤 Customer profile saved/updated for {name}")

        st.success(f"🎉 Order #{new_id} submitted successfully!")
