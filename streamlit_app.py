import streamlit as st
import requests
import base64
import urllib3
import time
import pyotp
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher # <--- ΕΔΩ ΕΓΙΝΕ Η ΑΛΛΑΓΗ

# --- 1. RUTHMISEIS ---
st.set_page_config(page_title="CU Booster Pro", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp {background-color: #ffffff;}
    div[data-testid="stForm"] {border: none; padding: 0;}
    .stButton button {width: 100%; font-weight: bold; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 3. ΦΟΡΤΩΣΗ SECRETS & SETUP AUTHENTICATOR ---
try:
    ADMIN_2FA_KEY = st.secrets["security"]["admin_2fa_key"]
    RAW_USERS = st.secrets["users"]
except:
    st.error("⚠️ Error: Secrets missing")
    st.stop()

# Setup Users
users_config = {}
for username, password in RAW_USERS.items():
    # Τώρα αυτό θα δουλέψει σωστά με την έκδοση 0.2.3
    hashed_pass = Hasher([str(password)]).generate()[0]
    users_config[username] = {
        "name": username,
        "password": hashed_pass,
        "email": f"{username}@cu.gr"
    }

credentials = {"usernames": users_config}
cookie_config = {"expiry_days": 30, "key": "cu_booster_auth_key", "name": "cu_booster_cookie"}

authenticator = stauth.Authenticate(
    credentials,
    cookie_config['name'],
    cookie_config['key'],
    cookie_config['expiry_days']
)

# --- 4. API FUNCTIONS ---
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
# --- MAIN LOGIC ---
# ==========================================

name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('❌ Λάθος στοιχεία')
elif authentication_status == None:
    st.info('Παρακαλώ συνδεθείτε.')
elif authentication_status == True:
    
    # Header & Logout
    c1, c2 = st.columns([3, 1])
    with c1: st.title("🚀 CU Booster")
    with c2: 
        st.write(f"👤 {name}")
        authenticator.logout('Έξοδος', 'main')

    if 'step' not in st.session_state: st.session_state.step = 1
    if 'phone' not in st.session_state: st.session_state.phone = ""
    if 'token' not in st.session_state: st.session_state.token = None

    if st.session_state.step == 1:
        with st.container(border=True):
            phone_input = st.text_input("Κινητό", placeholder="694...", max_chars=10)
            if st.button("SMS 📩", type="primary"):
                if len(phone_input)==10:
                    with st.spinner("Wait..."):
                        if api_send_sms(phone_input):
                            st.session_state.phone = phone_input
                            st.session_state.step = 2
                            st.rerun()
                        else: st.error("Error")
                else: st.warning("10 Digits")

    elif st.session_state.step == 2:
        with st.container(border=True):
            st.info(f"OTP: {st.session_state.phone}")
            otp_input = st.text_input("OTP Code")
            cc1, cc2 = st.columns(2)
            if cc1.button("Back"): st.session_state.step=1; st.rerun()
            if cc2.button("Verify", type="primary"):
                with st.spinner("Checking..."):
                    token = api_verify_otp(st.session_state.phone, otp_input)
                    if token: st.session_state.token=token; st.session_state.step=3; st.rerun()
                    else: st.error("Invalid OTP")

    elif st.session_state.step == 3:
        st.success(f"Active: {st.session_state.phone}")
        with st.container(border=True):
            pkg = st.radio("Package:", ["🥤 Shake (Data)", "🗣️ Voice"], horizontal=True)
            offer = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
            times = st.slider("Quantity:", 1, 50, 20)
            if st.button(f"ACTIVATE ({times}x) 🔥", type="primary"):
                bar = st.progress(0); succ = 0
                for i in range(times):
                    if api_activate(st.session_state.token, st.session_state.phone, offer) in [200, 201, 403]: succ+=1
                    bar.progress((i+1)/times)
                    time.sleep(0.05)
                st.success(f"Completed: {succ}/{times}")
        if st.button("New Number"):
            st.session_state.step=1; st.session_state.phone=""; st.session_state.token=None; st.rerun()
