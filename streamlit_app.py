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

# --- 2. PREMIUM CSS STYLING (PRO DARK) ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Γενικό Φόντο (Midnight Gradient) */
    .stApp {
        background: radial-gradient(circle at top, #1e2028, #0e1117) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Χρώματα Κειμένου */
    h1, h2, h3, h4, p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #e6e6e6 !important;
    }
    
    /* Εξαίρεση: Κείμενο μέσα στα κουμπιά */
    button p { color: #ffffff !important; font-weight: 600 !important; }

    /* Κάρτες (Glassmorphism Effect) */
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: rgba(38, 39, 48, 0.95) !important; /* Σκούρο με ελάχιστη διαφάνεια */
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        padding: 40px !important;
        backdrop-filter: blur(10px);
    }

    /* Inputs (Κουτάκια κειμένου) */
    div[data-testid="stTextInput"] input {
        background-color: #12141a !important; /* Πολύ σκούρο */
        color: #ffffff !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        padding: 14px !important;
        font-size: 15px !important;
    }

    /* Input Focus */
    div[data-testid="stTextInput"] input:focus {
        border-color: #e60000 !important;
        box-shadow: 0 0 0 2px rgba(230, 0, 0, 0.25) !important;
    }
    
    /* Labels */
    div[data-testid="stTextInput"] label {
        color: #a0a0a0 !important;
        font-size: 13px !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Κουμπιά (Vodafone Red Gradient - Premium) */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #ff0000 0%, #b30000 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3) !important;
        transition: all 0.3s ease;
    }

    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 0, 0, 0.5) !important;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        background-color: #262730 !important;
        color: #e6e6e6 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px;
    }

    /* Απόκρυψη στοιχείων Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    
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
cookie_manager = stx.CookieManager(key="manager_pro")

# --- 5. AUTHENTICATOR SETUP ---
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

# 🔹 ΔΙΟΡΘΩΣΗ: Αλλάξαμε το όνομα της φόρμας από 'main' σε 'Secure Access'
name, authentication_status, username = authenticator.login('Secure Access', 'main')

if authentication_status == False:
    st.error('❌ Λάθος Username ή Password')
elif authentication_status == None:
    # Αντί για απλό μήνυμα, δεν δείχνουμε τίποτα (η φόρμα φαίνεται ήδη)
    pass

elif authentication_status == True:
    
    # --- CHECK FREE PASS (COOKIE) ---
    cookie_2fa = cookie_manager.get("cu_free_pass")
    
    is_verified_cookie = (cookie_2fa == username)
    is_verified_session = st.session_state.get("session_verified", False)
    
    FINAL_ACCESS = is_verified_cookie or is_verified_session
    
    if not FINAL_ACCESS:
        # --- SHOW 2FA FORM ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align: center;'>🔐 2FA Security</h3>", unsafe_allow_html=True)
            st.info("⚠️ Νέα συσκευή: Απαιτείται κωδικός επαλήθευσης.")
            
            otp_code = st.text_input("6-digit Code", max_chars=6)
            
            if st.button("VERIFY & REMEMBER DEVICE 🚀", type="primary"):
                totp = pyotp.TOTP(ADMIN_2FA_KEY)
                if totp.verify(otp_code, valid_window=4):
                    st.session_state.session_verified = True
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("cu_free_pass", username, expires_at=expires)
                    
                    st.success("✅ Επιτυχία! Είσοδος...")
                    with st.spinner("Redirecting..."):
                        time.sleep(2) 
                    st.rerun()
                else:
                    st.error("❌ Λάθος κωδικός!")
            
            # Logout Button (Safe)
            if st.button("Logout"):
                st.session_state["authentication_status"] = None
                st.session_state["name"] = None
                st.session_state["username"] = None
                try: cookie_manager.delete("cu_main_cookie", key="logout_del_main_temp")
                except: pass
                st.rerun()

    else:
        # --- MAIN APP ---
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 CU Booster")
        with c2: 
            st.write(f"👤 {name}")
            
            # Safe Logout
            if st.button("Έξοδος", type="primary"):
                try: cookie_manager.delete("cu_free_pass", key="logout_del_free")
                except: pass
                
                st.session_state.session_verified = False
                st.session_state["authentication_status"] = None
                st.session_state["name"] = None
                st.session_state["username"] = None
                
                try: cookie_manager.delete("cu_main_cookie", key="logout_del_main_final")
                except: pass
                st.rerun()

        if 'step' not in st.session_state: st.session_state.step = 1
        if 'phone' not in st.session_state: st.session_state.phone = ""
        if 'token' not in st.session_state: st.session_state.token = None

        if st.session_state.step == 1:
            with st.container(border=True):
                phone_input = st.text_input("Κινητό (Vodafone CU)", placeholder="694...", max_chars=10)
                if st.button("SMS 📩", type="primary"):
                    if len(phone_input)==10:
                        with st.spinner("Connecting..."):
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
                    with st.spinner("Verifying..."):
                        token = api_verify_otp(st.session_state.phone, otp_input)
                        if token: st.session_state.token=token; st.session_state.step=3; st.rerun()
                        else: st.error("Λάθος SMS OTP")

        elif st.session_state.step == 3:
            st.success(f"Connected: {st.session_state.phone}")
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
