import streamlit as st
import requests
import base64
import urllib3
import time
import pyotp
import extra_streamlit_components as stx
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher
import datetime

# --- 1. RUTHMISEIS ---
st.set_page_config(page_title="CU Booster", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. ELITE DARK CSS (PROFESSIONAL UI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Background: Deep Dark Theme */
    .stApp {
        background-color: #0e1117 !important;
        background-image: radial-gradient(circle at 50% 0%, #1c202b, #0e1117 60%);
        font-family: 'Inter', sans-serif !important;
    }

    /* Hide Elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* TEXT COLORS */
    h1, h2, h3, p, label, span { color: #e0e0e0 !important; }
    
    /* CARDS (Login & 2FA) - Minimal & Clean */
    div[data-testid="stForm"], div[data-testid="stExpander"], div.block-container {
        background-color: #161920 !important;
        border: 1px solid #2d3342 !important;
        border-radius: 16px !important;
        padding: 40px 30px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
        max-width: 450px !important;
        margin: auto !important;
    }

    /* INPUT FIELDS */
    div[data-testid="stTextInput"] input {
        background-color: #0e1117 !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #ff3b30 !important; /* CU Red */
        box-shadow: 0 0 0 1px rgba(255, 59, 48, 0.3) !important;
    }
    div[data-testid="stTextInput"] label {
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888 !important;
        margin-bottom: 5px !important;
    }

    /* BUTTONS (Primary Red) */
    div[data-testid="stButton"] button {
        background-color: #ff3b30 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(255, 59, 48, 0.2) !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #d63026 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(255, 59, 48, 0.3) !important;
    }
    div[data-testid="stButton"] button p { color: white !important; }

    /* LINK BUTTON (Support) */
    .stLinkButton a {
        background-color: transparent !important;
        color: #666 !important;
        border: 1px solid #333 !important;
        display: flex;
        justify-content: center;
        width: 100%;
        border-radius: 8px;
        transition: 0.3s;
        text-decoration: none;
    }
    .stLinkButton a:hover {
        border-color: #ff3b30 !important;
        color: #ff3b30 !important;
    }

    /* ALERTS */
    div[data-testid="stAlert"] {
        background-color: #1c202b !important;
        border: 1px solid #333 !important;
        color: #ccc !important;
    }
</style>
""", unsafe_allow_html=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 3. SECRETS ---
try:
    ADMIN_2FA_KEY = st.secrets["security"]["admin_2fa_key"]
    RAW_USERS = st.secrets["users"]
except:
    st.error("⚠️ Error: Secrets missing!")
    st.stop()

# --- 4. COOKIE MANAGER ---
cookie_manager = stx.CookieManager(key="mgr_final_pro")

# --- 5. AUTHENTICATOR ---
users_config = {}
for username, password in RAW_USERS.items():
    hashed_pass = Hasher([str(password)]).generate()[0]
    users_config[username] = {"name": username, "password": hashed_pass, "email": f"{username}@cu.gr"}

credentials = {"usernames": users_config}
cookie_config = {"expiry_days": 30, "key": "cu_auth_main", "name": "cu_auth_ck"}

authenticator = stauth.Authenticate(credentials, cookie_config['name'], cookie_config['key'], cookie_config['expiry_days'])

# --- 6. API FUNCTIONS ---
@st.cache_resource
def get_session(): s = requests.Session(); s.verify = False; return s
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

def api_send_sms(phone):
    try: return get_session().post(f"{AUTH_OTP_URL}/authorize", headers={"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}, data={"login_hint": f"+30{phone}", "response_type": "code"}).status_code in [200, 202]
    except: return False
def api_verify_otp(phone, otp):
    raw = f"30{phone}:{otp}"; enc = base64.b64encode(raw.encode()).decode()
    try: return get_session().post(f"{AUTH_OTP_URL}/token", headers={"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}, data={"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": enc}).json().get("access_token")
    except: return None
def api_activate(token, phone, offer):
    try: return get_session().post(ORDER_URL, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": USER_AGENT}, json={"productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer}}], "relatedParty": [{"role": "subscriber", "id": phone}]}).status_code
    except: return 999

# ==========================================
# --- LOGIC FLOW ---
# ==========================================

# Placeholder για να καθαρίζουμε το Login Form
login_placeholder = st.empty()

# Ελέγχουμε αν υπάρχει ήδη verification
cookie_2fa = cookie_manager.get("cu_free_pass")
is_verified_session = st.session_state.get("session_verified", False)

# --- LOGIN FORM ---
# Χρησιμοποιούμε το placeholder. Αν πετύχει το login, το καθαρίζουμε.
with login_placeholder.container():
    # Αν έχουμε login, δεν δείχνουμε τη φόρμα
    if not st.session_state.get("authentication_status"):
        name, authentication_status, username = authenticator.login('Member Access', 'main')
    else:
        name = st.session_state["name"]
        username = st.session_state["username"]
        authentication_status = True

# Λογική μετά το Login
if authentication_status:
    # 1. ΚΑΘΑΡΙΣΜΟΣ LOGIN FORM (Το κλειδί για να μην τα δείχνει διπλά)
    login_placeholder.empty()

    # 2. CHECK 2FA
    is_verified_cookie = (cookie_2fa == username)
    FINAL_ACCESS = is_verified_cookie or is_verified_session

    if not FINAL_ACCESS:
        # --- 2FA SCREEN ---
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #fff;'>🔐 Verification</h3>", unsafe_allow_html=True)
            # Απλό κείμενο, όχι alert
            st.markdown("<p style='text-align: center; color: #666; font-size: 13px;'>Enter your 2FA code to continue</p>", unsafe_allow_html=True)
            
            otp_code = st.text_input("Authenticator Code", max_chars=6, label_visibility="collapsed", placeholder="000 000")
            
            if st.button("VERIFY DEVICE", type="primary", use_container_width=True):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                if totp.verify(otp_code, valid_window=4):
                    st.session_state.session_verified = True
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("cu_free_pass", username, expires_at=expires)
                    st.rerun()
                else:
                    st.error("Invalid Code")
            
            st.divider()
            # Support Link
            st.link_button("💬 Support", "https://t.me/mrcrabx", use_container_width=True)
            
            # Logout
            if st.button("Cancel / Logout", use_container_width=True):
                 st.session_state["authentication_status"] = None
                 st.rerun()

    else:
        # --- MAIN APP (DASHBOARD) ---
        
        # Navbar style
        c1, c2 = st.columns([4, 1])
        with c1: st.title("🚀 CU Booster")
        with c2: 
            if st.button("Logout"):
                try: cookie_manager.delete("cu_free_pass", key="del_free")
                except: pass
                st.session_state.session_verified = False
                st.session_state["authentication_status"] = None
                try: cookie_manager.delete("cu_auth_ck", key="del_main")
                except: pass
                st.rerun()
        
        st.write(f"Logged in as: **{name}**")
        st.divider()

        if 'step' not in st.session_state: st.session_state.step = 1
        if 'phone' not in st.session_state: st.session_state.phone = ""
        if 'token' not in st.session_state: st.session_state.token = None

        if st.session_state.step == 1:
            with st.container(border=True):
                phone_input = st.text_input("Mobile Number", placeholder="694xxxxxxx", max_chars=10)
                if st.button("SEND SMS 📩", type="primary", use_container_width=True):
                    if len(phone_input)==10:
                        with st.spinner("Connecting to Vodafone..."):
                            if api_send_sms(phone_input):
                                st.session_state.phone = phone_input
                                st.session_state.step = 2
                                st.rerun()
                            else: st.error("Connection Failed")
                    else: st.warning("Invalid Number")

        elif st.session_state.step == 2:
            with st.container(border=True):
                st.info(f"OTP sent to: {st.session_state.phone}")
                otp_input = st.text_input("SMS Code", placeholder="1234")
                
                col1, col2 = st.columns(2)
                if col1.button("Back", use_container_width=True): 
                    st.session_state.step=1; st.rerun()
                if col2.button("VERIFY", type="primary", use_container_width=True):
                    with st.spinner("Verifying..."):
                        token = api_verify_otp(st.session_state.phone, otp_input)
                        if token: 
                            st.session_state.token=token
                            st.session_state.step=3
                            st.rerun()
                        else: st.error("Invalid Code")

        elif st.session_state.step == 3:
            st.success(f"Ready: {st.session_state.phone}")
            with st.container(border=True):
                pkg = st.radio("Select Package", ["🥤 Shake (Data)", "🗣️ Voice"], horizontal=True)
                offer = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
                times = st.slider("Quantity", 1, 50, 20)
                
                if st.button(f"ACTIVATE ({times}x) 🔥", type="primary", use_container_width=True):
                    bar = st.progress(0); succ = 0
                    for i in range(times):
                        if api_activate(st.session_state.token, st.session_state.phone, offer) in [200, 201, 403]: succ+=1
                        bar.progress((i+1)/times)
                        time.sleep(0.05)
                    st.success(f"Done: {succ}/{times} successful")
            
            if st.button("New Number", use_container_width=True):
                st.session_state.step=1; st.session_state.phone=""; st.session_state.token=None; st.rerun()

        # Footer Link
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.link_button("💬 Support", "https://t.me/mrcrabx", use_container_width=True)

# Αν υπάρχει λάθος στο login (λάθος κωδικός), το authenticator το χειρίζεται μόνο του
elif authentication_status == False:
    st.error('Incorrect Username/Password')
