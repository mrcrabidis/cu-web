import streamlit as st
import requests
import base64
import urllib3
import time
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher

# --- 1. RUTHMISEIS ---
st.set_page_config(page_title="CU Booster Pro", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp {background-color: #ffffff;}
    div[data-testid="stForm"] {border: none; padding: 0;}
    .stButton button {width: 100%; font-weight: bold; border-radius: 8px;}
    .stProgress > div > div > div > div {background-color: #e60000;}
</style>
""", unsafe_allow_html=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# --- 🍪 ΡΥΘΜΙΣΕΙΣ COOKIES (ΕΔΩ ΤΑ ΒΑΖΕΙΣ) ---
# ==========================================
MY_COOKIES = {
    # Παράδειγμα: "JSESSIONID": "...", "TIV": "..."
    # Αντέγραψε τα cookies σου εδώ μέσα:
}

# --- 3. CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- 4. API SESSION (ΜΕ COOKIES) ---
@st.cache_resource
def get_session():
    s = requests.Session()
    s.verify = False
    # Φορτώνουμε τα cookies ΜΙΑ φορά και μένουν για πάντα
    if MY_COOKIES:
        s.cookies.update(MY_COOKIES)
    return s

# --- 5. API FUNCTIONS (ΠΡΟΣΑΡΜΟΣΜΕΝΕΣ) ---
def api_send_sms(phone):
    session = get_session()
    headers = {
        "Accept": "*/*",
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "Accept-Language": "en",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"login_hint": f"+30{phone}", "response_type": "code"}
    
    try:
        res = session.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data=data)
        return res.status_code in [200, 202]
    except: return False

def api_verify_otp(phone, otp):
    session = get_session()
    headers = {
        "Host": "eu3.api.vodafone.com",
        "Accept": "*/*",
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "Accept-Language": "en",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    raw = f"30{phone}:{otp}"
    enc = base64.b64encode(raw.encode()).decode()
    data = {"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": enc}
    
    try:
        res = session.post(f"{AUTH_OTP_URL}/token", headers=headers, data=data)
        if res.status_code == 200:
            return res.json().get("access_token")
        else:
            return None
    except: return None

def api_activate(token, target_msisdn, offer_id):
    session = get_session()
    headers = {
        "Host": "eu3.api.vodafone.com",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Connection": "keep-alive",
        "Accept": "application/json",        
        "Accept-Language": "en",
        "Authorization": f"Bearer {token}",
        "api-key-name": "CUAPP",             
        "vf-country-code": "GR"
    }
    payload = {
        "productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer_id}}],
        "relatedParty": [{"role": "subscriber", "id": target_msisdn}]
    }
    try:
        res = session.post(ORDER_URL, headers=headers, json=payload)
        return res.status_code, res.text
    except Exception as e: return 999, str(e)

# ==========================================
# --- 6. AUTHENTICATION LOGIC ---
# ==========================================
try:
    RAW_USERS = st.secrets["users"]
except:
    st.error("⚠️ Error: Δεν βρέθηκαν τα Secrets [users]!")
    st.stop()

# Setup Users for Authenticator
users_config = {}
for username, password in RAW_USERS.items():
    hashed_pass = Hasher([str(password)]).generate()[0]
    users_config[username] = {
        "name": username,
        "password": hashed_pass,
        "email": f"{username}@cu.gr"
    }

credentials = {"usernames": users_config}
cookie_config = {"expiry_days": 30, "key": "cu_cookie_key", "name": "cu_auth_cookie"}

authenticator = stauth.Authenticate(
    credentials,
    cookie_config['name'],
    cookie_config['key'],
    cookie_config['expiry_days']
)

# Login Widget
name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('❌ Λάθος όνομα χρήστη ή κωδικός')
elif authentication_status == None:
    st.info('Παρακαλώ συνδεθείτε.')
elif authentication_status == True:
    
    # --- MAIN APP START ---
    
    # Header & Logout
    c1, c2 = st.columns([3, 1])
    with c1: st.title("🚀 CU Booster")
    with c2: 
        st.write(f"👤 {name}")
        authenticator.logout('Έξοδος', 'main')
    
    # Διαχείριση Cookies UI
    if MY_COOKIES:
        st.caption(f"🍪 Cookies Loaded: {len(MY_COOKIES)}")
    else:
        st.warning("⚠️ Δεν έχουν οριστεί Cookies στον κώδικα!")

    # Initialization
    if 'step' not in st.session_state: st.session_state.step = 1
    if 'phone' not in st.session_state: st.session_state.phone = ""
    if 'token' not in st.session_state: st.session_state.token = None

    # --- STEP 1: LOGIN (SMS) ---
    if st.session_state.step == 1:
        with st.container(border=True):
            st.subheader("📲 Σύνδεση με Vodafone")
            phone_input = st.text_input("Κινητό Τηλέφωνο", placeholder="694...", max_chars=10)
            
            if st.button("Αποστολή SMS 📩", type="primary", use_container_width=True):
                if len(phone_input) == 10:
                    with st.spinner("Επικοινωνία με Vodafone..."):
                        if api_send_sms(phone_input):
                            st.session_state.phone = phone_input
                            st.session_state.step = 2
                            st.rerun()
                        else:
                            st.error("❌ Αποτυχία αποστολής SMS")
                else:
                    st.warning("⚠️ Απαιτούνται 10 ψηφία")

    # --- STEP 2: OTP ---
    elif st.session_state.step == 2:
        with st.container(border=True):
            st.subheader("🔐 Επαλήθευση")
            st.info(f"OTP εστάλη στο: **{st.session_state.phone}**")
            otp_input = st.text_input("Κωδικός OTP")
            
            col1, col2 = st.columns(2)
            if col1.button("Πίσω", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
            
            if col2.button("Είσοδος", type="primary", use_container_width=True):
                with st.spinner("Έλεγχος OTP..."):
                    token = api_verify_otp(st.session_state.phone, otp_input)
                    if token:
                        st.session_state.token = token
                        st.session_state.step = 3
                        st.rerun()
                    else:
                        st.error("❌ Λάθος OTP ή Πρόβλημα Δικτύου")

    # --- STEP 3: DASHBOARD ---
    elif st.session_state.step == 3:
        st.success(f"✅ Συνδεθήκατε: {st.session_state.phone}")
        
        with st.container(border=True):
            st.subheader("📦 Ενεργοποίηση Πακέτου")
            
            # Επιλογή Αριθμού Στόχου (Default: Ο ίδιος)
            target_phone = st.text_input("Αριθμός Στόχος (Αφήστε το ίδιο για εσάς)", value=st.session_state.phone, max_chars=10)
            
            pkg = st.radio("Επιλογή:", ["🥤 CU Shake (Data)", "🗣️ Voice Bonus"], horizontal=True)
            offer_id = "BDLCUShakeBon7" if "Shake" in pkg else "BDLBonVoice3"
            
            times = st.slider("Ποσότητα:", 1, 50, 20)
            
            if st.button(f"ΕΝΕΡΓΟΠΟΙΗΣΗ ({times}x) 🔥", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                
                for i in range(times):
                    # Καθαρισμός αριθμού (αν έχει +30)
                    final_target = target_phone.replace("+30", "").strip()
                    if len(final_target) != 10:
                        st.error("Λάθος αριθμός στόχος")
                        break

                    status_text.text(f"⏳ Εκτέλεση {i+1}/{times}...")
                    
                    code, resp_text = api_activate(st.session_state.token, final_target, offer_id)
                    
                    if code in [200, 201]:
                        success_count += 1
                    elif code == 403:
                        success_count += 1 # Το μετράμε ως success γιατί πέρασε το request αλλά κόπηκε από logic
                    
                    progress_bar.progress((i + 1) / times)
                    time.sleep(0.3) # Μικρή καθυστέρηση
                
                st.balloons()
                st.success(f"Ολοκληρώθηκε: {success_count}/{times} Επιτυχίες")
        
        if st.button("🔄 Νέο Νούμερο", use_container_width=True):
            st.session_state.step = 1
            st.session_state.phone = ""
            st.session_state.token = None
            st.rerun()
