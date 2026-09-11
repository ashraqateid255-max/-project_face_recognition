import streamlit as st
import requests

# ------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------
st.set_page_config(page_title="FaceGate AI · Face Attendance", page_icon="🛰️", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

API_URL = st.sidebar.text_input("Backend API URL", value="http://127.0.0.1:8000")

# ------------------------------------------------------------------
# Visual identity — "FaceGate AI" dark biometric console
# ------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --bg: #0A0E1A;
  --panel: #131A2E;
  --panel-2: #0D1220;
  --border: #212A42;
  --accent: #38BDF8;
  --accent-strong: #0EA5E9;
  --accent-soft: rgba(56,189,248,0.14);
  --text: #E7ECF6;
  --text-dim: #8B93A8;
  --success: #34D399;
  --danger: #FB7185;
  --warning: #FBBF24;
}

html, body, [class*="css"], .stApp, p, span, div, label {
  font-family: 'Inter', sans-serif;
  color: var(--text);
}

.stApp { background: var(--bg); }

[data-testid="stSidebar"] { background: var(--panel-2); border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text) !important; }

h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text) !important; }

/* ---------- Brand panel (left) ---------- */
.fg-brand {
  background: linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.6rem 1.4rem;
  height: 100%;
}
.fg-logo-row { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.2rem; }
.fg-logo-badge {
  width: 40px; height: 40px; border-radius: 10px;
  background: var(--accent-soft); border: 1px solid var(--accent);
  display: flex; align-items: center; justify-content: center; font-size: 1.15rem;
}
.fg-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700; line-height: 1.1; }
.fg-kicker {
  font-size: 0.68rem; letter-spacing: 0.14em; color: var(--accent);
  margin: 0.55rem 0 0.9rem 0; font-weight: 600;
}
.fg-desc { font-size: 0.86rem; color: var(--text-dim); line-height: 1.55; margin-bottom: 1.3rem; }

.fg-section-label {
  font-size: 0.7rem; letter-spacing: 0.08em; color: var(--text-dim);
  font-weight: 600; margin: 1.1rem 0 0.6rem 0; text-transform: uppercase;
}
.fg-action-row { display: flex; align-items: center; gap: 0.55rem; padding: 0.3rem 0; font-size: 0.85rem; }
.fg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.fg-dot-blue { background: var(--accent); }
.fg-dot-green { background: var(--success); }
.fg-dot-amber { background: var(--warning); }
.fg-dot-red { background: var(--danger); }

.fg-guide-row { padding: 0.4rem 0; border-top: 1px solid var(--border); }
.fg-guide-row:first-child { border-top: none; }
.fg-guide-title { display: flex; align-items: center; gap: 0.55rem; font-size: 0.85rem; font-weight: 600; }
.fg-guide-sub { font-size: 0.76rem; color: var(--text-dim); margin-left: 1.35rem; margin-top: 0.1rem; }

/* ---------- Right console ---------- */
.fg-topbar { display: flex; justify-content: flex-end; margin-bottom: 0.6rem; }
.fg-status-pill {
  font-size: 0.72rem; color: var(--success); background: rgba(52,211,153,0.1);
  border: 1px solid rgba(52,211,153,0.35); border-radius: 999px; padding: 0.25rem 0.75rem;
  display: inline-flex; align-items: center; gap: 0.4rem;
}
.fg-status-pill::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--success); }

.fg-steps { display: flex; gap: 0.9rem; margin-bottom: 1.1rem; }
.fg-step {
  flex: 1; background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
  padding: 1rem 1rem 0.9rem;
}
.fg-step-num {
  width: 26px; height: 26px; border-radius: 8px; background: var(--accent-soft);
  border: 1px solid var(--accent); color: var(--accent); font-weight: 700; font-size: 0.8rem;
  display: flex; align-items: center; justify-content: center; margin-bottom: 0.6rem;
}
.fg-step-title { font-weight: 600; font-size: 0.88rem; margin-bottom: 0.2rem; }
.fg-step-desc { font-size: 0.76rem; color: var(--text-dim); line-height: 1.4; }

/* ---------- Panel card wrapper (login/signup/checkin/checkout) ---------- */
.fg-card-marker { display: block; height: 0; }
.fg-card-marker + div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel) !important; border: 1px solid var(--border) !important;
  border-radius: 12px !important; padding: 1.3rem 1.2rem !important; position: relative !important;
}
.fg-card-label {
  position: absolute; top: -11px; left: 1rem; background: var(--bg);
  padding: 0 0.5rem; font-size: 0.68rem; letter-spacing: 0.08em; color: var(--accent);
  font-weight: 600; text-transform: uppercase;
}

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--border); }
[data-baseweb="tab"] { background: transparent; color: var(--text-dim) !important; font-weight: 600; font-size: 0.85rem; padding: 0.3rem 0 0.7rem 0; }
[data-baseweb="tab"][aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }
[data-baseweb="tab-highlight"] { background-color: transparent !important; }

/* ---------- Inputs / widgets ---------- */
.stTextInput input, [data-testid="stTextInput"] input {
  background: var(--panel-2) !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; border-radius: 8px !important;
}
.stTextInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 1px var(--accent) !important; }
label, .stTextInput label, [data-testid="stWidgetLabel"] p {
  color: var(--text-dim) !important; font-size: 0.78rem !important;
}

input[type="radio"] { accent-color: var(--accent); }
div[role="radiogroup"] { gap: 0.5rem; }
div[role="radiogroup"] label {
  border: 1px solid var(--border); border-radius: 8px; padding: 0.3rem 0.9rem !important;
  background: var(--panel-2);
}

[data-testid="stFileUploaderDropzone"], [data-testid="stCameraInput"] {
  background: var(--panel-2) !important; border: 1px dashed var(--border) !important; border-radius: 10px !important;
}

.stButton > button, [data-testid="stCameraInput"] button, [data-testid="stFileUploader"] button {
  border-radius: 8px !important; font-weight: 600; border: 1px solid var(--border) !important;
  background: var(--panel-2) !important; color: var(--text) !important;
}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button {
  background: var(--accent-strong) !important; color: #04121C !important; border: 1px solid var(--accent-strong) !important;
}
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover { background: var(--accent) !important; }
.stButton > button[kind="secondary"]:hover { border-color: var(--accent) !important; color: var(--accent) !important; }

[data-testid="stAlert"] { border-radius: 8px !important; background: var(--panel) !important; border: 1px solid var(--border) !important; }

/* ---------- Result banner ---------- */
.fg-result { border-radius: 10px; padding: 0.85rem 1rem; margin: 0.9rem 0; display: flex; align-items: flex-start; gap: 0.7rem; }
.fg-result-success { background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.35); }
.fg-result-error   { background: rgba(251,113,133,0.08); border: 1px solid rgba(251,113,133,0.35); }
.fg-result-info    { background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.35); }
.fg-result-icon { font-size: 1.1rem; }
.fg-result-msg { font-size: 0.85rem; }
.fg-result-time { font-size: 0.74rem; color: var(--text-dim); margin-top: 0.15rem; }

.stCaption, [data-testid="stCaptionContainer"] { color: var(--text-dim) !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Reusable layout pieces
# ------------------------------------------------------------------
def render_brand_panel():
    st.markdown("""
    <div class="fg-brand">
        <div class="fg-logo-row">
            <div class="fg-logo-badge">🛰️</div>
            <div class="fg-title">FaceGate AI</div>
        </div>
        <div class="fg-kicker">SMART FACE ATTENDANCE</div>
        <div class="fg-desc">
            AI-powered assistant that replaces badges and passwords with real-time
            face recognition — sign up once, then check in and out with a glance.
        </div>
        <div class="fg-section-label">Supported actions</div>
        <div class="fg-action-row"><span class="fg-dot fg-dot-blue"></span> New employee sign-up</div>
        <div class="fg-action-row"><span class="fg-dot fg-dot-blue"></span> Face login</div>
        <div class="fg-action-row"><span class="fg-dot fg-dot-blue"></span> Face check-in</div>
        <div class="fg-action-row"><span class="fg-dot fg-dot-blue"></span> Face check-out</div>
        <div class="fg-section-label">Status guide</div>
        <div class="fg-guide-row">
            <div class="fg-guide-title"><span class="fg-dot fg-dot-green"></span> Recognized</div>
            <div class="fg-guide-sub">Face matched — action completed successfully.</div>
        </div>
        <div class="fg-guide-row">
            <div class="fg-guide-title"><span class="fg-dot fg-dot-amber"></span> Already on file</div>
            <div class="fg-guide-sub">You've already checked in/out for today.</div>
        </div>
        <div class="fg-guide-row">
            <div class="fg-guide-title"><span class="fg-dot fg-dot-red"></span> Not recognized</div>
            <div class="fg-guide-sub">Face not found — try again or sign up first.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_steps(steps):
    cards = []
    for i, (title, desc) in enumerate(steps, start=1):
        cards.append(
            f'<div class="fg-step"><div class="fg-step-num">{i}</div>'
            f'<div class="fg-step-title">{title}</div>'
            f'<div class="fg-step-desc">{desc}</div></div>'
        )
    html = '<div class="fg-steps">' + "".join(cards) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def panel_card(label):
    st.markdown('<div class="fg-card-marker"></div>', unsafe_allow_html=True)
    box = st.container(border=True)
    with box:
        st.markdown(f'<div class="fg-card-label">{label}</div>', unsafe_allow_html=True)
    return box


def result_banner(kind, message, time_str=None):
    variant = {"success": ("fg-result-success", "✅"),
               "error": ("fg-result-error", "⚠️"),
               "info": ("fg-result-info", "🕒")}.get(kind, ("fg-result-info", "🕒"))
    css_class, icon = variant
    time_html = f'<div class="fg-result-time">{time_str}</div>' if time_str else ""
    st.markdown(f"""
    <div class="fg-result {css_class}">
        <span class="fg-result-icon">{icon}</span>
        <div><div class="fg-result-msg">{message}</div>{time_html}</div>
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
    col_left, col_right = st.columns([1, 1.35], gap="medium")

    with col_left:
        render_brand_panel()

    with col_right:
        st.markdown('<div class="fg-topbar"><span class="fg-status-pill">Backend connected</span></div>',
                     unsafe_allow_html=True)
        render_steps([
            ("Capture", "Take a live photo or upload one of your face."),
            ("Recognize", "The KNN model matches it against registered employees."),
            ("Confirm", "Get an instant sign-in result, no password needed."),
        ])

        tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

        with tab_login:
            card = panel_card("face login")
            with card:
                st.caption("Look at the camera or upload your photo to log in using face identification.")

                login_photo_source = st.radio("Login Photo Source", ["Take a photo", "Upload a photo"], horizontal=True, key="login_source")
                camera_login_photo, uploaded_login_photo = None, None

                if login_photo_source == "Take a photo":
                    camera_login_photo = st.camera_input("Face Scan Login", key="login_cam")
                else:
                    uploaded_login_photo = st.file_uploader("Upload face photo", type=["png", "jpg", "jpeg"], key="login_file")

                login_submitted = st.button("Log in with face", use_container_width=True, type="primary", key="login_btn")

                if login_submitted:
                    photo_file = camera_login_photo or uploaded_login_photo
                    if not photo_file:
                        result_banner("error", "Attach a face photo — take one or upload one.")
                    else:
                        files = {"file": (getattr(photo_file, "name", "login_photo.jpg"), photo_file.getvalue(), "image/jpeg")}
                        result = api_post("/login", files=files)
                        if result.get("status") == "success":
                            st.session_state.user = result["user_info"]
                            st.rerun()
                        else:
                            result_banner("error", result.get("message", "Login failed. Face not recognized."))

        with tab_signup:
            card = panel_card("new employee")
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

                signup_submitted = st.button("Create account", use_container_width=True, type="primary", key="signup_btn")

                if signup_submitted:
                    photo_file = camera_photo or uploaded_photo
                    if not all([new_username, new_password, full_name, title]):
                        result_banner("error", "Fill in every field before continuing.")
                    elif not photo_file:
                        result_banner("error", "Attach a photo — take one or upload one.")
                    else:
                        files = {"file": (getattr(photo_file, "name", "photo.jpg"), photo_file.getvalue(), "image/jpeg")}
                        data = {"username": new_username, "password": new_password, "full_name": full_name, "title": title}
                        result = api_post("/signup", data=data, files=files)
                        if result.get("status") == "success":
                            result_banner("success", result["message"] + " Log in from the Log in tab now.")
                        else:
                            result_banner("error", result.get("message", "Sign up failed."))


# ------------------------------------------------------------------
# 2. Check in / Check out
# ------------------------------------------------------------------
def render_main_screen():
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"""
        <div style="padding-top:0.4rem;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:1.05rem; font-weight:600;">{user['full_name']}</div>
            <div style="font-size:0.75rem; color:var(--text-dim);">{user['username']} — {user['title']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Log out", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

    col_left, col_right = st.columns([1, 1.35], gap="medium")

    with col_left:
        render_brand_panel()

    with col_right:
        st.markdown('<div class="fg-topbar"><span class="fg-status-pill">Backend connected</span></div>',
                     unsafe_allow_html=True)
        render_steps([
            ("Scan", "Take a live photo or upload one at the start/end of your shift."),
            ("Match", "The model matches your face against your registered profile."),
            ("Log", "Your check-in or check-out time is recorded instantly."),
        ])

        tab_in, tab_out = st.tabs(["Check in", "Check out"])

        # ---------- TAB: CHECK IN ----------
        with tab_in:
            card = panel_card("check-in scan")
            with card:
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
                        result_banner("error", "Attach a photo to check in.")
                    else:
                        files = {"file": (getattr(photo_in, "name", "checkin.jpg"), photo_in.getvalue(), "image/jpeg")}
                        result = api_post("/attendance/check-in", files=files)
                        status = result.get("status")
                        if status == "success":
                            result_banner("success", result["message"], time_str=result.get("check_in_time"))
                        elif status == "already_marked":
                            result_banner("info", result["message"], time_str=result.get("check_in_time"))
                        elif status == "unknown_person":
                            result_banner("error", result["message"])
                        else:
                            result_banner("error", result.get("message", "Check-in failed."))

        # ---------- TAB: CHECK OUT ----------
        with tab_out:
            card = panel_card("check-out scan")
            with card:
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
                        result_banner("error", "Attach a photo to check out.")
                    else:
                        files = {"file": (getattr(photo_out, "name", "checkout.jpg"), photo_out.getvalue(), "image/jpeg")}
                        result = api_post("/attendance/check-out", files=files)
                        status = result.get("status")
                        if status == "success":
                            result_banner("success", result["message"], time_str=result.get("check_out_time"))
                        elif status == "already_marked":
                            result_banner("info", result["message"], time_str=result.get("check_out_time"))
                        elif status == "unknown_person":
                            result_banner("error", result["message"])
                        else:
                            result_banner("error", result.get("message", "Check-out failed."))


# ------------------------------------------------------------------
# Router
# ------------------------------------------------------------------
if st.session_state.user is None:
    render_auth_screen()
else:
    render_main_screen()
