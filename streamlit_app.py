import streamlit as st
import requests
import base64
import time
import urllib3

# Απενεργοποίηση warnings για SSL (λόγω verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- ΡΥΘΜΙΣΕΙΣ & CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- ΣΥΝΑΡΤΗΣΕΙΣ ---

def get_session():
    s = requests.Session()
    s.verify = False
    return s

def request_otp(phone):
    """Ζητάει OTP από τη Vodafone"""
    s = get_session()
    headers = {
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"login_hint": f"+30{phone}", "response_type": "code"}
    
    try:
        res = s.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data=data)
        return res.status_code in [200, 202]
    except Exception as e:
        st.error(f"Network Error: {e}")
        return False

def verify_otp(phone, otp):
    """Κάνει επαλήθευση OTP και επιστρέφει το Token"""
    s = get_session()
    headers = {
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*"
    }
    
    raw_auth = f"30{phone}:{otp}"
    encoded_auth = base64.b64encode(raw_auth.encode()).decode()
    data = {"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": encoded_auth}
    
    try:
        res = s.post(f"{AUTH_OTP_URL}/token", headers=headers, data=data)
        if res.status_code == 200:
            return res.json().get("access_token")
        return None
    except:
        return None

def activate_package(token, target_msisdn, offering_id):
    """Ενεργοποιεί το πακέτο"""
    s = get_session()
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
        "productOrderItem": [{
            "action": "adhoc", 
            "quantity": 1, 
            "productOffering": {"id": offering_id}
        }],
        "relatedParty": [{"role": "subscriber", "id": target_msisdn}]
    }
    
    try:
        response = s.post(ORDER_URL, headers=headers, json=payload)
        return response.status_code
    except Exception:
        return 0

# --- UI SETUP ---
st.set_page_config(page_title="CU Bot Mobile", page_icon="📱", layout="centered")

# CSS για να μοιάζει πιο 'App' στο κινητό
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; }
    .stTextInput>div>div>input { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("📱 CU Controller")

# --- SESSION STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = 'login_phone' # login_phone, login_otp, dashboard
if 'phone' not in st.session_state:
    st.session_state.phone = ""
if 'token' not in st.session_state:
    st.session_state.token = None

# --- LOGIC FLOW ---

# 1. Βήμα: Εισαγωγή Κινητού
if st.session_state.step == 'login_phone':
    st.subheader("Σύνδεση")
    phone_input = st.text_input("Αριθμός Κινητού (χωρίς +30)", value=st.session_state.phone)
    
    if st.button("Αποστολή SMS"):
        if len(phone_input) == 10:
            with st.spinner("Αποστολή..."):
                if request_otp(phone_input):
                    st.session_state.phone = phone_input
                    st.session_state.step = 'login_otp'
                    st.rerun()
                else:
                    st.error("Αποτυχία αποστολής SMS.")
        else:
            st.warning("Παρακαλώ εισάγετε σωστό 10ψήφιο αριθμό.")

# 2. Βήμα: Εισαγωγή OTP
elif st.session_state.step == 'login_otp':
    st.subheader(f"Επαλήθευση: {st.session_state.phone}")
    otp_input = st.text_input("Κωδικός OTP", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Πίσω"):
            st.session_state.step = 'login_phone'
            st.rerun()
    with col2:
        if st.button("Είσοδος", type="primary"):
            with st.spinner("Έλεγχος OTP..."):
                token = verify_otp(st.session_state.phone, otp_input)
                if token:
                    st.session_state.token = token
                    st.session_state.step = 'dashboard'
                    st.success("Επιτυχία!")
                    st.rerun()
                else:
                    st.error("Λάθος κωδικός OTP.")

# 3. Βήμα: Dashboard (Ενέργειες)
elif st.session_state.step == 'dashboard':
    st.success(f"Συνδεδεμένος: {st.session_state.phone}")
    
    # Επιλογή Στόχου (Target)
    target = st.text_input("Στόχος (Target Number)", value=st.session_state.phone)
    
    st.divider()
    
    # Επιλογές Πακέτου
    option = st.selectbox("Επίλεξε Πακέτο", 
                          ["CU Shake (BDLCUShakeBon7)", "Voice Bonus (BDLBonVoice3)"])
    
    offering_id = "BDLCUShakeBon7" if "Shake" in option else "BDLBonVoice3"
    
    count = st.slider("Πλήθος επαναλήψεων", min_value=1, max_value=50, value=1)
    
    if st.button("🚀 ΕΚΤΕΛΕΣΗ"):
        # Καθαρισμός αριθμού
        clean_target = target.replace(" ", "").replace("+30", "")[-10:]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success = 0
        fails = 0
        limits = 0
        
        for i in range(count):
            # Update UI
            status_text.text(f"Εκτέλεση {i+1}/{count}...")
            progress_bar.progress((i + 1) / count)
            
            # API Call
            code = activate_package(st.session_state.token, clean_target, offering_id)
            
            if code in [200, 201]:
                success += 1
            elif code == 403:
                limits += 1
            else:
                fails += 1
            
            time.sleep(0.2) # Μικρή καθυστέρηση για να μην φάμε ban
            
        st.balloons()
        st.info(f"📊 Αποτελέσματα: ✅ {success} | ⛔ {limits} | ❌ {fails}")

    st.divider()
    if st.button("Αποσύνδεση"):
        st.session_state.clear()
        st.rerun()
