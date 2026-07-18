import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
from fpdf import FPDF
import os
import requests
import firebase_admin
from firebase_admin import credentials, storage

from login_sidebar import show_sidebar
import Database as mdb

st.set_page_config(page_title="Order Management", page_icon="🛒", layout="wide")

show_sidebar()

# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()

st.title("🛢️ Atulit Pure Cold Pressed Oil - Order Management")
st.caption("Easily track, edit, and export your oil orders.")

# -------- FIREBASE INIT --------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firestore"]))
    firebase_admin.initialize_app(cred, {
        "storageBucket": st.secrets["storage"]["id"]
    })

def upload_to_firebase(file_bytes, filename):
    bucket = storage.bucket()
    blob = bucket.blob(f"invoices/{filename}")
    blob.upload_from_string(file_bytes, content_type="application/pdf")
    blob.make_public()
    return blob.public_url

db = mdb.init()

# -------- SESSION STATE --------
for key, default in {
    "id": "",
    "view": False,
    "update": False,
    "invoice_ready": False,
    "pdf_url": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

home_empty = st.empty()
view_empty = st.empty()
update_empty = st.empty()

# ================= UPDATE MODE =================
if st.session_state["update"]:
    view_empty.empty()
    with update_empty.container():
        rec = db.collection("Orders").document(
            st.session_state["id"]).get().to_dict()

        st.header(f"✏️ Editing Order ID: `{st.session_state['id']}`")

        name = st.text_input("👤 Name", rec.get("Name", ""))
        phone = st.text_input("📞 Phone", rec.get("Phone", ""))
        date = st.date_input(
            "🗓️ Date",
            rec.get("Date").date() if rec.get("Date") else dt.date.today())
        time = st.time_input(
            "⏰ Time",
            rec.get("Date").time() if rec.get("Date")
            else dt.datetime.now().time())
        address = st.text_input("📄 Address", rec.get("Address", ""))

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
        edited_df = st.data_editor(df, use_container_width=True)

        dc = st.number_input("🚚 Delivery Charge",
                             value=rec.get("DC", 0))

        edited_df["Amount"] = edited_df.apply(
            lambda r: r["Quantity"] * r["Rate"], axis=1)

        total_amount = edited_df["Amount"].sum() + dc
        total_qty = edited_df["Quantity"].sum()

        summary_df = pd.DataFrame([
            {"Oil": "Delivery Charge", "Amount": dc},
            {"Oil": "Total", "Quantity": total_qty,
             "Amount": total_amount}
        ])

        st.dataframe(pd.concat([edited_df, summary_df],
                               ignore_index=True),
                     use_container_width=True)

        if st.button("💾 Save Changes"):
            update_data = {
                "Name": name,
                "Phone": phone,
                "Address": address,
                "Date": dt.datetime.combine(date, time),
                "DC": dc,
                "TotalAmount": total_amount
            }

            for _, row in edited_df.iterrows():
                update_data[row["Oil"]] = int(row["Quantity"])
                update_data[f"{row['Oil']}_Amount"] = int(row["Amount"])

            db.collection("Orders").document(
                st.session_state["id"]).update(update_data)

            st.session_state.update({"update": False, "view": True})
            st.rerun()

# ================= VIEW MODE =================
elif st.session_state["view"]:
    home_empty.empty()
    update_empty.empty()

    with view_empty.container():
        rec = db.collection("Orders").document(
            st.session_state["id"]).get().to_dict()

        st.header(f"📄 Viewing Order ID: `{st.session_state['id']}`")

        st.write(f"👤 **Name:** {rec.get('Name','')}")
        st.write(f"📞 **Phone:** {rec.get('Phone','')}")
        st.write(
            f"🗓️ **Date:** {rec.get('Date').strftime('%Y-%m-%d %H:%M') if rec.get('Date') else 'N/A'}"
        )
        st.write(f"📄 **Address:** {rec.get('Address')}")

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
            qty = rec.get(oil, 0.0)
            amount = rec.get(f"{oil}_Amount", 0)
            rate_display = (
                f"Rs. {int(round(amount/qty,2))}" if qty else "N/A")
            total_display = (
                f"Rs. {int(amount)}" if amount else "Rs. 0")

            oil_data.append({
                "Oil": oil,
                "Rate": rate_display,
                "Quantity": qty,
                "Total": total_display
            })

        delivery = int(rec.get("DC", 0))
        dc = f"Rs. {delivery}"
        ta = int(rec.get("TotalAmount", 0))
        total_amount = f"Rs. {ta}"

        summary_df = pd.DataFrame([
            {"Oil": "Delivery Charge", "Total": dc},
            {"Oil": "Total", "Total": total_amount}
        ])

        st.dataframe(pd.concat(
            [pd.DataFrame(oil_data), summary_df],
            ignore_index=True),
            use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("❌ Close"):
                st.session_state["invoice_ready"] = False
                st.session_state["pdf_url"] = None
                st.session_state.update({"view": False, "id": ""})
                st.rerun()

        with col2:
            if st.button("✏️ Update"):
                st.session_state.update(
                    {"update": True, "view": False})
                st.rerun()
        
        # ===== GENERATE INVOICE =====
        if st.button("🧾 Generate Invoice"):

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, f"Invoice for Order", ln=True, align="C")
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
                pdf.cell(30, 10, row['Rate'], 1)
                pdf.cell(30, 10, str(row["Quantity"]), 1)
                pdf.cell(40, 10, f"{row['Total']}", 1)
                pdf.ln()

            pdf.cell(110, 10, "Delivery Charge", 1)
            pdf.cell(40, 10, f"{dc}", 1)
            pdf.ln()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(110, 10, "Grand Total", 1)
            pdf.cell(40, 10, f"{total_amount}", 1)

            path = f"Invoice_{st.session_state['id']}.pdf"
            pdf.output(path)

            with open(path,"rb") as f:
                st.session_state["pdf_bytes"] = f.read()

            st.session_state["pdf_url"] = upload_to_firebase(
                st.session_state["pdf_bytes"],
                path
            )

            st.session_state["invoice_ready"] = True

            os.remove(path)

            st.rerun()

        # ===== DOWNLOAD BUTTON (separate block) =====
        if st.session_state["invoice_ready"]:

            if st.download_button(
                "📄 Download Invoice",
                st.session_state["pdf_bytes"],
                f"Invoice_{st.session_state['id']}.pdf",
                "application/pdf"
            ):
                st.session_state["invoice_ready"] = False
                st.session_state["pdf_url"] = None
                st.session_state["pdf_bytes"] = None
                st.rerun()

            # ===== SEND BUTTON =====
            if st.button("📲 Send via WhatsApp"):

                token = st.secrets["WHATSAPP_TOKEN"]["wa_token"]

                payload = {
                    "messaging_product": "whatsapp",
                    "to": "919535972102",
                    "type": "template",
                    "template": {
                        "name": "invoice_tempelate",
                        "language": {"code":"en"},
                        "components":[
                            {
                                "type":"header",
                                "parameters":[
                                    {"type":"document",
                                     "document":{
                                         "link":st.session_state["pdf_url"],
                                         "filename":"Invoice.pdf"}}
                                ]
                            },
                            {
                                "type":"body",
                                "parameters":[
                                    {"type":"text",
                                     "text":rec.get("Name")}
                                ]
                            }
                        ]
                    }
                }

                headers = {
                    "Authorization":f"Bearer {token}",
                    "Content-Type":"application/json"
                }

                url = "https://graph.facebook.com/v22.0/855788854294250/messages"
                requests.post(url,json=payload,headers=headers)

                st.session_state["invoice_ready"] = False
                st.session_state["pdf_url"] = None
                st.session_state["pdf_bytes"] = None

                st.success("✅ Sent!")
                st.rerun()

# ================= HOME PAGE =================
if not st.session_state["update"] and not st.session_state["view"]:
    with home_empty.container():
        st.header("📋 Order Dashboard")

        col1,col2,col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "🔎 Filter by Status",
                ["All","Ordered","Delivered","Payment Done"])

        with col2:
            name_filter = st.text_input(
                "🔤 Search by Name").strip().lower()

        with col3:
            date_filter = st.date_input(
                "📅 Filter by Date (Optional)",
                value=None)

        orders=[]
        for doc in db.collection("Orders").stream():
            d=doc.to_dict()
            d["id"]=doc.id
            orders.append(d)

        status_dict={1:"Ordered",2:"Delivered",3:"Payment Done"}
        filtered_orders=[]

        for doc in orders:
            status=status_dict.get(doc.get("Status",1),"Unknown")

            if (status_filter!="All" and status!=status_filter) or \
               (name_filter and name_filter not in doc.get("Name","").lower()) or \
               (date_filter and doc.get("Date") and
                doc.get("Date").date()!=date_filter):
                continue

            filtered_orders.append((doc,status))

        if filtered_orders:
            export=[]
            for doc,status in filtered_orders:
                export.append({
                    "Order ID":doc["id"],
                    "Name":doc.get("Name",""),
                    "Phone":doc.get("Phone",""),
                    "Date":doc.get("Date").strftime("%Y-%m-%d")
                           if doc.get("Date") else "",
                    "Status":status
                })

            df=pd.DataFrame(export)
            from io import BytesIO
            buf=BytesIO()
            with pd.ExcelWriter(buf,engine="xlsxwriter") as w:
                df.to_excel(w,index=False)

            st.download_button(
                "📥 Export Filtered Orders",
                buf.getvalue(),
                "Orders.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("---")

        if not filtered_orders:
            st.info("No orders found with the selected filters.")
        else:
            for doc,status in filtered_orders:
                with st.container(border=True):
                    st.subheader(f"🆔 Order ID: `{doc['id']}`")
                    st.write(f"👤 **Name:** {doc.get('Name','')}")
                    st.write(f"📞 **Phone:** {doc.get('Phone','')}")
                    st.write(f"🗓️ **Date:** {doc.get('Date').date() if doc.get('Date') else 'N/A'}")
                    st.write(f"📦 **Status:** {status}")
                    if st.button("🔍 View",key=f"view_{doc['id']}"):
                        st.session_state["id"]=doc["id"]
                        st.session_state["view"]=True
                        st.rerun()
