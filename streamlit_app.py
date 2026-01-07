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
st.set_page_config(page_title="CU Booster Pro", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS STYLING (PERMANENT DARK MODE) ---
st.markdown("""
<style>
    /* 1. Εισαγωγή Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* 2. Γενικό Φόντο Εφαρμογής (Σκούρο) */
    .stApp {
        background-color: #0e1117 !important; /* Πολύ σκούρο γκρι/μαύρο */
        font-family: 'Inter', sans-serif !important;
    }

    /* 3. Χρώμα Κειμένου (Λευκό για να φαίνεται στο μαύρο) */
    h1, h2, h3, h4, h5, h6, p, span, div[data-testid="stMarkdownContainer"] p {
        color: #e6e6e6 !important; /* Απαλό λευκό */
    }
    
    /* Εξαίρεση: Κείμενο μέσα στα κουμπιά */
    button p { color: #ffffff !important; }

    /* 4. Κάρτες (Login, Forms) - Σκούρο Γκρι */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #262730 !important; /* Σκούρο γκρι για τις κάρτες */
        border: 1px solid #3b3c3d !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important; /* Σκιά */
        padding: 30px !important;
    }

    /* 5. Inputs (Κουτάκια κειμένου) - Μαύρο φόντο, Λευκά γράμματα */
    div[data-testid="stTextInput"] input {
        background-color: #161b22 !important; /* Σχεδόν μαύρο */
        color: #ffffff !important; /* Λευκά γράμματα */
        border: 1px solid #454749 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    /* Όταν κάνεις κλικ στο κουτί */
    div[data-testid="stTextInput"] input:focus {
        border-color: #e60000 !important; /* Κόκκινο περίγραμμα */
        box-shadow: 0 0 0 1px #e60000 !important;
    }
    
    /* Τα Labels (π.χ. "Username") πάνω από τα κουτιά */
    div[data-testid="stTextInput"] label {
        color: #b0b0b0 !important; /* Γκρι ανοιχτό */
        font-size: 14px !important;
    }

    /* 6. Κουμπιά (Vodafone Red - Glowing) */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #e60000 0%, #990000 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 12px rgba(230, 0, 0, 0.4) !important; /* Κόκκινη λάμψη */
        transition: all 0.3s ease;
    }

    div[data-testid="stButton"] button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 16px rgba(230, 0, 0, 0.6) !important;
    }

    /* 7. Alerts */
    div[data-testid="stAlert"] {
        background-color: #262730 !important;
        color: #e6e6e6 !important;
        border: 1px solid #454749 !important;
    }

    /* Απόκρυψη */
    #MainMenu, footer, header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)
# --- 3. SECRETS ---
try:
    ADMIN_2FA_KEY = st.secrets["security"]["admin_2fa_key"]
    RAW_USERS = st.secrets["users"]
except:
    st.error("⚠️ Error: Secrets missing!")
    st.stop()

# --- 4. COOKIE MANAGER (Για το Free Pass) ---
# Βάζουμε key για να μην κάνει reset το component
cookie_manager = stx.CookieManager(key="free_pass_manager")

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

name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('❌ Λάθος Username ή Password')
elif authentication_status == None:
    st.info('Παρακαλώ συνδεθείτε.')

elif authentication_status == True:
    
    # --- CHECK FREE PASS (COOKIE) ---
    # Εδώ είναι το "κλειδί". Διαβάζουμε αν υπάρχει το cookie που λέει "Είμαι Verified"
    cookie_2fa = cookie_manager.get("cu_free_pass")
    
    # Είμαστε ΟΚ αν:
    # 1. Το cookie υπάρχει ΚΑΙ είναι ίσο με το username μας
    # 2. Ή αν μόλις περάσαμε το 2FA σε αυτό το session (session_state override)
    is_verified_cookie = (cookie_2fa == username)
    is_verified_session = st.session_state.get("session_verified", False)
    
    FINAL_ACCESS = is_verified_cookie or is_verified_session
    
    if not FINAL_ACCESS:
        # --- SHOW 2FA FORM ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align: center;'>🔐 2FA Security</h3>", unsafe_allow_html=True)
            st.info("Για λόγους ασφαλείας, απαιτείται επαλήθευση OTP την πρώτη φορά.")
            
            otp_code = st.text_input("6-digit Code", max_chars=6)
            
            if st.button("VERIFY & REMEMBER ME 🚀", type="primary"):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                # Δίνουμε μεγάλο παράθυρο (valid_window=4) για να μην έχεις θέμα με την ώρα
                if totp.verify(otp_code, valid_window=4):
                    
                    # 1. Ενημερώνουμε το Session State για να μπει ΑΜΕΣΩΣ (χωρίς να περιμένει το cookie)
                    st.session_state.session_verified = True
                    
                    # 2. Γράφουμε το Cookie για να μπαίνει ΜΕΛΛΟΝΤΙΚΑ (30 μέρες)
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("cu_free_pass", username, expires_at=expires)
                    
                    st.success("✅ Επιτυχία!")
                    
                    # 3. ΚΡΙΣΙΜΟ: Περιμένουμε να γραφτεί το cookie πριν το refresh
                    with st.spinner("Saving session..."):
                        time.sleep(2) 
                    
                    st.rerun()
                else:
                    st.error("❌ Λάθος κωδικός!")
            
            if st.button("Logout"):
                authenticator.logout('Logout', 'main')

    else:
        # --- MAIN APP (ΕΧΕΙΣ FREE PASS) ---
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 CU Booster")
        with c2: 
            st.write(f"👤 {name}")
            if st.button("Έξοδος"):
                # Διαγραφή του Free Pass
                cookie_manager.delete("cu_free_pass")
                st.session_state.session_verified = False
                authenticator.logout('Έξοδος', 'main')

        if 'step' not in st.session_state: st.session_state.step = 1
        if 'phone' not in st.session_state: st.session_state.phone = ""
        if 'token' not in st.session_state: st.session_state.token = None

        if st.session_state.step == 1:
            with st.container(border=True):
                phone_input = st.text_input("Κινητό (Vodafone CU)", placeholder="694...", max_chars=10)
                if st.button("SMS 📩", type="primary"):
                    if len(phone_input)==10:
                        with st.spinner("Wait..."):
                            if api_send_sms(phone_input):
                                st.session_state.phone = phone_input
                                st.session_state.step = 2
                                st.rerun()
                            else: st.error("Σφάλμα σύνδεσης")
                    else: st.warning("10 Ψηφία")

        elif st.session_state.step == 2:
            with st.container(border=True):
                st.info(f"OTP εστάλη στο: **{st.session_state.phone}**")
                otp_input = st.text_input("Κωδικός SMS")
                cc1, cc2 = st.columns(2)
                if cc1.button("Πίσω"): st.session_state.step=1; st.rerun()
                if cc2.button("Είσοδος", type="primary"):
                    with st.spinner("Checking..."):
                        token = api_verify_otp(st.session_state.phone, otp_input)
                        if token: st.session_state.token=token; st.session_state.step=3; st.rerun()
                        else: st.error("Λάθος SMS OTP")

        elif st.session_state.step == 3:
            st.success(f"Συνδέθηκε: {st.session_state.phone}")
            with st.container(border=True):
                pkg = st.radio("Πακέτο:", ["🥤 Shake (Data)", "🗣️ Voice"], horizontal=True)
                offer = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
                times = st.slider("Ποσότητα:", 1, 50, 20)
                if st.button(f"ΕΝΕΡΓΟΠΟΙΗΣΗ ({times}x) 🔥", type="primary"):
                    bar = st.progress(0); succ = 0
                    for i in range(times):
                        if api_activate(st.session_state.token, st.session_state.phone, offer) in [200, 201, 403]: succ+=1
                        bar.progress((i+1)/times)
                        time.sleep(0.05)
                    st.success(f"Επιτυχίες: {succ}/{times}")
            if st.button("Νέο Νούμερο"):
                st.session_state.step=1; st.session_state.phone=""; st.session_state.token=None; st.rerun()
