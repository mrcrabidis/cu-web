import streamlit as st
import requests
import base64
import urllib3
import time
import pyotp
import datetime
import extra_streamlit_components as stx

# --- 1. RUTHMISEIS SELIDAS (ΠΡΩΤΟ) ---
st.set_page_config(
    page_title="CU Booster Pro",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ΦΟΡΤΩΣΗ SECRETS ---
try:
    ADMIN_2FA_KEY = st.secrets["security"]["admin_2fa_key"]
    SYSTEM_USERS = st.secrets["users"]
except Exception as e:
    st.error("⚠️ ΣΦΑΛΜΑ: Δεν βρέθηκαν τα Secrets!")
    st.info("Πήγαινε στο Streamlit Dashboard -> Settings -> Secrets και πρόσθεσέ τα.")
    st.stop()

# --- 3. COOKIE MANAGER SETUP (ΔΙΟΡΘΩΜΕΝΟ) ---
# ΣΗΜΑΝΤΙΚΟ: Προσθέσαμε key="auth_cookie_manager" για να μην χάνεται η αναφορά
cookie_manager = stx.CookieManager(key="auth_cookie_manager")

# --- SYNC FIX: Περιμένουμε λίγο και κάνουμε rerun την πρώτη φορά ---
if "cookies_synced" not in st.session_state:
    time.sleep(0.7) # Αυξήθηκε ελάχιστα για σιγουριά
    st.session_state.cookies_synced = True
    st.rerun()

# --- 4. CSS STYLING ---
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stCard {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stButton button {
        height: 3em;
        font-weight: bold;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- API CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- FUNCTIONS ---
def get_session():
    s = requests.Session(); s.verify = False; return s

def api_send_sms(phone):
    session = get_session()
    headers = {"Accept": "*/*", "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = session.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data={"login_hint": f"+30{phone}", "response_type": "code"})
        return res.status_code in [200, 202]
    except: return False

def api_verify_otp(phone, otp):
    session = get_session()
    headers = {"Accept": "*/*", "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    raw = f"30{phone}:{otp}"
    enc = base64.b64encode(raw.encode()).decode()
    try:
        res = session.post(f"{AUTH_OTP_URL}/token", headers=headers, data={"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": enc})
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def api_activate(token, phone, offer):
    session = get_session()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json", "User-Agent": USER_AGENT}
    payload = {"productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer}}], "relatedParty": [{"role": "subscriber", "id": phone}]}
    try:
        res = session.post(ORDER_URL, headers=headers, json=payload)
        return res.status_code
    except: return 999

# ==========================================
# --- SECURITY LOGIC (ΔΙΟΡΘΩΜΕΝΗ) ---
# ==========================================

# 1. Προσπάθεια ανάγνωσης ΤΟΥ ΣΥΓΚΕΚΡΙΜΕΝΟΥ cookie (πιο αξιόπιστο από get_all)
cookie_user = cookie_manager.get(cookie="cu_app_user")

# Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "system_username" not in st.session_state:
    st.session_state.system_username = ""
if "user_verified" not in st.session_state: 
    st.session_state.user_verified = False

# 2. ΑΥΤΟΜΑΤΟ LOGIN ΑΝ ΒΡΕΘΗΚΕ COOKIE
if not st.session_state.authenticated and cookie_user:
    # Επιβεβαίωση ότι ο χρήστης υπάρχει ακόμα στα secrets
    if cookie_user in SYSTEM_USERS:
        st.session_state.authenticated = True
        st.session_state.system_username = cookie_user
        st.rerun() 

def login_system():
    st.markdown("<h2 style='text-align: center;'>🔐 Secure Access</h2>", unsafe_allow_html=True)
    
    # ΦΑΣΗ 1: Username / Password
    if not st.session_state.user_verified:
        with st.container(border=True):
            st.subheader("Βήμα 1: Ταυτοποίηση")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            
            if st.button("Έλεγχος", use_container_width=True):
                if u in SYSTEM_USERS and SYSTEM_USERS[u] == p:
                    st.session_state.user_verified = True
                    st.session_state.system_username = u
                    st.rerun()
                else:
                    st.error("Λάθος στοιχεία.")
    
    # ΦΑΣΗ 2: Admin Token
    else:
        with st.container(border=True):
            st.subheader("Βήμα 2: Έγκριση Admin")
            st.info(f"Γειά σου **{st.session_state.system_username}**. Ζήτα τον κωδικό από τον Admin.")
            
            otp_code = st.text_input("Κωδικός Admin (6-ψήφιος)", max_chars=6)
            
            if st.button("Είσοδος στο App 🚀", use_container_width=True, type="primary"):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                if totp.verify(otp_code):
                    st.session_state.authenticated = True
                    
                    # --- ΑΠΟΘΗΚΕΥΣΗ COOKIE ---
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("cu_app_user", st.session_state.system_username, expires_at=expires, key="set_cookie")
                    
                    st.toast("Επιτυχία! Καλωσήρθατε.", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Ο κωδικός είναι λάθος ή έληξε.")
            
            if st.button("🔙 Αλλαγή Χρήστη"):
                st.session_state.user_verified = False
                st.rerun()

# --- MAIN CONTROLLER ---
if not st.session_state.authenticated:
    login_system()
    st.stop()

# ==========================================
# --- MAIN APP ---
# ==========================================

if 'step' not in st.session_state: st.session_state.step = 1
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# Header & Logout
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("<h1 style='text-align: left;'>🚀 CU Booster</h1>", unsafe_allow_html=True)
with col_head2:
    st.caption(f"User: {st.session_state.system_username}")
    if st.button("🔴 Exit"):
        # Διαγραφή cookie με το κλειδί του manager
        cookie_manager.delete("cu_app_user", key="del_cookie")
        st.session_state.authenticated = False
        st.session_state.user_verified = False
        st.session_state.step = 1
        st.rerun()

# --- APP LOGIC (Steps 1, 2, 3) ---
if st.session_state.step == 1:
    with st.container(border=True):
        st.subheader("📲 Σύνδεση CU")
        phone_input = st.text_input("Κινητό Τηλέφωνο", placeholder="694...", max_chars=10)
        
        if st.button("Αποστολή SMS 📩", use_container_width=True, type="primary"):
            if len(phone_input) == 10:
                with st.spinner("Σύνδεση με Vodafone..."):
                    if api_send_sms(phone_input):
                        st.session_state.phone = phone_input
                        st.session_state.step = 2
                        st.rerun()
                    else: st.error("❌ Αποτυχία σύνδεσης.")
            else: st.warning("⚠️ 10 ψηφία απαιτούνται.")

elif st.session_state.step == 2:
    with st.container(border=True):
        st.subheader("🔐 Επαλήθευση SMS")
        st.info(f"Kωδικός εστάλη στο **{st.session_state.phone}**")
        otp_input = st.text_input("Κωδικός OTP", placeholder="123456")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Πίσω", use_container_width=True):
                st.session_state.step = 1; st.rerun()
        with col2:
            if st.button("Είσοδος", use_container_width=True, type="primary"):
                with st.spinner("Έλεγχος..."):
                    token = api_verify_otp(st.session_state.phone, otp_input)
                    if token:
                        st.session_state.token = token; st.session_state.step = 3; st.rerun()
                    else: st.error("❌ Λάθος OTP.")

elif st.session_state.step == 3:
    st.success(f"Συνδεθήκατε στο: **{st.session_state.phone}**")
    with st.container(border=True):
        st.subheader("📦 Επιλογή Πακέτου")
        pkg = st.radio("Διάλεξε:", ["🥤 CU Shake (Data)", "🗣️ Voice Bonus"], horizontal=True)
        offer_id = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
        times = st.slider("Ποσότητα (x φορές):", 1, 50, 20)
        
        if st.button(f"ΕΝΕΡΓΟΠΟΙΗΣΗ ({times}x) 🔥", use_container_width=True, type="primary"):
            bar = st.progress(0); stats = st.empty(); success_count = 0
            for i in range(times):
                stats.markdown(f"⏳ Εκτέλεση: **{i+1}/{times}**")
                code = api_activate(st.session_state.token, st.session_state.phone, offer_id)
                if code in [200, 201, 403]: success_count += 1
                bar.progress((i+1)/times); time.sleep(0.3)
            st.balloons(); st.success(f"✅ Τέλος! ({success_count}/{times} Επιτυχίες)")
            
    if st.button("🔄 Νέο Νούμερο", use_container_width=True):
        st.session_state.step = 1; st.session_state.phone = ""; st.session_state.token = None; st.rerun()
