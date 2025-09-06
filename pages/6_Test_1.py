import firebase_admin
from firebase_admin import credentials, storage
# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("Storage.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'oil-project-for-appgyver.appspot.com'
    })

bucket = storage.bucket()

import streamlit as st

uploaded_file = st.file_uploader("Upload a file")

if uploaded_file is not None:
    blob = bucket.blob(f"uploads/{uploaded_file.name}")
    blob.upload_from_file(uploaded_file, content_type=uploaded_file.type)
    st.success(f"{uploaded_file.name} uploaded to Firebase Storage!")

file_name = "uploads/sample.txt"  # Replace with your path
blob = bucket.blob(file_name)

# Download content as string
file_content = blob.download_as_text()
st.text_area("File Content", file_content, height=200)

blobs = bucket.list_blobs(prefix="uploads/")  # Use your folder path
for blob in blobs:
    st.write(blob.name)


