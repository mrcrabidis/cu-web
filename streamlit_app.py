import streamlit as st
import requests
import base64
import urllib3
import time
import pyotp
import datetime
import extra_streamlit_components as stx

# --- 1. RUTHMISEIS SELIDAS ---
st.set_page_config(page_title="CU Booster Pro", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. ΦΟΡΤΩΣΗ SECRETS ---
try:
    ADMIN_2FA_KEY = st.secrets["security"]["admin_2fa_key"]
    SYSTEM_USERS = st.secrets["users"]
except:
    st.error("⚠️ ΣΦΑΛΜΑ: Λείπουν τα Secrets!")
    st.stop()

# --- 3. COOKIE MANAGER (Lightweight) ---
cookie_manager = stx.CookieManager(key="auth_manager")

# --- 4. CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stCard {background-color: #f0f2f6; padding: 20px; border-radius: 15px; margin-bottom: 20px;}
    .stButton button {height: 3em; font-weight: bold;}
</style>
""", unsafe_allow_html=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- API OPTIMIZATION (CACHE SESSION) ---
# Αυτό κρατάει ανοιχτή τη σύνδεση με Vodafone για να μην την ανοίγει κάθε φορά (Πολύ πιο γρήγορο)
@st.cache_resource
def get_session():
    s = requests.Session()
    s.verify = False
    return s

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
# --- SECURITY LOGIC (FAST VERSION) ---
# ==========================================

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "system_username" not in st.session_state: st.session_state.system_username = ""

# 1. Γρήγορος έλεγχος Cookie
# Χρησιμοποιούμε get_all() γιατί είναι συνήθως πιο γρήγορο στο cache του browser
cookies = cookie_manager.get_all()
cookie_user = cookies.get("cu_user_fast")

# 2. Αν βρούμε cookie, κάνουμε login ΧΩΡΙΣ καθυστέρηση
if not st.session_state.authenticated and cookie_user:
    if cookie_user in SYSTEM_USERS:
        st.session_state.authenticated = True
        st.session_state.system_username = cookie_user
        st.rerun()

def login_page():
    st.markdown("<h2 style='text-align: center;'>🔐 Secure Access</h2>", unsafe_allow_html=True)
    
    if "user_verified" not in st.session_state: st.session_state.user_verified = False

    if not st.session_state.user_verified:
        with st.container(border=True):
            st.subheader("Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Next", use_container_width=True):
                if u in SYSTEM_USERS and SYSTEM_USERS[u] == p:
                    st.session_state.user_verified = True
                    st.session_state.system_username = u
                    st.rerun()
                else: st.error("Λάθος στοιχεία")
    else:
        with st.container(border=True):
            st.info(f"User: **{st.session_state.system_username}**")
            otp_code = st.text_input("Admin Code", max_chars=6)
            if st.button("Login 🚀", use_container_width=True, type="primary"):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                if totp.verify(otp_code):
                    st.session_state.authenticated = True
                    # Γράφουμε το cookie και συνεχίζουμε ΑΜΕΣΩΣ
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("cu_user_fast", st.session_state.system_username, expires_at=expires)
                    st.rerun()
                else: st.error("Λάθος κωδικός")
            if st.button("Back"): st.session_state.user_verified = False; st.rerun()

if not st.session_state.authenticated:
    login_page()
    st.stop()

# ==========================================
# --- MAIN APP ---
# ==========================================

if 'step' not in st.session_state: st.session_state.step = 1
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

col1, col2 = st.columns([3,1])
with col1: st.title("🚀 CU Booster")
with col2:
    st.caption(f"👤 {st.session_state.system_username}")
    if st.button("Exit"):
        cookie_manager.delete("cu_user_fast")
        st.session_state.clear()
        st.rerun()

if st.session_state.step == 1:
    with st.container(border=True):
        phone_input = st.text_input("Κινητό", placeholder="694...", max_chars=10)
        if st.button("SMS 📩", use_container_width=True, type="primary"):
            if len(phone_input)==10:
                with st.spinner("Wait..."):
                    if api_send_sms(phone_input):
                        st.session_state.phone = phone_input
                        st.session_state.step = 2
                        st.rerun()
                    else: st.error("Σφάλμα")
            else: st.warning("10 ψηφία")

elif st.session_state.step == 2:
    with st.container(border=True):
        st.info(f"OTP στο {st.session_state.phone}")
        otp_input = st.text_input("OTP Code")
        c1, c2 = st.columns(2)
        if c1.button("Πίσω", use_container_width=True): st.session_state.step=1; st.rerun()
        if c2.button("Enter", use_container_width=True, type="primary"):
            with st.spinner("Verifying..."):
                token = api_verify_otp(st.session_state.phone, otp_input)
                if token: st.session_state.token=token; st.session_state.step=3; st.rerun()
                else: st.error("Λάθος OTP")

elif st.session_state.step == 3:
    st.success(f"Connected: {st.session_state.phone}")
    with st.container(border=True):
        pkg = st.radio("Πακέτο:", ["🥤 Shake (Data)", "🗣️ Voice"], horizontal=True)
        offer = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
        times = st.slider("Ποσότητα:", 1, 50, 20)
        if st.button(f"ΕΝΕΡΓΟΠΟΙΗΣΗ ({times}x) 🔥", use_container_width=True, type="primary"):
            bar = st.progress(0); succ = 0
            for i in range(times):
                if api_activate(st.session_state.token, st.session_state.phone, offer) in [200, 201, 403]: succ+=1
                bar.progress((i+1)/times)
                # Αφαίρεσα το time.sleep(0.3) ή το μείωσα πολύ για ταχύτητα
                time.sleep(0.1) 
            st.success(f"Τέλος: {succ}/{times}")
    if st.button("Νέο Νούμερο", use_container_width=True):
        st.session_state.step=1; st.session_state.phone=""; st.session_state.token=None; st.rerun()
