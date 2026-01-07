import streamlit as st
import requests
import base64
import urllib3
import time
import pyotp
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher

# --- 1. RUTHMISEIS ---
st.set_page_config(page_title="CU Booster Pro", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS STYLING (DARK TEXT FIX) ---
st.markdown("""
<style>
    /* 1. Ρύθμιση Φόντου σε όλη την εφαρμογή */
    .stApp {
        background-color: #f0f2f6 !important;
    }

    /* 2. ΑΝΑΓΚΑΣΤΙΚΗ ΑΛΛΑΓΗ ΧΡΩΜΑΤΟΣ ΚΕΙΜΕΝΟΥ ΣΕ ΜΑΥΡΟ */
    /* Αυτό διορθώνει το πρόβλημα που δεν διαβάζονται οι τίτλοι */
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #0d0d0d !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 3. Κάρτα Login & Περιεχομένου */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #ffffff !important; /* Καθαρό λευκό */
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #dcdcdc;
    }

    /* 4. Διόρθωση των Inputs (Κουτάκια που γράφεις) */
    /* Να είναι λευκά/γκρι με μαύρα γράμματα */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 10px;
    }
    /* Το Label πάνω από το input (π.χ. "Username") */
    div[data-testid="stTextInput"] label {
        color: #333333 !important;
        font-weight: bold;
    }

    /* 5. Κουμπιά (Vodafone Red Style) */
    div[data-testid="stButton"] button {
        background-color: #e60000 !important;
        color: #ffffff !important;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        border-radius: 8px;
        width: 100%;
        font-size: 16px;
        transition: 0.3s;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #b30000 !important;
        color: #ffffff !important;
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    /* Κειμενάκι μέσα στο κουμπί να είναι σίγουρα άσπρο */
    div[data-testid="stButton"] button p {
        color: #ffffff !important;
    }

    /* 6. Απόκρυψη περιττών στοιχείων */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;}
    
    /* 7. Διόρθωση Alert/Info Boxes */
    div[data-testid="stAlert"] {
        background-color: #ebf5ff;
        color: #004085;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SECRETS & SETUP ---
try:
    # Εδώ διαβάζουμε το κλειδί που μου έδωσες
    ADMIN_2FA_KEY = st.secrets["security"]["admin_2fa_key"]
    RAW_USERS = st.secrets["users"]
except:
    st.error("⚠️ Error: Secrets missing! Check .streamlit/secrets.toml")
    st.stop()

# --- 4. AUTHENTICATOR SETUP ---
# Μετατροπή χρηστών για το σύστημα Login
users_config = {}
for username, password in RAW_USERS.items():
    # Χρησιμοποιούμε str() για να μην μπερδευτεί αν ο κωδικός είναι αριθμός
    hashed_pass = Hasher([str(password)]).generate()[0]
    users_config[username] = {
        "name": username,
        "password": hashed_pass,
        "email": f"{username}@cu.gr"
    }

credentials = {"usernames": users_config}
cookie_config = {"expiry_days": 30, "key": "cu_boost_key_final", "name": "cu_boost_cookie"}

authenticator = stauth.Authenticate(
    credentials,
    cookie_config['name'],
    cookie_config['key'],
    cookie_config['expiry_days']
)

# --- 5. API FUNCTIONS ---
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
# --- MAIN FLOW ---
# ==========================================

# 1. Βήμα Α: Username / Password (μέσω Authenticator)
name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('❌ Λάθος Username ή Password')
elif authentication_status == None:
    st.info('Παρακαλώ συνδεθείτε για να συνεχίσετε.')

elif authentication_status == True:
    # 2. Βήμα Β: 2FA CHECK (Το κλειδί από τα Secrets)
    
    # Initialization του 2FA state
    if "is_2fa_verified" not in st.session_state:
        st.session_state.is_2fa_verified = False
    
    # Αν δεν έχει περάσει το 2FA, δείξε το πεδίο
    if not st.session_state.is_2fa_verified:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align: center;'>🔐 2FA Verification</h3>", unsafe_allow_html=True)
            st.caption(f"Γειά σου **{name}**. Απαιτείται κωδικός Authenticator.")
            
            otp_code = st.text_input("6-digit Code", max_chars=6, key="otp_input_field")
            
            if st.button("VERIFY 🚀", type="primary"):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                # valid_window=1: Συγχωρεί +/- 30 δευτερόλεπτα διαφορά ώρας
                if totp.verify(otp_code, valid_window=1):
                    st.session_state.is_2fa_verified = True
                    st.rerun()
                else:
                    st.error("❌ Λάθος κωδικός! Ελέγξτε το Authenticator app.")
            
            # Κουμπί εξόδου αν κολλήσει
            if st.button("Logout"):
                authenticator.logout('Logout', 'main')
    
    # 3. Βήμα Γ: Η ΕΦΑΡΜΟΓΗ (Μόνο αν πέρασε ΚΑΙ τα δύο)
    else:
        # Header & Logout
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 CU Booster")
        with c2: 
            st.write(f"👤 {name}")
            # Κουμπί Logout που καθαρίζει και το 2FA
            if st.button("Έξοδος"):
                st.session_state.is_2fa_verified = False
                authenticator.logout('Έξοδος', 'main')

        # --- APP STATES ---
        if 'step' not in st.session_state: st.session_state.step = 1
        if 'phone' not in st.session_state: st.session_state.phone = ""
        if 'token' not in st.session_state: st.session_state.token = None

        # --- STEP 1 ---
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

        # --- STEP 2 ---
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

        # --- STEP 3 ---
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
