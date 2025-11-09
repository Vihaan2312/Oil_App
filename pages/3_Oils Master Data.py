import streamlit as st
from google.cloud import firestore
import pandas as pd
import time
import os
from login_sidebar import show_sidebar
import Database as mdb

st.set_page_config(page_title="🛢️ Master Oil Rates", layout="wide")

# 🔐 Always show login sidebar
show_sidebar()


# --- LOGIN WALL ---
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access this page.")
    st.stop()  # stops the rest of the script from running

st.title("🛢️ Master Oil Rates")

db = mdb.init()

# Ensure images folder exists
if not os.path.exists("images"):
    os.makedirs("images")

# 🔄 Fetch oil rates from Firestore
def fetch_rates():
    docs = db.collection("Rates").stream()
    data = []
    for doc in docs:
        doc_id = doc.id
        rate_data = doc.to_dict()
        rate = rate_data.get("Rate", 0)

        # Local image check
        img_path = f"images/{doc_id.lower()}.png"
        if not os.path.exists(img_path):
            img_path = ""

        data.append({
            "DocID": doc_id,          # Track original doc ID
            "Oil Name": doc_id,
            "Rate (₹/L)": rate,
            "Image": img_path
        })
    return pd.DataFrame(data)

rates_df = fetch_rates()

# ---------------- Edit Existing Oils ----------------
st.subheader("🖊️ Edit Existing Oils")
edited_data = []

for i, row in rates_df.iterrows():
    col1, col2, col3, col4 = st.columns([2, 2, 1.5, 0.8])
    
    with col1:
        new_name = st.text_input("Oil Name", row["Oil Name"], key=f"name_{i}")
    with col2:
        new_rate = st.number_input("Rate (₹/L)", value=float(row["Rate (₹/L)"]), key=f"rate_{i}", step=1.0)
    with col3:
        if row["Image"]:
            st.image(row["Image"], width=80)
        else:
            st.write("No Image")
    with col4:
        if st.button("❌", key=f"del_{i}"):
            db.collection("Rates").document(row["DocID"]).delete()
            if row["Image"] and os.path.exists(row["Image"]):
                os.remove(row["Image"])
            st.success(f"🗑️ Deleted: {row['Oil Name']}")
            time.sleep(1.5)
            st.rerun()

    edited_data.append({
        "DocID": row["DocID"],
        "Oil Name": new_name,
        "Rate (₹/L)": new_rate,
        "Image": row["Image"]
    })

# Save button for edits (supports renaming)
if st.button("💾 Save Changes"):
    for item in edited_data:
        old_id = item["DocID"]
        new_id = item["Oil Name"].strip()

        if new_id == "":
            st.error("⚠️ Oil Name cannot be empty!")
            continue

        doc_ref_new = db.collection("Rates").document(new_id)
        doc_ref_old = db.collection("Rates").document(old_id)

        if old_id != new_id:
            if doc_ref_new.get().exists:
                st.warning(f"⚠️ Cannot rename {old_id} → {new_id}, name already exists!")
                continue

            # Copy old doc to new doc
            doc_data = doc_ref_old.get().to_dict()
            doc_ref_new.set(doc_data)
            # Rename image file if exists
            old_img_path = f"images/{old_id.lower()}.png"
            new_img_path = f"images/{new_id.lower()}.png"
            if os.path.exists(old_img_path):
                os.rename(old_img_path, new_img_path)
            # Delete old doc
            doc_ref_old.delete()
        else:
            doc_ref_old.update({"Rate": item["Rate (₹/L)"]})

    st.success("✅ Rates updated successfully!")
    time.sleep(1.5)
    st.rerun()

# ---------------- Add New Oil ----------------
st.markdown("---")
st.subheader("➕ Add New Oil")

col1, col2, col3 = st.columns([2, 2, 1.5])

with col1:
    new_oil_name = st.text_input("Oil Name", key="new_name")
with col2:
    new_oil_rate = st.number_input("Rate (₹/L)", min_value=0.0, step=1.0, key="new_rate")
with col3:
    if st.button("➕ Add Oil"):
        if not new_oil_name.strip():
            st.error("⚠️ Oil Name cannot be empty!")
        else:
            doc_ref = db.collection("Rates").document(new_oil_name.strip())
            if doc_ref.get().exists:
                st.warning("⚠️ This oil already exists!")
            else:
                doc_ref.set({"Rate": new_oil_rate})
                st.success(f"✅ Added new oil: {new_oil_name.strip()}")
                time.sleep(1)
                st.rerun()

# ---------------- Manage Oil Images ----------------
st.markdown("---")
st.subheader("🖼️ Manage Oil Images")

for i, row in rates_df.iterrows():
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        st.write(f"**{row['Oil Name']}**")
    with col2:
        if row["Image"]:
            st.image(row["Image"], width=80)
        else:
            st.write("No Image")
    with col3:
        # Upload new image
        uploaded_file = st.file_uploader(f"Upload for {row['Oil Name']}", type=["png","jpg","jpeg"], key=f"upload_{i}")
        if uploaded_file:
            save_path = f"images/{row['Oil Name'].lower()}.png"
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Image updated for {row['Oil Name']}")
            time.sleep(1)
            st.rerun()

        # Delete image button
        if row["Image"] and st.button(f"🗑️ Delete Image", key=f"del_img_{i}"):
            if os.path.exists(row["Image"]):
                os.remove(row["Image"])
                st.success(f"🗑️ Image deleted for {row['Oil Name']}")
                time.sleep(1)
                st.rerun()
