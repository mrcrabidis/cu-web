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

# --- 2. ELITE DARK CSS (CLEAN & POLISHED) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* 1. Background (Deep Dark) */
    .stApp {
        background-color: #0e1117 !important;
        background-image: radial-gradient(circle at 50% 0%, #1c202b, #0e1117 90%);
        font-family: 'Inter', sans-serif !important;
    }
    
    /* 2. Spacing Fix (Για να μην κολλάει πάνω) */
    div.block-container {
        padding-top: 4rem !important;
        padding-bottom: 4rem !important;
        max-width: 520px !important;
    }

    /* Hide Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Text Colors */
    h1, h2, h3, p, label, span, div { color: #e0e0e0 !important; }
    
    /* 3. CARDS DESIGN (Στοχευμένο CSS για να μην χαλάει τον τίτλο) */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #161920 !important;
        border: 1px solid #2d3342 !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4) !important;
        padding: 30px !important;
    }
    
    /* Ειδικό στυλ για το container των inputs (για να φαίνεται σαν κάρτα) */
    div.element-container img {
        border-radius: 10px;
    }

    /* Inputs (Modern Look) */
    div[data-testid="stTextInput"] input {
        background-color: #0e1117 !important;
        color: #fff !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #ff3b30 !important;
        box-shadow: 0 0 0 1px rgba(255, 59, 48, 0.3) !important;
    }

    /* Buttons (Premium Gradient) */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #ff3b30 0%, #d63026 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        box-shadow: 0 4px 15px rgba(255, 59, 48, 0.25) !important;
        width: 100%;
        transition: transform 0.2s;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 59, 48, 0.4) !important;
    }
    div[data-testid="stButton"] button p { color: white !important; }

    /* Support Link */
    .stLinkButton a {
        color: #666 !important;
        border: 1px solid #333 !important;
        text-align: center;
        border-radius: 10px;
        transition: 0.3s;
        text-decoration: none;
        display: block;
        padding: 10px;
        background-color: #161920;
    }
    .stLinkButton a:hover {
        border-color: #ff3b30 !important;
        color: #ff3b30 !important;
    }
    
    /* Alerts */
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
cookie_manager = stx.CookieManager(key="free_pass_final_v2")

# --- 5. AUTHENTICATOR ---
users_config = {}
for username, password in RAW_USERS.items():
    hashed_pass = Hasher([str(password)]).generate()[0]
    users_config[username] = {"name": username, "password": hashed_pass, "email": f"{username}@cu.gr"}

credentials = {"usernames": users_config}
cookie_config = {"expiry_days": 30, "key": "cu_main_auth", "name": "cu_main_cookie"}

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
# --- LOGIC START ---
# ==========================================

login_placeholder = st.empty()

# --- CHECK COOKIE ---
cookie_2fa = cookie_manager.get("cu_free_pass")

# --- LOGIN FORM ---
with login_placeholder.container():
    if not st.session_state.get("authentication_status"):
        name, authentication_status, username = authenticator.login('Member Access', 'main')
    else:
        name = st.session_state["name"]
        username = st.session_state["username"]
        authentication_status = True

# --- MAIN LOGIC ---
if authentication_status:
    login_placeholder.empty()

    is_verified_cookie = (cookie_2fa == username)
    is_verified_session = st.session_state.get("session_verified", False)
    
    FINAL_ACCESS = is_verified_cookie or is_verified_session
    
    if not FINAL_ACCESS:
        # --- 2FA SCREEN ---
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🔐 Verification</h3>", unsafe_allow_html=True)
            st.info("Required for new devices")
            
            otp_code = st.text_input("6-digit Code", max_chars=6, label_visibility="collapsed", placeholder="Code from Authenticator")
            
            if st.button("VERIFY DEVICE 🚀", type="primary"):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                if totp.verify(otp_code, valid_window=4):
                    st.session_state.session_verified = True
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("cu_free_pass", username, expires_at=expires)
                    
                    st.success("✅ Success! Redirecting...")
                    with st.spinner("Saving session..."):
                        time.sleep(2) 
                    st.rerun()
                else:
                    st.error("❌ Invalid Code")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.link_button("💬 Support", "https://t.me/mrcrabx", use_container_width=True)
            
            if st.button("Logout"):
                authenticator.logout('Logout', 'main')

    else:
        # --- DASHBOARD UI (HEADER FIX) ---
        
        # Χρησιμοποιούμε Columns για να βάλουμε Τίτλο και Logout στην ίδια ευθεία
        # [3, 1] σημαίνει ο τίτλος πιάνει το 75% και το κουμπί το 25%
        c1, c2 = st.columns([3, 1.2], gap="medium")
        
        with c1:
            st.markdown(f"<h2 style='margin:0; padding-top: 5px;'>🚀 CU Booster</h2>", unsafe_allow_html=True)
            st.caption(f"Logged in as: {name}")
        
        with c2:
            if st.button("🚪 Logout", use_container_width=True):
                cookie_manager.delete("cu_free_pass")
                st.session_state.session_verified = False
                authenticator.logout('Logout', 'main')
        
        st.divider()

        # --- APP LOGIC ---
        if 'step' not in st.session_state: st.session_state.step = 1
        if 'phone' not in st.session_state: st.session_state.phone = ""
        if 'token' not in st.session_state: st.session_state.token = None

        if st.session_state.step == 1:
            with st.container(border=True):
                st.markdown("**Mobile Number**")
                phone_input = st.text_input("Mobile Number", placeholder="694xxxxxxx", max_chars=10, label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("SEND SMS 📩", type="primary"):
                    if len(phone_input)==10:
                        with st.spinner("Connecting..."):
                            if api_send_sms(phone_input):
                                st.session_state.phone = phone_input
                                st.session_state.step = 2
                                st.rerun()
                            else: st.error("Connection Failed")
                    else: st.warning("10 Digits Required")

        elif st.session_state.step == 2:
            with st.container(border=True):
                st.success(f"OTP Sent to: **{st.session_state.phone}**")
                otp_input = st.text_input("SMS Code", placeholder="1234")
                
                col1, col2 = st.columns(2)
                if col1.button("⬅️ Back"): st.session_state.step=1; st.rerun()
                if col2.button("VERIFY ✅", type="primary"):
                    with st.spinner("Checking..."):
                        token = api_verify_otp(st.session_state.phone, otp_input)
                        if token: st.session_state.token=token; st.session_state.step=3; st.rerun()
                        else: st.error("Invalid OTP")

        elif st.session_state.step == 3:
            st.success(f"Active: {st.session_state.phone}")
            with st.container(border=True):
                pkg = st.radio("Package", ["🥤 Shake (Data)", "🗣️ Voice"], horizontal=True)
                offer = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
                
                st.write("Quantity")
                times = st.slider("Quantity", 1, 50, 20, label_visibility="collapsed")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"ACTIVATE ({times}x) 🔥", type="primary"):
                    bar = st.progress(0); succ = 0
                    for i in range(times):
                        if api_activate(st.session_state.token, st.session_state.phone, offer) in [200, 201, 403]: succ+=1
                        bar.progress((i+1)/times)
                        time.sleep(0.05)
                    st.success(f"Done: {succ}/{times}")
            
            if st.button("🔄 New Number", use_container_width=True):
                st.session_state.step=1; st.session_state.phone=""; st.session_state.token=None; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("💬 Contact Support", "https://t.me/mrcrabx", use_container_width=True)

elif authentication_status == False:
    st.error('Incorrect Credentials')
