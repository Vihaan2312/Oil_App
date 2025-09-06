import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt

# Firestore Init
creds = st.secrets["firestore"]
st.write(creds)
db = firestore.Client.from_service_account_info(dict(creds))

# --- Fetch Rates Dynamically ---
rate_docs = db.collection("Rates").stream()
rates = {doc.id: doc.to_dict().get("Rate", 0) for doc in rate_docs}
oil_names = list(rates.keys())

# --- Fetch Customer Profiles ---
profiles_ref = db.collection("Profiles").stream()
customer_data = {doc.id: doc.to_dict() for doc in profiles_ref}
customer_names = [data["Name"] for data in customer_data.values()]
customer_phones = list(customer_data.keys())

# --- Page Title ---
st.set_page_config(page_title="🛢️ New Order Entry", page_icon="🛒", layout="centered")
st.title("🛒 Atulit Pure Cold Pressed Oil - New Order")
st.caption("Quickly place a customer order and auto-fill details.")

# --- Customer Name Input with Suggestions ---
st.subheader("👤 Customer Details")

name_input = st.text_input("Enter Customer Name")
matching_names = [n for n in customer_names if name_input.lower() in n.lower()] if name_input else customer_names

if matching_names and name_input:
    name = st.selectbox("Select or continue typing", options=[f"{name_input} (Typed)"] + matching_names, index=0)
    if name.endswith("(Typed)"):
        name = name_input
else:
    name = name_input

# --- Auto-fill Phone ---
phone = ""
if name in customer_names:
    phone = next(phone for phone, data in customer_data.items() if data["Name"] == name)
phone = st.text_input("📞 Phone Number", value=phone)

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
            "Status": 1,
            "TotalAmount": round(grand_total + dc, 2)
        }

        for oil in oil_names:
            order_data[oil] = quantities[oil]
            order_data[f"{oil}_Amount"] = round(amounts[oil], 2)

        db.collection("Orders").document(str(new_id)).set(order_data)

        if phone not in customer_phones:
            db.collection("Profiles").document(phone).set({
                "Name": name,
                "Phone no.": phone
            })
            st.success(f"🆕 New customer '{name}' added to profiles!")

        st.success(f"🎉 Order #{new_id} submitted successfully!")

