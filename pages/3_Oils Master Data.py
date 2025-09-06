import streamlit as st
from google.cloud import firestore
import pandas as pd
import time

st.set_page_config(page_title="🛢️ Master Oil Rates", layout="wide")
st.title("🛢️ Master Oil Rates")

# Firestore Init
creds = st.secrets["firestore"]
db = firestore.Client.from_service_account_info(dict(creds))

# 🔄 Fetch oil rates from Firestore
def fetch_rates():
    docs = db.collection("Rates").stream()
    data = []
    for doc in docs:
        doc_id = doc.id
        rate_data = doc.to_dict()
        rate = rate_data.get("Rate", 0)
        data.append({"Oil Name": doc_id, "Rate (₹/L)": rate})
    return pd.DataFrame(data)

# 🔃 Initial fetch
rates_df = fetch_rates()

# 🔧 Editable section
st.subheader("📝 Edit Oil Rates")
edited_df = st.data_editor(
    rates_df.copy(),
    key="oil_rates_editor",
    use_container_width=True,
    num_rows="dynamic"
)

# Check if edited
if not edited_df.equals(rates_df):
    if st.button("💾 Save Changes"):
        # Go through each row
        for i in range(len(edited_df)):
            old_name = rates_df.iloc[i]["Oil Name"] if i < len(rates_df) else None
            new_name = edited_df.iloc[i]["Oil Name"]
            new_rate = edited_df.iloc[i]["Rate (₹/L)"]

            if old_name and old_name != new_name:
                # Renamed oil
                db.collection("Rates").document(old_name).delete()
                db.collection("Rates").document(new_name).set({"Rate": new_rate})
            else:
                # New or unchanged name
                db.collection("Rates").document(new_name).set({"Rate": new_rate})

        st.success("✅ Changes saved!")
        time.sleep(1.5)
        st.rerun()

# 🗑️ Deletion Section
st.subheader("🗑️ Delete Oils")
for i, row in rates_df.iterrows():
    col1, col2, col3 = st.columns([4, 4, 1])
    col1.write(row["Oil Name"])
    col2.write(f"{row['Rate (₹/L)']} ₹/L")
    if col3.button("❌", key=f"del_{i}"):
        db.collection("Rates").document(row["Oil Name"]).delete()
        st.success(f"Deleted: {row['Oil Name']}")
        time.sleep(1.5)
        st.rerun()
