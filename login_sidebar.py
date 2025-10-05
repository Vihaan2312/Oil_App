# login_sidebar.py
import streamlit as st
import pyrebase

# Firebase config
firebaseConfig = st.secrets["authentication"]
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.session_state["user"] = user
        return True
    except Exception as e:
        st.sidebar.error("❌ Login failed")
        st.sidebar.error(e)
        return False

def signup(email, password):
    try:
        auth.create_user_with_email_and_password(email, password)
        st.sidebar.success("✅ Account created successfully! Please log in.")
    except Exception as e:
        st.sidebar.error("❌ Signup failed")
        st.sidebar.error(e)

def reset_password(email):
    try:
        auth.send_password_reset_email(email)
        st.sidebar.success("📩 Password reset email sent!")
    except Exception as e:
        st.sidebar.error("❌ Error sending reset email")
        st.sidebar.error(e)

def logout():
    st.session_state.pop("user", None)
    st.sidebar.info("👋 Logged out successfully")

def show_sidebar():
    with st.sidebar:
        st.title("🔐 Authentication")

        if "user" not in st.session_state:
            tab1, tab2, tab3 = st.tabs(["Login", "Signup", "Forgot Password"])

            with tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Login"):
                    email = email.strip()
                    if login(email, password):
                        st.success(f"🎉 Welcome {email}")
                        st.experimental_set_query_params(logged_in="true")
                        st.stop()

            with tab2:
                new_email = st.text_input("New Email", key="signup_email")
                new_pass = st.text_input("New Password", type="password", key="signup_pass")
                if st.button("Create Account"):
                    signup(new_email.strip(), new_pass)

            with tab3:
                reset_email = st.text_input("Enter your email", key="reset_email")
                if st.button("Send Reset Email"):
                    reset_password(reset_email)

        else:
            user = st.session_state["user"]
            st.success(f"✅ Logged in as {user['email']}")
            if st.button("Logout"):
                logout()
                
