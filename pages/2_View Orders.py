import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
from fpdf import FPDF
import os
from login_sidebar import show_sidebar

st.set_page_config(page_title="Order Management", page_icon="🛒", layout="wide")

# 🔐 Always show login sidebar
show_sidebar()

# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()  # stops the rest of the script from running

# Streamlit Config
st.set_page_config(page_title="Order Management", page_icon="🛒", layout="wide")
st.title("🛢️ Atulit Pure Cold Pressed Oil - Order Management")
st.caption("Easily track, edit, and export your oil orders.")

# Firestore Init
creds = st.secrets["firestore"]
db = firestore.Client.from_service_account_info(dict(creds))

# Session State
if "id" not in st.session_state:
    st.session_state["id"] = ""
if "view" not in st.session_state:
    st.session_state["view"] = False
if "update" not in st.session_state:
    st.session_state["update"] = False

home_empty = st.empty()
view_empty = st.empty()
update_empty = st.empty()

# Update Mode
if st.session_state["update"]:
    view_empty.empty()
    with update_empty.container():
        rec = db.collection("Orders").document(st.session_state["id"]).get().to_dict()

        st.header(f"✏️ Editing Order ID: `{st.session_state['id']}`")

        name = st.text_input("👤 Name", rec.get("Name", ""))
        phone = st.text_input("📞 Phone", rec.get("Phone", ""))
        date = st.date_input("🗓️ Date", rec.get("Date").date() if rec.get("Date") else dt.date.today())
        time = st.time_input("⏰ Time", rec.get("Date").time() if rec.get("Date") else dt.datetime.now().time())

        status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
        current_status = rec.get("Status", 1)
        st.write(f"📦 **Order Status:** {status_dict.get(current_status)}")

        if current_status != 3:
            if st.button(f"✅ Mark as {status_dict.get(current_status + 1)}"):
                db.collection("Orders").document(st.session_state["id"]).update({"Status": current_status + 1})
                st.rerun()

        oil_data = []
        for doc in db.collection("Rates").stream():
            oil = doc.id
            rate_master = doc.to_dict().get("Rate", 0)
            qty = rec.get(oil, 0)
            amount = rec.get(f"{oil}_Amount", 0)
            rate = round(amount / qty, 2) if qty else rate_master
            oil_data.append({"Oil": oil, "Rate": rate, "Quantity": qty})

        df = pd.DataFrame(oil_data)
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
        dc = st.number_input("🚚 Delivery Charge", value=rec.get("DC", 0))
        edited_df["Amount"] = edited_df.apply(lambda row: row["Quantity"] * row["Rate"], axis=1)
        total_amount = edited_df["Amount"].sum() + dc
        total_qty = edited_df["Quantity"].sum()

        summary_df = pd.DataFrame([
            {"Oil": "Delivery Charge", "Amount": dc},
            {"Oil": "Total", "Quantity": total_qty, "Amount": total_amount}
        ])
        st.dataframe(pd.concat([edited_df, summary_df], ignore_index=True), use_container_width=True)

        if st.button("💾 Save Changes"):
            update_data = {"Name": name, "Phone": phone, "Date": dt.datetime.combine(date, time), "DC": dc, "TotalAmount": total_amount}
            for _, row in edited_df.iterrows():
                update_data[row["Oil"]] = int(row["Quantity"])
                update_data[f"{row['Oil']}_Amount"] = int(row["Amount"])
            db.collection("Orders").document(st.session_state["id"]).update(update_data)
            st.session_state.update({"update": False, "view": True})
            st.rerun()

# View Mode
elif st.session_state["view"]:
    home_empty.empty()
    update_empty.empty()
    with view_empty.container():
        rec = db.collection("Orders").document(st.session_state["id"]).get().to_dict()

        st.header(f"📄 Viewing Order ID: `{st.session_state['id']}`")
        st.write(f"👤 **Name:** {rec.get('Name', '')}")
        st.write(f"📞 **Phone:** {rec.get('Phone', '')}")
        st.write(f"🗓️ **Date:** {rec.get('Date').strftime('%Y-%m-%d %H:%M') if rec.get('Date') else 'N/A'}")

        status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
        current_status = rec.get("Status", 1)
        st.write(f"📦 **Order Status:** {status_dict.get(current_status)}")

        if current_status != 3:
            if st.button(f"✅ Mark as {status_dict.get(current_status + 1)}"):
                db.collection("Orders").document(st.session_state["id"]).update({"Status": current_status + 1})
                st.rerun()

        oil_data = []
        for doc in db.collection("Rates").stream():
            oil = doc.id
            qty = rec.get(oil, 0)
            amount = rec.get(f"{oil}_Amount", 0)
            rate_display = f"{round(amount/qty, 2)}" if qty else "N/A"
            total_display = f"{amount}" if amount else "N/A"
            oil_data.append({"Oil": oil, "Rate": rate_display, "Quantity": qty, "Total": total_display})

        dc = rec.get("DC", 0)
        total_amount = rec.get("TotalAmount", 0)

        summary_df = pd.DataFrame([
            {"Oil": "Delivery Charge", "Total": dc},
            {"Oil": "Total", "Total": total_amount}
        ])

        st.dataframe(pd.concat([pd.DataFrame(oil_data), summary_df], ignore_index=True), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Close"):
                st.session_state.update({"view": False, "id": ""})
                st.rerun()
        with col2:
            if current_status == 1 and st.button("✏️ Update"):
                st.session_state.update({"update": True, "view": False})
                st.rerun()

        if st.button("🧾 Generate Invoice"):
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
            for row in oil_data:
                pdf.cell(50, 10, row["Oil"], 1)
                pdf.cell(30, 10, f"Rs. {row['Rate']}", 1)
                pdf.cell(30, 10, str(row["Quantity"]), 1)
                pdf.cell(40, 10, f"Rs. {row['Total']}", 1)
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

# Home Page
if not st.session_state["update"] and not st.session_state["view"]:
    with home_empty.container():
        st.header("📋 Order Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("🔎 Filter by Status", ["All", "Ordered", "Delivered", "Payment Done"])
        with col2:
            name_filter = st.text_input("🔤 Search by Name").strip().lower()
        with col3:
            date_filter = st.date_input("📅 Filter by Date (Optional)", value=None)

        orders = []
        for doc in db.collection("Orders").stream():
            data = doc.to_dict()
            data["id"] = doc.id
            orders.append(data)

        status_dict = {1: "Ordered", 2: "Delivered", 3: "Payment Done"}
        filtered_orders = []

        for doc in orders:
            status = status_dict.get(doc.get("Status", 1), "Unknown")
            if (status_filter != "All" and status != status_filter) or \
               (name_filter and name_filter not in doc.get("Name", "").lower()) or \
               (date_filter and doc.get("Date") and doc.get("Date").date() != date_filter):
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
                    "Status": status
                })
            df = pd.DataFrame(export_data)
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Export Filtered Orders", output.getvalue(), "Orders.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("---")

        if not filtered_orders:
            st.info("No orders found with the selected filters.")
        else:
            for doc, status in filtered_orders:
                with st.container(border=True):
                    st.subheader(f"🆔 Order ID: `{doc['id']}`")
                    st.write(f"👤 **Name:** {doc.get('Name', '')}")
                    st.write(f"📞 **Phone:** {doc.get('Phone', '')}")
                    st.write(f"🗓️ **Date:** {doc.get('Date').date() if doc.get('Date') else 'N/A'}")
                    st.write(f"📦 **Status:** {status}")
                    if st.button("🔍 View", key=f"view_{doc['id']}"):
                        st.session_state["id"] = doc["id"]
                        st.session_state["view"] = True
                        st.rerun()
