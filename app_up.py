import streamlit as st
import requests

# ------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------
st.set_page_config(page_title="Personnel File · Attendance", page_icon="📎", layout="centered")

if "user" not in st.session_state:
    st.session_state.user = None

API_URL = st.sidebar.text_input("Backend API URL", value="http://127.0.0.1:8000")

# ------------------------------------------------------------------
# Visual identity — "paper personnel file" system
# ------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&family=Courier+Prime:wght@400;700&display=swap');

:root {
  --paper: #EDE1C4;
  --paper-dark: #E3D3A9;
  --paper-card: #F2E9D2;
  --line: #C7B489;
  --ink: #332B1F;
  --ink-soft: #6B5D45;
  --stamp-green: #3F6B4A;
  --stamp-red: #A23B2E;
  --stamp-blue: #2C4A6E;
}

html, body, [class*="css"], .stApp, p, span, div, label {
  font-family: 'Courier Prime', monospace;
  color: var(--ink);
}

.stApp {
  background-color: var(--paper);
  background-image: repeating-linear-gradient(
      to bottom, rgba(51,43,31,0.05) 0px, rgba(51,43,31,0.05) 1px,
      transparent 1px, transparent 29px
  );
}

[data-testid="stSidebar"] {
  background: var(--paper-dark);
  border-right: 1px dashed var(--line);
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }

/* ---------- Letterhead ---------- */
.pf-header { display: flex; align-items: baseline; gap: 0.9rem;
  padding-bottom: 1rem; margin-bottom: 1.6rem; border-bottom: 3px double var(--ink); }
.pf-title { font-family: 'Special Elite', cursive; font-size: 1.5rem; color: var(--ink); }
.pf-sub { font-size: 0.78rem; color: var(--ink-soft); letter-spacing: 0.03em; }

/* ---------- Folder-tab card ---------- */
.pf-tab-marker { display: block; height: 0; }
.pf-tab-marker + div[data-testid="stVerticalBlockBorderWrapper"] {
  position: relative !important;
  background: var(--paper-card) !important;
  border: 1px solid var(--line) !important;
  border-radius: 0 8px 3px 3px !important;
  padding: 1.6rem 1.1rem 1rem !important;
  margin-top: 0.9rem !important;
  box-shadow: 2px 3px 0 rgba(51,43,31,0.08);
}
.pf-tab-label {
  position: absolute; top: -15px; left: 1rem;
  background: var(--paper-dark); border: 1px solid var(--line); border-bottom: none;
  border-radius: 4px 4px 0 0;
  padding: 0.15rem 0.8rem 0.35rem; z-index: 6;
  font-family: 'Special Elite', cursive; font-size: 0.68rem; letter-spacing: 0.06em;
  color: var(--ink-soft); text-transform: uppercase;
}

.pf-photo-corner { position: absolute; inset: 0; pointer-events: none; z-index: 5; }
.pf-photo-corner::before, .pf-photo-corner::after {
  content: ""; position: absolute; width: 0; height: 0; border-style: solid;
}
.pf-photo-corner::before { top: 0; left: 0; border-width: 20px 20px 0 0; border-color: var(--ink-soft) transparent transparent transparent; opacity: 0.55; }
.pf-photo-corner::after { bottom: 0; right: 0; border-width: 0 0 20px 20px; border-color: transparent transparent var(--ink-soft) transparent; opacity: 0.55; }

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] { gap: 1.8rem; border-bottom: 2px solid var(--ink); }
[data-baseweb="tab"] { background: transparent; color: var(--ink-soft) !important;
  font-family: 'Special Elite', cursive; font-size: 0.85rem; padding: 0.4rem 0 0.7rem 0; }
[data-baseweb="tab"][aria-selected="true"] { color: var(--ink) !important; border-bottom: 3px solid var(--stamp-blue) !important; }
[data-baseweb="tab-highlight"] { background-color: transparent !important; }

/* ---------- Inputs ---------- */
.stTextInput input, [data-testid="stTextInput"] input {
  background: var(--paper) !important; color: var(--ink) !important;
  border: 1px solid var(--ink-soft) !important; border-radius: 2px !important;
  font-family: 'Courier Prime', monospace !important;
}
.stTextInput input:focus { border-color: var(--stamp-blue) !important; box-shadow: 0 0 0 1px var(--stamp-blue) !important; }
label, .stTextInput label, [data-testid="stWidgetLabel"] p {
  color: var(--ink-soft) !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.05em;
}

div[role="radiogroup"] { gap: 0.5rem; }
div[role="radiogroup"] label {
  border: 1px dashed var(--ink-soft); border-radius: 2px; padding: 0.3rem 0.9rem !important;
  background: var(--paper);
}

.stButton > button, [data-testid="stCameraInput"] button, [data-testid="stFileUploader"] button {
  border-radius: 2px !important; font-family: 'Special Elite', cursive !important;
  letter-spacing: 0.03em; border: 2px solid var(--ink) !important; background: var(--paper) !important; color: var(--ink) !important;
}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button {
  background: var(--stamp-blue) !important; color: var(--paper-card) !important; border: 2px solid var(--stamp-blue) !important;
}
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {
  background: var(--ink) !important; border-color: var(--ink) !important;
}
.stButton > button[kind="secondary"]:hover { border-color: var(--stamp-blue) !important; color: var(--stamp-blue) !important; }

[data-testid="stAlert"] { border-radius: 2px !important; background: var(--paper-card) !important; border: 1px dashed var(--ink-soft) !important; }

.pf-stamp-wrap { margin: 0.9rem 0 1.1rem 0; }
.pf-stamp {
  display: inline-block; font-family: 'Special Elite', cursive; text-transform: uppercase;
  font-size: 1rem; letter-spacing: 0.09em; padding: 0.4rem 1rem;
  border: 3px solid currentColor; border-radius: 4px; transform: rotate(-4deg); opacity: 0.88;
}
.pf-stamp-approved { color: var(--stamp-green); }
.pf-stamp-denied { color: var(--stamp-red); }
.pf-stamp-onfile { color: var(--stamp-blue); }
.pf-stamp-note { display:block; margin-top: 0.5rem; font-size: 0.78rem; color: var(--ink-soft); transform: none; }
.pf-stamp-time { font-size: 0.72rem; color: var(--ink-soft); margin-top: 0.35rem; }

h1, h2, h3 { color: var(--ink) !important; font-family: 'Special Elite', cursive !important; font-weight: 400 !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--ink-soft) !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)


def render_header(subtitle):
    st.markdown(f"""
    <div class="pf-header">
        <div class="pf-title">Personnel File</div>
        <div class="pf-sub">— {subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def folder_card(tab_label):
    st.markdown('<div class="pf-tab-marker"></div>', unsafe_allow_html=True)
    box = st.container(border=True)
    with box:
        st.markdown(f'<div class="pf-tab-label">{tab_label}</div>', unsafe_allow_html=True)
    return box


def photo_frame():
    st.markdown('<div class="pf-tab-marker"></div>', unsafe_allow_html=True)
    box = st.container(border=True)
    with box:
        st.markdown('<div class="pf-photo-corner"></div>', unsafe_allow_html=True)
    return box


def stamp_block(kind, message, sub=None, time_str=None):
    variant = {"success": ("pf-stamp-approved", "verified"),
               "error": ("pf-stamp-denied", "not recognized"),
               "info": ("pf-stamp-onfile", "on file")}.get(kind, ("pf-stamp-onfile", "on file"))
    css_class, stamp_word = variant
    time_html = f'<div class="pf-stamp-time">{time_str}</div>' if time_str else ""
    st.markdown(f"""
    <div class="pf-stamp-wrap">
        <span class="pf-stamp {css_class}">{stamp_word}</span>
        <span class="pf-stamp-note">{message}</span>
        {time_html}
    </div>
    """, unsafe_allow_html=True)


def api_post(endpoint, data=None, files=None):
    try:
        resp = requests.post(f"{API_URL}{endpoint}", data=data, files=files, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Could not reach the server: {e}"}


def logout():
    st.session_state.user = None


# ------------------------------------------------------------------
# 1. Log in (Face Recognition via KNN) / Open a new employee file
# ------------------------------------------------------------------
def render_auth_screen():
    render_header("step 1 of 2 — sign in")
    tab_login, tab_signup = st.tabs(["Log in", "New employee file"])

    with tab_login:
        card = folder_card("access log")
        with card:
            st.caption("Look at the camera or upload your photo to log in using face identification.")
            
            login_photo_source = st.radio("Login Photo Source", ["Take a photo", "Upload a photo"], horizontal=True, key="login_source")
            camera_login_photo, uploaded_login_photo = None, None
            
            if login_photo_source == "Take a photo":
                camera_login_photo = st.camera_input("Face Scan Login", key="login_cam")
            else:
                uploaded_login_photo = st.file_uploader("Upload face photo", type=["png", "jpg", "jpeg"], key="login_file")

            login_submitted = st.button("Log in with Face", use_container_width=True, type="primary", key="login_btn")

            if login_submitted:
                photo_file = camera_login_photo or uploaded_login_photo
                if not photo_file:
                    stamp_block("error", "Attach a face photo — take one or upload one.")
                else:
                    files = {"file": (getattr(photo_file, "name", "login_photo.jpg"), photo_file.getvalue(), "image/jpeg")}
                    result = api_post("/login", files=files)
                    if result.get("status") == "success":
                        st.session_state.user = result["user_info"]
                        st.rerun()
                    else:
                        stamp_block("error", result.get("message", "Login failed. Face not recognized."))

    with tab_signup:
        card = folder_card("new hire intake")
        with card:
            st.caption("Attach a clear face photo — it's how you'll be recognized at check-in and check-out.")

            new_username = st.text_input("Choose a username", key="signup_username")
            new_password = st.text_input("Choose a password", type="password", key="signup_password")
            full_name = st.text_input("Full name", key="signup_fullname")
            title = st.text_input("Job title", value="Employee", key="signup_title")

            photo_source = st.radio("Photo source", ["Take a photo", "Upload a photo"], horizontal=True, key="signup_photosource")
            camera_photo, uploaded_photo = None, None
            
            if photo_source == "Take a photo":
                camera_photo = st.camera_input("Take your photo", key="signup_cam")
            else:
                uploaded_photo = st.file_uploader("Upload photo", type=["png", "jpg", "jpeg"], key="signup_file")

            signup_submitted = st.button("Open file", use_container_width=True, type="primary", key="signup_btn")

            if signup_submitted:
                photo_file = camera_photo or uploaded_photo
                if not all([new_username, new_password, full_name, title]):
                    stamp_block("error", "Fill in every field before continuing.")
                elif not photo_file:
                    stamp_block("error", "Attach a photo — take one or upload one.")
                else:
                    files = {"file": (getattr(photo_file, "name", "photo.jpg"), photo_file.getvalue(), "image/jpeg")}
                    data = {"username": new_username, "password": new_password, "full_name": full_name, "title": title}
                    result = api_post("/signup", data=data, files=files)
                    if result.get("status") == "success":
                        stamp_block("success", result["message"] + " Log in from the Log in tab now.")
                    else:
                        stamp_block("error", result.get("message", "Sign up failed."))


# ------------------------------------------------------------------
# 2. Check in / Check out
# ------------------------------------------------------------------
def render_main_screen():
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"""
        <div style="padding-top:0.4rem; font-family:'Courier Prime',monospace;">
            <div style="font-family:'Special Elite',cursive; font-size:1.05rem;">{user['full_name']}</div>
            <div style="font-size:0.75rem; color:var(--ink-soft);">{user['username']} — {user['title']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Log out", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

    render_header("step 2 of 2 — timesheet")

    tab_in, tab_out = st.tabs(["Check in", "Check out"])

    # ---------- TAB: CHECK IN ----------
    with tab_in:
        frame = photo_frame()
        with frame:
            st.caption("Take a photo or upload one to check in.")
            
            in_source = st.radio("Check-in Photo Source", ["Take a photo", "Upload a photo"], horizontal=True, key="in_source")
            camera_in, uploaded_in = None, None
            
            if in_source == "Take a photo":
                camera_in = st.camera_input("Check-in capture", key="checkin_cam", label_visibility="collapsed")
            else:
                uploaded_in = st.file_uploader("Upload check-in photo", type=["png", "jpg", "jpeg"], key="checkin_file")

        photo_in = camera_in or uploaded_in
        if st.button("Confirm check-in", use_container_width=True, type="primary", key="checkin_btn"):
            if not photo_in:
                stamp_block("error", "Attach a photo to check in.")
            else:
                files = {"file": (getattr(photo_in, "name", "checkin.jpg"), photo_in.getvalue(), "image/jpeg")}
                result = api_post("/attendance/check-in", files=files)
                status = result.get("status")
                if status == "success":
                    stamp_block("success", result["message"], time_str=result.get("check_in_time"))
                elif status == "already_marked":
                    stamp_block("info", result["message"], time_str=result.get("check_in_time"))
                elif status == "unknown_person":
                    stamp_block("error", result["message"])
                else:
                    stamp_block("error", result.get("message", "Check-in failed."))

    # ---------- TAB: CHECK OUT ----------
    with tab_out:
        frame = photo_frame()
        with frame:
            st.caption("Take a photo or upload one to check out.")
            
            out_source = st.radio("Check-out Photo Source", ["Take a photo", "Upload a photo"], horizontal=True, key="out_source")
            camera_out, uploaded_out = None, None
            
            if out_source == "Take a photo":
                camera_out = st.camera_input("Check-out capture", key="checkout_cam", label_visibility="collapsed")
            else:
                uploaded_out = st.file_uploader("Upload check-out photo", type=["png", "jpg", "jpeg"], key="checkout_file")

        photo_out = camera_out or uploaded_out
        if st.button("Confirm check-out", use_container_width=True, type="primary", key="checkout_btn"):
            if not photo_out:
                stamp_block("error", "Attach a photo to check out.")
            else:
                files = {"file": (getattr(photo_out, "name", "checkout.jpg"), photo_out.getvalue(), "image/jpeg")}
                result = api_post("/attendance/check-out", files=files)
                status = result.get("status")
                if status == "success":
                    stamp_block("success", result["message"], time_str=result.get("check_out_time"))
                elif status == "already_marked":
                    stamp_block("info", result["message"], time_str=result.get("check_out_time"))
                elif status == "unknown_person":
                    stamp_block("error", result["message"])
                else:
                    stamp_block("error", result.get("message", "Check-out failed."))


# ------------------------------------------------------------------
# Router
# ------------------------------------------------------------------
if st.session_state.user is None:
    render_auth_screen()
else:
    render_main_screen()