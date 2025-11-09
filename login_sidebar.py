import streamlit as st
import pyrebase

# --- Firebase Init (initialize only once) ---
if "firebase" not in st.session_state:
    firebaseConfig = st.secrets["authentication"]
    firebase = pyrebase.initialize_app(firebaseConfig)
    st.session_state["firebase"] = firebase
    st.session_state["auth"] = firebase.auth()

auth = st.session_state["auth"]

# --- Auth Functions ---
def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.session_state["user"] = user
        st.session_state["logged_in"] = True
        st.sidebar.success(f"🎉 Welcome {email}")
        return True
    except Exception as e:
        st.sidebar.error("❌ Login failed. Check your email or password.")
        st.sidebar.error(str(e))
        return False

def signup(email, password):
    try:
        auth.create_user_with_email_and_password(email, password)
        st.sidebar.success("✅ Account created successfully! Please log in.")
    except Exception as e:
        st.sidebar.error("❌ Signup failed")
        st.sidebar.error(str(e))

def reset_password(email):
    try:
        auth.send_password_reset_email(email)
        st.sidebar.success("📩 Password reset email sent!")
    except Exception as e:
        st.sidebar.error("❌ Error sending reset email")
        st.sidebar.error(str(e))

def logout():
    st.session_state.pop("user", None)
    st.session_state["logged_in"] = False
    st.sidebar.info("👋 Logged out successfully")

# --- Sidebar UI ---
def show_sidebar():
    with st.sidebar:
        st.title("🔐 Authentication")

        if not st.session_state.get("logged_in", False):
            tab1, tab2 = st.tabs(["Login", "Forgot Password"])

            with tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Login"):
                    if email and password:
                        if login(email.strip(), password):
                            st.rerun()
            with tab2:
                reset_email = st.text_input("Enter your email", key="reset_email")
                if st.button("Send Reset Email"):
                    if reset_email:
                        reset_password(reset_email)

        else:
            user = st.session_state.get("user", {})
            st.success(f"✅ Logged in as {user.get('email', 'User')}")
            if st.button("Logout"):
                logout()
                st.rerun()
