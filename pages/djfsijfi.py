import streamlit as st
import requests

# --- Streamlit UI ---
st.title("Send WhatsApp Invoice Template")

# Input fields
phone = st.text_input("Recipient Phone (with country code, e.g., +91XXXXXXXXXX)")
name = st.text_input("Customer Name", "Deepa")
pdf_url = st.text_input("PDF URL", "https://yourdomain.com/invoice.pdf")

if st.button("Send Template"):

    if not phone or not pdf_url:
        st.error("Please enter both phone number and PDF URL.")
    else:
        # --- WhatsApp API request ---
        url = "https://graph.facebook.com/v22.0/855788854294250/messages"  # Replace with your phone number ID
        token = "EAAf7DQHtLE0BQYJwZBSf40PmZBThrtU3jkLt9IISgzOw0qxTSSqPSxHcEhPe9uEysYZAcPz9YTnqGEVaaNw3HUTAsxf7QR62PMOd3TndC1zlZASDs7dI8EjiIZCCgRonCDK7EmZAZB3kak28NHasT0Mg3MWipldHVeM3b8VGPcRi4FhKhZC28fNUh7DEewq9XdacaQZDZD"  # Replace with your WhatsApp Business API token

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": "invoice_tempelate",  # Replace with your approved template name
                "language": { "code": "en" },
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
                            { "type": "text", "text": name }
                        ]
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            st.success("Template sent successfully!")
        else:
            st.error(f"Failed to send template. Error: {response.text}")
