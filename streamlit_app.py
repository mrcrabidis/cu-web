import streamlit as st
import requests
import base64
import urllib3
import time
import pyotp
import extra_streamlit_components as stx
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher

# --- 1. RUTHMISEIS ---
st.set_page_config(page_title="CU Booster Pro", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {background: linear-gradient(to bottom, #ffffff, #f4f7f9) !important; font-family: 'Inter', sans-serif !important;}
    h1, h2, h3, p, label, span {color: #2c3e50 !important;}
    div[data-testid="stForm"], div[data-testid="stExpander"] {
        background-color: #ffffff !important; border-radius: 24px !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.08) !important; border: none !important; padding: 40px !important;
    }
    div[data-testid="stTextInput"] input {
        background-color: #f8f9fa !important; color: #333 !important; border: 2px solid transparent !important;
        border-radius: 12px !important; padding: 14px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        background-color: #ffffff !important; border-color: #e60000 !important; box-shadow: 0 0 0 4px rgba(230, 0, 0, 0.1) !important;
    }
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #e60000 0%, #c20000 100%) !important; color: white !important;
        border: none !important; padding: 14px 24px !important; border-radius: 12px !important; width: 100%;
    }
    div[data-testid="stButton"] button:hover {transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 25px rgba(230, 0, 0, 0.4) !important;}
    div[data-testid="stButton"] button p {color: #ffffff !important;}
    div[data-testid="stAlert"] {border-radius: 12px !important; border-left: 6px solid #e60000 !important;}
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
cookie_manager = stx.CookieManager(key="2fa_tracker_debug")

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
# --- MAIN FLOW ---
# ==========================================

name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('❌ Λάθος Username ή Password')
elif authentication_status == None:
    st.info('Παρακαλώ συνδεθείτε.')

elif authentication_status == True:
    
    # --- CHECK 2FA ---
    cookie_2fa = cookie_manager.get("2fa_verified_user")
    is_verified = (cookie_2fa == username)
    
    if not is_verified:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align: center;'>🔐 2FA Verification</h3>", unsafe_allow_html=True)
            
            # --- DEBUG BLOCK (ΘΑ ΤΟ ΣΒΗΣΟΥΜΕ ΜΕΤΑ) ---
            totp = pyotp.TOTP(ADMIN_2FA_KEY)
            current_code = totp.now()
            st.warning(f"🛠️ DEBUG MODE: Ο σωστός κωδικός τώρα είναι: **{current_code}**")
            st.caption("Γράψε αυτόν τον κωδικό ακριβώς από κάτω.")
            # ----------------------------------------
            
            otp_code = st.text_input("6-digit Code", max_chars=6)
            
            col_a, col_b = st.columns(2)
            
            if col_a.button("VERIFY 🚀", type="primary"):
                # valid_window=2 -> Δέχεται κωδικούς +/- 60 δευτερόλεπτα
                if totp.verify(otp_code, valid_window=2):
                    import datetime
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("2fa_verified_user", username, expires_at=expires)
                    st.success("Correct!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ Λάθος! Εσύ έγραψες: {otp_code}, Το σύστημα θέλει: {totp.now()}")

            # ΚΟΥΜΠΙ ΑΝΑΓΚΗΣ
            if col_b.button("🆘 Skip 2FA (Emergency)"):
                st.warning("Skipping 2FA for debugging...")
                import datetime
                expires = datetime.datetime.now() + datetime.timedelta(days=30)
                cookie_manager.set("2fa_verified_user", username, expires_at=expires)
                time.sleep(0.5)
                st.rerun()
            
            if st.button("Logout"):
                authenticator.logout('Logout', 'main')

    # --- APP ---
    else:
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 CU Booster")
        with c2: 
            st.write(f"👤 {name}")
            if st.button("Έξοδος"):
                cookie_manager.delete("2fa_verified_user")
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
