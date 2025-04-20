import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
import json

# Initialize Firestore client
db = firestore.Client.from_service_account_json("Firestore.json")

# Fetch existing customers from Firestore
profiles_ref = db.collection("Profiles").stream()
customer_data = {doc.id: doc.to_dict() for doc in profiles_ref}
customer_names = [data["Name"] for data in customer_data.values()]
customer_phones = list(customer_data.keys())  # Phone numbers as document IDs

# Smart Name Input with Auto-Suggestions
name_input = st.text_input("Enter Customer Name")

# Filter matches dynamically
matching_names = [n for n in customer_names if name_input.lower() in n.lower()] if name_input else customer_names

# Selectbox for existing names (appears only when matches exist)
if matching_names and name_input:
    name = st.selectbox("Select or continue typing", options=[f"{name_input}(Typed)"] + matching_names, index=0)
else:
    name = name_input

# Auto-fill phone number if name exists
phone = ""
if name in customer_names:
    phone = next(phone for phone, data in customer_data.items() if data["Name"] == name)

# Phone number input (editable)
phone = st.text_input("Phone no.", value=phone)

# Order details
date = st.date_input("Date")
time = st.time_input("Time", value=dt.datetime.now().time())  # Default to current time

cq = st.number_input("Coconut Quantity")
gq = st.number_input("Groundnut Quantity")
mq = st.number_input("Mustard Quantity")
sq = st.number_input("Sesame Quantity")
aq = st.number_input("Almond Quantity")

st.divider()

# Display order summary
st.write("**Name:**", name)
st.write("**Phone number:**", phone)
st.write("**Date & Time:**", f"{date} {time}")

df = pd.DataFrame([
    {"Oil": "Coconut", "Rate": "₹400/- per liter", "Quantity": cq, "Total": f"₹{cq*400}/-"},
    {"Oil": "Groundnut", "Rate": "₹350/- per liter", "Quantity": gq, "Total": f"₹{gq*350}/-"},
    {"Oil": "Mustard", "Rate": "₹350/- per liter", "Quantity": mq, "Total": f"₹{mq*350}/-"},
    {"Oil": "Sesame", "Rate": "₹450/- per liter", "Quantity": sq, "Total": f"₹{sq*450}/-"},
    {"Oil": "Almond", "Rate": "₹625/- per 250ml", "Quantity": aq, "Total": f"₹{aq*2500}/-"},
    {"Oil": "Total:", "Quantity": cq+gq+mq+sq+aq, "Total": f"₹{(aq*2500)+(cq*400)+(gq*350)+(mq*350)+(sq*450)}/-"}
])
st.write(df)

# Submit button logic
if st.button("Submit"):
    date_time = dt.datetime.combine(date, time)

    # Generate new order ID
    m = max([int(i.id) for i in db.collection("Orders").stream()] + [0])

    # Save order to Firestore
    db.collection("Orders").document(str(m+1)).set({
        "AQ": aq,
        "CQ": cq,
        "GQ": gq,
        "MQ": mq,
        "SQ": sq,
        "Phone": phone,
        "Date": date_time,
        "Name": name_input,
        "Status": 1
    })

    # If new customer, add to "Profiles" using phone number as document ID
    if phone not in customer_phones:
        db.collection("Profiles").document(phone).set({
            "Name": name_input,
            "Phone no.": phone
        })
        st.success(f"🆕 New customer '{name_input}' added with Phone No. '{phone}'!")

    st.success("🎉 Order submitted successfully!")
