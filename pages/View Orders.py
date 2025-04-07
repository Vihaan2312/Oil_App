import streamlit as st
from google.cloud import firestore
import pandas as pd
from datetime import datetime

db = firestore.Client.from_service_account_info("Firestore.json")

# Oil prices dictionary
oil_prices = {
    "Coconut": 400,
    "Groundnut": 350,
    "Mustard": 350,
    "Sesame": 450,
    "Almond": 2500
}

# Streamlit session state management
if "id" not in st.session_state:
    st.session_state["id"] = 0
if "view" not in st.session_state:
    st.session_state["view"] = False
if "update" not in st.session_state:
    st.session_state["update"] = False

home_empty = st.empty()
view_empty = st.empty()
update_empty = st.empty()

# -------------------------
#  Update Mode
# -------------------------
if st.session_state["update"]:
    view_empty.empty()
    with update_empty.container():
        order_doc = db.collection("Orders").document(str(st.session_state["id"])).get()
        rec = order_doc.to_dict()

        if rec:
            st.subheader(f"Editing Order ID: {st.session_state['id']}")

            # Editable fields
            name = st.text_input("Name:", rec.get("Name", ""))
            phone = st.number_input("Phone:", value=int(rec.get("Phone", 0)), step=1)
            date = st.date_input("Date:", rec.get("Date").date() if rec.get("Date") else datetime.today())

          # Status Dictionary
            status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
            status_reverse_dict = {"Ordered": 1, "Delivered": 2, "Payment Done": 3}

            # Get current status
            current_status = status_dict.get(rec.get("Status", 1), "Ordered")

            # Determine next possible status
            next_status = {
                "Ordered": "Delivered",
                "Delivered": "Payment Done",
                "Payment Done": None  # No further updates allowed
            }.get(current_status, None)

            st.write("**Order Status:**", current_status)

            if next_status:  # Show next status if available
                if st.button(f"Mark as {next_status}"):
                    db.collection("Orders").document(str(st.session_state["id"])).update({
                        "Status": status_reverse_dict[next_status]
                    })
                    st.rerun()

            # Create Editable DataFrame
            df = pd.DataFrame([
                {"Oil": "Coconut", "Rate": "₹400", "Quantity": rec.get("CQ", 0)},
                {"Oil": "Groundnut", "Rate": "₹350", "Quantity": rec.get("GQ", 0)},
                {"Oil": "Mustard", "Rate": "₹350", "Quantity": rec.get("MQ", 0)},
                {"Oil": "Sesame", "Rate": "₹450", "Quantity": rec.get("SQ", 0)},
                {"Oil": "Almond", "Rate": "₹2500", "Quantity": rec.get("AQ", 0)}
            ])

            # Editable DataFrame
            edited_df = st.data_editor(df, key="order_edit", column_config={"Quantity": {"editable": True}})

            # Calculate updated total price dynamically
            edited_df["Total"] = edited_df.apply(lambda row: row["Quantity"] * oil_prices[row["Oil"]], axis=1)

            # Display updated DataFrame with recalculated totals
            st.dataframe(edited_df)

            # Display Total Price
            total_price = edited_df["Total"].sum()
            st.write(f"**Total Price: ₹{total_price}/-**")

            # Save Button
            if st.button("Save"):
                db.collection("Orders").document(str(st.session_state["id"])).update({
                    "Name": name,
                    "Phone": phone,
                    "Date": datetime.combine(date, datetime.min.time()),  # Convert date to timestamp
                    "CQ": edited_df.loc[0, "Quantity"],
                    "GQ": edited_df.loc[1, "Quantity"],
                    "MQ": edited_df.loc[2, "Quantity"],
                    "SQ": edited_df.loc[3, "Quantity"],
                    "AQ": edited_df.loc[4, "Quantity"]
                })

                st.session_state["update"] = False
                st.session_state["view"] = True
                st.rerun()

# -------------------------
#  Home Page (List of Orders)
# -------------------------
if not st.session_state["update"] and not st.session_state["view"]:
    with home_empty.container():
        for i in db.collection("Orders").stream():
            doc = i.to_dict()
            status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
            status = status_dict.get(doc.get("Status", 1), "Unknown")

            with st.container(border=True):
                st.subheader(f"Order ID: {i.id}")
                st.write("**Name:**", doc.get("Name", ""))
                st.write("**Phone:**", str(int(doc.get("Phone", 0))))
                st.write("**Date:**", str(doc.get("Date").date() if doc.get("Date") else "N/A"))
                st.write("**Status:**", status)

                if st.button("View", key=i.id):
                    st.session_state["id"] = i.id
                    st.session_state["view"] = True
                    st.rerun()

# -------------------------
#  View Mode
# -------------------------
if st.session_state["view"]:
    home_empty.empty()
    update_empty.empty()
    with view_empty.container():
        order_doc = db.collection("Orders").document(str(st.session_state["id"])).get()
        rec = order_doc.to_dict()

        if rec:
            st.subheader(f"Viewing Order ID: {st.session_state['id']}")

            st.write("**Name:**", rec.get("Name", ""))
            st.write("**Phone:**", str(int(rec.get("Phone", 0))))
            st.write("**Date:**", str(rec.get("Date").date() if rec.get("Date") else "N/A"))

            # Status Dictionary
            status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
            status_reverse_dict = {"Ordered": 1, "Delivered": 2, "Payment Done": 3}

            # Get current status
            current_status = status_dict.get(rec.get("Status", 1), "Ordered")

            # Determine next possible status
            next_status = {
                "Ordered": "Delivered",
                "Delivered": "Payment Done",
                "Payment Done": None  # No further updates allowed
            }.get(current_status, None)

            st.write("**Order Status:**", current_status)

            if next_status:  # Show next status if available
                if st.button(f"Mark as {next_status}"):
                    db.collection("Orders").document(str(st.session_state["id"])).update({
                        "Status": status_reverse_dict[next_status]
                    })
                    st.rerun()

            # Create order details DataFrame
            df = pd.DataFrame([
                {"Oil": "Coconut", "Rate": "₹400", "Quantity": rec.get("CQ", 0), "Total": rec.get("CQ", 0) * 400},
                {"Oil": "Groundnut", "Rate": "₹350", "Quantity": rec.get("GQ", 0), "Total": rec.get("GQ", 0) * 350},
                {"Oil": "Mustard", "Rate": "₹350", "Quantity": rec.get("MQ", 0), "Total": rec.get("MQ", 0) * 350},
                {"Oil": "Sesame", "Rate": "₹450", "Quantity": rec.get("SQ", 0), "Total": rec.get("SQ", 0) * 450},
                {"Oil": "Almond", "Rate": "₹2500", "Quantity": rec.get("AQ", 0), "Total": rec.get("AQ", 0) * 2500}
            ])

            # Calculate grand total
            total_price = df["Total"].sum()
            total_quantity = df["Quantity"].sum()

            # Add a row for total price
            total_row = pd.DataFrame([{"Oil": "Total", "Rate": "", "Quantity": total_quantity, "Total": f"₹{total_price}/-"}])
            df = pd.concat([df, total_row], ignore_index=True)

            # Display DataFrame
            st.dataframe(df)

            if st.button("Close❌"):
                st.session_state["view"] = False
                st.session_state["id"] = 0
                st.rerun()

            if st.button("Update📝"):
                st.session_state["update"] = True
                st.session_state["view"] = False
                st.rerun()
