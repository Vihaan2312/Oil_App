import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
from fpdf import FPDF
import os

# Initialize Firestore
db = firestore.Client.from_service_account_json("Firestore.json")

# Session state
if "id" not in st.session_state:
    st.session_state["id"] = ""
if "view" not in st.session_state:
    st.session_state["view"] = False
if "update" not in st.session_state:
    st.session_state["update"] = False

home_empty = st.empty()
view_empty = st.empty()
update_empty = st.empty()

if st.session_state["update"]:
    view_empty.empty()
    with update_empty.container():
        order_doc = db.collection("Orders").document(st.session_state["id"]).get()
        rec = order_doc.to_dict()

        st.subheader(f"Editing Order ID: {st.session_state['id']}")
        name = st.text_input("Name", rec.get("Name", ""))
        phone = st.text_input("Phone", rec.get("Phone", ""))
        date = st.date_input("Date", rec.get("Date").date() if rec.get("Date") else dt.date.today())
        time = st.time_input("Time", rec.get("Date").time() if rec.get("Date") else dt.datetime.now().time())

        status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
        status_reverse_dict = {v: k for k, v in status_dict.items()}
        current_status = rec.get("Status", 1)
        st.write(f"**Order Status:** {status_dict.get(current_status)}")

        if current_status != 3:
            next_status = current_status + 1
            if st.button(f"Mark as {status_dict.get(next_status)}"):
                db.collection("Orders").document(st.session_state["id"]).update({"Status": next_status})
                st.rerun()

        # Fetch oils from Rates collection
        oil_docs = db.collection("Rates").stream()
        oil_data = []
        for doc in oil_docs:
            oil = doc.id
            rate_master = doc.to_dict().get("Rate", 0)
            qty = rec.get(oil, 0)
            amount = rec.get(f"{oil}_Amount", 0)

            if qty == 0:
                rate = rate_master
                amount = 0
            else:
                rate = round(amount / qty, 2) if qty else 0

            oil_data.append({
                "Oil": oil,
                "Rate": rate,
                "Quantity": qty,
            })

        df = pd.DataFrame(oil_data)
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

        dc = st.number_input("Delivery Charge", value=rec.get("DC", 0))

        # Recalculate Amount column live
        edited_df["Amount"] = edited_df.apply(lambda row: row["Quantity"] * row["Rate"], axis=1)

        total_amount = edited_df["Amount"].sum() + dc
        total_qty = edited_df["Quantity"].sum()

        summary_df = pd.DataFrame([
            {"Oil": "Delivery Charge", "Amount": dc},
            {"Oil": "Total", "Quantity": total_qty, "Amount": total_amount}
        ])
        display_df = pd.concat([edited_df, summary_df], ignore_index=True)
        st.dataframe(display_df, use_container_width=True)

        if st.button("Save"):
            update_data = {
                "Name": name,
                "Phone": phone,
                "Date": dt.datetime.combine(date, time),
                "DC": dc,
                "TotalAmount": total_amount
            }
            for _, row in edited_df.iterrows():
                oil = row["Oil"]
                update_data[oil] = int(row["Quantity"])
                update_data[f"{oil}_Amount"] = int(row["Amount"])

            db.collection("Orders").document(st.session_state["id"]).update(update_data)
            st.session_state["update"] = False
            st.session_state["view"] = True
            st.rerun()


# ----------------- VIEW MODE -------------------
elif st.session_state["view"]:
    home_empty.empty()
    update_empty.empty()
    with view_empty.container():
        order_doc = db.collection("Orders").document(st.session_state["id"]).get()
        rec = order_doc.to_dict()

        st.subheader(f"Viewing Order ID: {st.session_state['id']}")
        st.write(f"**Name:** {rec.get('Name', '')}")
        st.write(f"**Phone:** {rec.get('Phone', '')}")
        st.write(f"**Date:** {rec.get('Date').strftime('%Y-%m-%d %H:%M') if rec.get('Date') else 'N/A'}")

        status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
        status_reverse_dict = {v: k for k, v in status_dict.items()}
        current_status = rec.get("Status", 1)
        st.write(f"**Order Status:** {status_dict.get(current_status)}")

        if current_status != 3:
            next_status = current_status + 1
            if st.button(f"Mark as {status_dict.get(next_status)}"):
                db.collection("Orders").document(st.session_state["id"]).update({"Status": next_status})
                st.rerun()

        oil_docs = db.collection("Rates").stream()
        oils = db.collection("Rates").stream()
        table = []
        total_amount = 0

        for oil_doc in oils:
            oil = oil_doc.id
            qty = rec.get(oil, 0)
            amount = rec.get(f"{oil}_Amount", 0)
            rate_display = f"{amount // qty}" if qty else "N/A"
            table.append({"Oil": oil, "Rate": rate_display, "Quantity": qty, "Amount": amount})
            total_amount += amount
            
        oil_data = []
        for doc in oil_docs:
            oil = doc.id
            qty = rec.get(oil, 0)
            amount = rec.get(f"{oil}_Amount", 0)

            if qty == 0:
                rate_display = "N/A"
                total_display = "N/A"
            else:
                rate_display = f"₹{round(amount/qty, 2)}"
                total_display = f"₹{amount}"

            oil_data.append({"Oil": oil, "Rate": rate_display, "Quantity": qty, "Total": total_display})

        df = pd.DataFrame(oil_data)
        dc = rec.get("DC", 0)
        total_amount = rec.get("TotalAmount", 0)

        summary_df = pd.DataFrame([
            {"Oil": "Delivery Charge", "Total": f"₹{dc}"},
            {"Oil": "Total", "Total": f"₹{total_amount}"}
        ])
        display_df = pd.concat([df, summary_df], ignore_index=True)
        st.dataframe(display_df, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Close"):
                st.session_state["view"] = False
                st.session_state["id"] = ""
                st.rerun()
        with col2:
            if current_status == 1 and st.button("Update"):
                st.session_state["update"] = True
                st.session_state["view"] = False
                st.rerun()
        if st.button("Generate Invoice"):
            folder = "invoices"
            os.makedirs(folder, exist_ok=True)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, f"Invoice for Order {st.session_state['id']}", ln=True, align="C")
            pdf.ln(10)

            pdf.cell(200, 10, f"Name: {rec.get('Name', '')}", ln=True)
            pdf.cell(200, 10, f"Phone: {rec.get('Phone', '')}", ln=True)
            pdf.cell(200, 10, f"Date: {rec.get('Date').date()}", ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 10, "Oil", 1)
            pdf.cell(30, 10, "Rate", 1)
            pdf.cell(30, 10, "Qty", 1)
            pdf.cell(40, 10, "Total", 1)
            pdf.ln()

            pdf.set_font("Arial", size=12)
            for row in table:
                pdf.cell(50, 10, row["Oil"], 1)
                pdf.cell(30, 10, str(row["Rate"]), 1)
                pdf.cell(30, 10, str(row["Quantity"]), 1)
                pdf.cell(40, 10, f"Rs. {row['Amount']}", 1)
                pdf.ln()

            pdf.cell(110, 10, "Delivery Charge", 1)
            pdf.cell(40, 10, f"Rs. {dc}", 1)
            pdf.ln()

            pdf.set_font("Arial", "B", 12)
            pdf.cell(110, 10, "Grand Total", 1)
            pdf.cell(40, 10, f"Rs. {total_amount}", 1)

            filepath = f"invoices/Invoice_{st.session_state['id']}.pdf"
            pdf.output(filepath)

            with open(filepath, "rb") as f:
                st.download_button("📄 Download Invoice", f.read(), f"Invoice_{st.session_state['id']}.pdf", "application/pdf")
            os.remove(filepath)

# ----------------- HOME PAGE -------------------
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
