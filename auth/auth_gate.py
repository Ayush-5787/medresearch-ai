"""
MedResearch AI — Auth gate (Streamlit UI for login/signup).
"""

import streamlit as st
from pathlib import Path
from auth.user_manager import create_user, authenticate, get_user_count


def init_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def render_login_screen():
    init_session()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        logo_path = Path(__file__).parent.parent / "docs" / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=120)

        st.markdown(
            "<div style='text-align:center;padding:1rem 0;'>"
            "<h1 style='color:#00d4ff;font-size:2rem;margin-bottom:0.3rem;'>MedResearch AI</h1>"
            "<p style='color:#888;font-size:0.95rem;'>Sign in to access the governed research system</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])

        with tab1:
            with st.form("login_form"):
                st.markdown("### Welcome back")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("🔑 Log In", use_container_width=True, type="primary")

                if submit:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        user = authenticate(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user = user
                            st.success("Welcome back, " + user["username"] + "!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")

        with tab2:
            with st.form("signup_form"):
                st.markdown("### Create your account")
                new_username = st.text_input("Username", key="signup_username", help="Min 3 characters")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password", help="Min 6 characters")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
                submit = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")

                if submit:
                    if new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif not all([new_username, new_email, new_password]):
                        st.error("Please fill in all fields")
                    else:
                        result = create_user(new_username, new_email, new_password)
                        if result["success"]:
                            st.success("✅ Account created! Please log in.")
                            st.balloons()
                        else:
                            st.error("❌ " + result["error"])

        st.markdown("---")
        st.caption("👥 " + str(get_user_count()) + " users registered · 🔒 Passwords secured with bcrypt")

    return st.session_state.get("authenticated", False)