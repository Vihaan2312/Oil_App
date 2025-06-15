import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt

db = firestore.Client.from_service_account_json("Firestore.json")

# Fetch oil rates dynamically
rate_docs = db.collection("Rates").stream()
rates = {doc.id: doc.to_dict().get("Rate", 0) for doc in rate_docs}
oil_names = list(rates.keys())

# Fetch customer data
profiles_ref = db.collection("Profiles").stream()
customer_data = {doc.id: doc.to_dict() for doc in profiles_ref}
customer_names = [data["Name"] for data in customer_data.values()]
customer_phones = list(customer_data.keys())

# Name input with suggestion
name_input = st.text_input("Enter Customer Name")
matching_names = [n for n in customer_names if name_input.lower() in n.lower()] if name_input else customer_names
if matching_names and name_input:
    name = st.selectbox("Select or continue typing", options=[f"{name_input}(Typed)"] + matching_names, index=0)
else:
    name = name_input

# Auto-fill phone
phone = ""
if name in customer_names:
    phone = next(phone for phone, data in customer_data.items() if data["Name"] == name)
phone = st.text_input("Phone no.", value=phone)

# Date and time
date = st.date_input("Date")
time = st.time_input("Time")

# Dynamic oil inputs
st.subheader("🛒 Oil Order Details")
quantities = {}
amounts = {}
for oil in oil_names:
    qty = st.number_input(f"{oil} Quantity (L)", min_value=0.0, step=0.5, key=oil)
    quantities[oil] = qty
    amounts[oil] = qty * rates[oil]

# Delivery charge
dc = st.number_input("Delivery Charge (₹)", step=10.0)

# Order summary
st.divider()
st.write("**Name:**", name)
st.write("**Phone number:**", phone)
st.write("**Date & Time:**", f"{date} {time}")

# Summary table
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
        "Rate (₹/L)": f"₹{rate}/-",
        "Quantity (L)": qty,
        "Total (₹)": f"₹{total}/-"
    })

summary.append({"Oil": "Delivery Charge", "Total (₹)": f"₹{dc}/-"})
summary.append({"Oil": "Total", "Quantity (L)": total_liters, "Total (₹)": f"₹{grand_total + dc}/-"})

st.write(pd.DataFrame(summary), use_container_width=True)

# Submit button
if st.button("Submit"):
    date_time = dt.datetime.combine(date, time)
    new_id = max([int(i.id) for i in db.collection("Orders").stream()] + [0]) + 1

    order_data = {
        "Phone": phone,
        "Name": name,
        "Date": date_time,
        "DC": dc,
        "Status": 1,
        "TotalAmount": round(grand_total + dc, 2)  # Store total with delivery
    }

    # Add quantities and amounts dynamically
    for oil in oil_names:
        order_data[oil] = quantities[oil]  # Quantity
        order_data[f"{oil}_Amount"] = round(amounts[oil], 2)  # Total amount per oil

    db.collection("Orders").document(str(new_id)).set(order_data)

    if phone not in customer_phones:
        db.collection("Profiles").document(phone).set({
            "Name": name,
            "Phone no.": phone
        })
        st.success(f"🆕 New customer '{name}' added!")

    st.success("🎉 Order submitted successfully!")
