import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
from fpdf import FPDF
import os
import requests
from login_sidebar import show_sidebar
import Database as mdb

# ================== WHATSAPP CONFIG ==================
PHONE_NUMBER_ID = "855788854294250"
ACCESS_TOKEN = "EAAf7DQHtLE0BQYJwZBSf40PmZBThrtU3jkLt9IISgzOw0qxTSSqPSxHcEhPe9uEysYZAcPz9YTnqGEVaaNw3HUTAsxf7QR62PMOd3TndC1zlZASDs7dI8EjiIZCCgRonCDK7EmZAZB3kak28NHasT0Mg3MWipldHVeM3b8VGPcRi4FhKhZC28fNUh7DEewq9XdacaQZDZD"
PUBLIC_INVOICE_BASE_URL = "https://github.com/Vihaan2312/Oil_App/blob/main/Invoices/"
# =====================================================

st.set_page_config(page_title="Order Management", page_icon="🛒", layout="wide")
show_sidebar()

if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()

st.title("🛢️ Atulit Pure Cold Pressed Oil - Order Management")
st.caption("Easily track, edit, and export your oil orders.")

db = mdb.init()

# ---------------- SESSION STATE ----------------
for key in ["id", "view", "update", "invoice_path"]:
    if key not in st.session_state:
        st.session_state[key] = None

home_empty = st.empty()
view_empty = st.empty()
update_empty = st.empty()

# ================== WHATSAPP SENDER ==================
def send_whatsapp_invoice(phone, name, pdf_url):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": "invoice_tempelate",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "document",
                            "document": {
                                "link": pdf_url,
                                "filename": "Invoice.pdf"
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": name
                        }
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)
    return r.status_code, r.text
# =====================================================

# ===================== VIEW MODE =====================
if st.session_state["view"]:
    home_empty.empty()
    update_empty.empty()

    with view_empty.container():
        rec = db.collection("Orders").document(st.session_state["id"]).get().to_dict()

        st.header(f"📄 Order ID: `{st.session_state['id']}`")
        st.write(f"👤 **Name:** {rec.get('Name')}")
        st.write(f"📞 **Phone:** {rec.get('Phone')}")
        st.write(f"📍 **Address:** {rec.get('Address')}")

        oil_data = []
        for doc in db.collection("Rates").stream():
            oil = doc.id
            qty = rec.get(oil, 0)
            amount = rec.get(f"{oil}_Amount", 0)
            rate = f"Rs. {int(amount/qty)}" if qty else "N/A"
            oil_data.append({
                "Oil": oil,
                "Rate": rate,
                "Quantity": qty,
                "Total": f"Rs. {amount}"
            })

        st.dataframe(pd.DataFrame(oil_data), use_container_width=True)

        # ----------- GENERATE INVOICE -----------
        if st.button("🧾 Generate Invoice"):
            os.makedirs("invoices", exist_ok=True)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 10, "Invoice", ln=True, align="C")
            pdf.ln(10)

            pdf.cell(200, 10, f"Name: {rec.get('Name')}", ln=True)
            pdf.cell(200, 10, f"Phone: {rec.get('Phone')}", ln=True)
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
                pdf.cell(30, 10, row["Rate"], 1)
                pdf.cell(30, 10, str(row["Quantity"]), 1)
                pdf.cell(40, 10, row["Total"], 1)
                pdf.ln()

            path = f"invoices/Invoice_{st.session_state['id']}.pdf"
            pdf.output(path)
            st.session_state["invoice_path"] = path

            st.success("Invoice generated successfully ✅")

        # -------- SEND WHATSAPP BUTTON --------
        if st.session_state.get("invoice_path"):
            with open(st.session_state["invoice_path"], "rb") as f:
                st.download_button(
                    "📄 Download Invoice",
                    f.read(),
                    os.path.basename(st.session_state["invoice_path"]),
                    "application/pdf"
                )

            if st.button("📤 Send Invoice on WhatsApp"):
                pdf_url = PUBLIC_INVOICE_BASE_URL + os.path.basename(st.session_state["invoice_path"])

                status, response = send_whatsapp_invoice(
                    phone="918105052102", #+ rec.get("Phone"),
                    name=rec.get("Name"),
                    pdf_url=pdf_url
                )

                if status == 200:
                    st.success("Invoice sent on WhatsApp ✅")
                else:
                    st.error(response)

        if st.button("❌ Close"):
            st.session_state["view"] = False
            st.session_state["id"] = None
            st.session_state["invoice_path"] = None
            st.rerun()

# ===================== HOME =====================
if not st.session_state["view"]:
    with home_empty.container():
        st.header("📋 Orders")

        for doc in db.collection("Orders").stream():
            data = doc.to_dict()
            with st.container(border=True):
                st.write(f"🆔 {doc.id}")
                st.write(f"👤 {data.get('Name')}")
                if st.button("🔍 View", key=doc.id):
                    st.session_state["id"] = doc.id
                    st.session_state["view"] = True
                    st.rerun()
