import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt

# Initialize Firestore client
db = firestore.Client.from_service_account_json("Firestore.json")

# Oil prices dictionary
oil_prices = {
    "Coconut": 450,
    "Groundnut": 350,
    "Mustard": 350,
    "Sesame": 450,
    "Almond": 2500
}

# Initialize session state variables
if "id" not in st.session_state:
    st.session_state["id"] = 0
if "view" not in st.session_state:
    st.session_state["view"] = False
if "update" not in st.session_state:
    st.session_state["update"] = False

# Containers for dynamic UI updates
home_empty = st.empty()
view_empty = st.empty()
update_empty = st.empty()

# -------------------------
# Update Mode: Edit order details
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
            date = st.date_input("Date:", rec.get("Date").date() if rec.get("Date") else dt.date.today())
            time = st.time_input("Time:", rec.get("Date").time() if rec.get("Date") else dt.datetime.now().time())

            # Status dictionaries
            status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
            status_reverse_dict = {v: k for k, v in status_dict.items()}

            current_status = status_dict.get(rec.get("Status", 1), "Ordered")
            next_status = {
                "Ordered": "Delivered",
                "Delivered": "Payment Done",
                "Payment Done": None
            }.get(current_status, None)

            st.write("**Order Status:**", current_status)

            if next_status:
                if st.button(f"Mark as {next_status}"):
                    db.collection("Orders").document(str(st.session_state["id"])).update({
                        "Status": status_reverse_dict[next_status]
                    })
                    st.rerun()

            # Prepare editable dataframe for oil quantities
            df = pd.DataFrame([
                {"Oil": "Coconut", "Rate": "₹450", "Quantity": rec.get("CQ", 0)},
                {"Oil": "Groundnut", "Rate": "₹350", "Quantity": rec.get("GQ", 0)},
                {"Oil": "Mustard", "Rate": "₹350", "Quantity": rec.get("MQ", 0)},
                {"Oil": "Sesame", "Rate": "₹450", "Quantity": rec.get("SQ", 0)},
                {"Oil": "Almond", "Rate": "₹2500", "Quantity": rec.get("AQ", 0)},
            ])

            edited_df = st.data_editor(df, key="order_edit", column_config={"Quantity": {"editable": True}})

            # Calculate total price
            edited_df["Total"] = edited_df.apply(lambda row: row["Quantity"] * oil_prices[row["Oil"]], axis=1)
            st.dataframe(edited_df)

            total_price = edited_df["Total"].sum()
            st.write(f"**Total Price: ₹{total_price}/-**")

            # Save button updates Firestore
            if st.button("Save"):
                db.collection("Orders").document(str(st.session_state["id"])).update({
                    "Name": name,
                    "Phone": phone,
                    "Date": dt.datetime.combine(date, time),
                    "CQ": int(edited_df.loc[0, "Quantity"]),
                    "GQ": int(edited_df.loc[1, "Quantity"]),
                    "MQ": int(edited_df.loc[2, "Quantity"]),
                    "SQ": int(edited_df.loc[3, "Quantity"]),
                    "AQ": int(edited_df.loc[4, "Quantity"])
                })
                st.session_state["update"] = False
                st.session_state["view"] = True
                st.rerun()

# -------------------------
# Home Page: List and filter orders
# -------------------------
if not st.session_state["update"] and not st.session_state["view"]:
    with home_empty.container():
        st.subheader("📋 Order List")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Ordered", "Delivered", "Payment Done"])
        with col2:
            name_filter = st.text_input("Search by Name").strip().lower()
        with col3:
            date_filter = st.date_input("Filter by Date (Optional)", value=None)

        # Fetch orders from Firestore
        orders = []
        for doc in db.collection("Orders").stream():
            data = doc.to_dict()
            data["id"] = doc.id
            orders.append(data)

        # Status lookup
        status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}

        # Filter orders
        filtered_orders = []
        for doc in orders:
            status = status_dict.get(doc.get("Status", 1), "Unknown")
            name = doc.get("Name", "").lower()
            order_date = doc.get("Date")

            if status_filter != "All" and status != status_filter:
                continue
            if name_filter and name_filter not in name:
                continue
            if date_filter and order_date and order_date.date() != date_filter:
                continue
            filtered_orders.append((doc, status))

        if filtered_orders:
            export_data = []
            for doc, status in filtered_orders:
                export_data.append({
                    "Order ID": doc["id"],
                    "Name": doc.get("Name", ""),
                    "Phone": doc.get("Phone", ""),
                    "Date": doc.get("Date").strftime("%Y-%m-%d") if doc.get("Date") else "",
                    "Time": doc.get("Date").time(),
                    "Status": status,
                    "Coconut Qty": doc.get("CQ", 0),
                    "Groundnut Qty": doc.get("GQ", 0),
                    "Mustard Qty": doc.get("MQ", 0),
                    "Sesame Qty": doc.get("SQ", 0),
                    "Almond Qty": doc.get("AQ", 0),
                })

            df_export = pd.DataFrame(export_data)

            from io import BytesIO
            import xlsxwriter

            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df_export.to_excel(writer, index=False, sheet_name='Filtered Orders')
            writer.close()
            output.seek(0)

            st.download_button(
                label="📥 Export Filtered Orders to Excel",
                data=output,
                file_name="Orders.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.markdown("---")



        # Display orders
        if not filtered_orders:
            st.info("No orders found with the selected filters.")
        else:
            for doc, status in filtered_orders:
                with st.container(border=True):
                    st.subheader(f"Order ID: {doc['id']}")
                    st.write("**Name:**", doc.get("Name", ""))
                    st.write("**Phone:**", str(int(doc.get("Phone", 0))))
                    st.write("**Date:**", str(doc.get("Date").date() if doc.get("Date") else "N/A"))
                    st.write("**Status:**", status)

                    if st.button("View", key=f"view_{doc['id']}"):
                        st.session_state["id"] = doc["id"]
                        st.session_state["view"] = True
                        st.rerun()
                # Export to Excel
        


# -------------------------
# View Mode: Show order details
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
            st.write("**Time:**", str(rec.get("Date").time() if rec.get("Date") else "N/A"))

            status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
            status_reverse_dict = {v: k for k, v in status_dict.items()}

            current_status = status_dict.get(rec.get("Status", 1), "Ordered")
            next_status = {
                "Ordered": "Delivered",
                "Delivered": "Payment Done",
                "Payment Done": None
            }.get(current_status, None)

            st.write("**Order Status:**", current_status)

            if next_status:
                if st.button(f"Mark as {next_status}"):
                    db.collection("Orders").document(str(st.session_state["id"])).update({
                        "Status": status_reverse_dict[next_status]
                    })
                    st.rerun()

            # Show order details in dataframe
            df = pd.DataFrame([
                {"Oil": "Coconut", "Rate": "₹450", "Quantity": rec.get("CQ", 0), "Total": rec.get("CQ", 0) * 450},
                {"Oil": "Groundnut", "Rate": "₹350", "Quantity": rec.get("GQ", 0), "Total": rec.get("GQ", 0) * 350},
                {"Oil": "Mustard", "Rate": "₹350", "Quantity": rec.get("MQ", 0), "Total": rec.get("MQ", 0) * 350},
                {"Oil": "Sesame", "Rate": "₹450", "Quantity": rec.get("SQ", 0), "Total": rec.get("SQ", 0) * 450},
                {"Oil": "Almond", "Rate": "₹2500", "Quantity": rec.get("AQ", 0), "Total": rec.get("AQ", 0) * 2500},
            ])

            total_price = df["Total"].sum()
            total_quantity = df["Quantity"].sum()

            total_row = pd.DataFrame([{"Oil": "Total", "Rate": "", "Quantity": total_quantity, "Total": f"₹{total_price}/-"}])
            df = pd.concat([df, total_row], ignore_index=True)

            st.dataframe(df)

            # Buttons to close or update
            # Buttons to close or update side by side
            col1, col2, col3 = st.columns([0.8, 0.9, 3.9])

            with col1:
                if st.button("Close ❌"):
                    st.session_state["view"] = False
                    st.session_state["id"] = 0
                    st.rerun()

            with col2:
                if current_status == "Ordered":
                    if st.button("Update 📝"):
                        st.session_state["update"] = True
                        st.session_state["view"] = False
                        st.rerun()

            if st.button("Generate Invoice"):
                from fpdf import FPDF
                import os

                # Define the folder where invoices will be saved
                folder = "invoices"
                os.makedirs(folder, exist_ok=True)  # Create folder if it doesn't exist

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.cell(200, 10, txt=f"Invoice for Order ID: {st.session_state['id']}", ln=True, align="C")
                pdf.ln(10)

                pdf.cell(200, 10, txt=f"Name: {rec.get('Name', '')}", ln=True)
                pdf.cell(200, 10, txt=f"Phone: {str(int(rec.get('Phone', 0)))}", ln=True)
                pdf.cell(200, 10, txt=f"Date: {str(rec.get('Date').date())}", ln=True)
                pdf.cell(200, 10, txt=f"Time: {str(rec.get('Date').time())}", ln=True)
                pdf.cell(200, 10, txt=f"Status: {current_status}", ln=True)

                pdf.ln(10)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(50, 10, "Oil", 1)
                pdf.cell(30, 10, "Rate", 1)
                pdf.cell(30, 10, "Qty", 1)
                pdf.cell(40, 10, "Total", 1)
                pdf.ln()
                pdf.set_font("Arial", size=12)
                total_price = 0
                for oil, rate_key, qty_key in [
                    ("Coconut", 450, "CQ"),
                    ("Groundnut", 350, "GQ"),
                    ("Mustard", 350, "MQ"),
                    ("Sesame", 450, "SQ"),
                    ("Almond", 2500, "AQ"),
                ]:
                    qty = rec.get(qty_key, 0)
                    rate = rate_key
                    total = qty * rate
                    total_price += total

                    pdf.cell(50, 10, oil, 1)
                    pdf.cell(30, 10, f"Rs. {rate}", 1)
                    pdf.cell(30, 10, str(qty), 1)
                    pdf.cell(40, 10, f"Rs. {total}", 1)
                    pdf.ln()

                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(110, 10, "Total", 1)
                    pdf.cell(40, 10, f"Rs. {total_price}", 1)

                    # Save and display
                    file_path = os.path.join(folder, f"Invoice_{st.session_state['id']}.pdf")
                    pdf.output(file_path)

                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📄 Download Invoice",
                            data=f,
                            file_name=f"Invoice_{st.session_state['id']}.pdf",
                            mime="application/pdf",
                            key="123456789009876543212345678909876543212345678987654321234567876543erfghjuy6trfghytresdftyujyr"
                        )

                    os.remove(file_path)