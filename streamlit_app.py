import streamlit as st
import requests
import base64
import time
import urllib3
import pyotp

# Απενεργοποίηση warnings για SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- ΡΥΘΜΙΣΕΙΣ API VODAFONE ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
# User Agent που μιμείται την εφαρμογή iPhone
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- UI CONFIG ---
st.set_page_config(page_title="CU Bot Panel", page_icon="🔴", layout="centered")

# --- INITIALIZATION (SESSION STATE) ---
if 'login_step' not in st.session_state:
    st.session_state['login_step'] = 1  # 1: User/Pass, 2: OTP, 3: Logged In
if 'vf_token' not in st.session_state:
    st.session_state['vf_token'] = None
if 'vf_phone' not in st.session_state:
    st.session_state['vf_phone'] = None
if 'sms_sent' not in st.session_state:
    st.session_state['sms_sent'] = False

# --- ΣΥΝΑΡΤΗΣΕΙΣ ---

def check_credentials(username, password):
    """Ελέγχει αν το username/password ταιριάζουν με τα secrets."""
    try:
        sec_user = st.secrets["auth"]["username"]
        sec_pass = st.secrets["auth"]["password"]
        return username == sec_user and password == sec_pass
    except Exception:
        st.error("❌ Λείπει το αρχείο secrets στο Streamlit Cloud ή τοπικά!")
        return False

def check_otp(otp_code):
    """Ελέγχει το OTP με βάση το secret key."""
    try:
        sec_key = st.secrets["auth"]["totp_secret"]
        totp = pyotp.TOTP(sec_key)
        return totp.verify(otp_code)
    except Exception:
        st.error("❌ Πρόβλημα με το secret key στα secrets.")
        return False

def send_vodafone_sms(phone):
    headers = {
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"login_hint": f"+30{phone}", "response_type": "code"}
    try:
        res = requests.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data=data, verify=False, timeout=10)
        return res.status_code in [200, 202]
    except Exception as e:
        st.error(f"SMS Error: {e}")
        return False

def verify_vodafone_otp(phone, otp):
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
        res = requests.post(f"{AUTH_OTP_URL}/token", headers=headers, data=data, verify=False, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token")
        return None
    except Exception:
        return None

def activate_package(token, target_msisdn, offering_id):
    """
    Ενεργοποιεί πακέτο.
    Επιστρέφει: (status_code, response_text) για debugging.
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {token}",
        "api-key-name": "CUAPP",             
        "vf-country-code": "GR",
        # Προσθήκη έξτρα headers μήπως ξεγελάσουμε το firewall
        "Origin": "https://www.vodafonecu.gr",
        "Referer": "https://www.vodafonecu.gr/"
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
        response = requests.post(ORDER_URL, headers=headers, json=payload, verify=False, timeout=15)
        return response.status_code, response.text
    except Exception as e:
        return 0, str(e)

# --- LOGIN FLOW ---

if st.session_state['login_step'] < 3:
    st.title("🔐 Secure Login")
    
    # Βήμα 1: Username & Password
    if st.session_state['login_step'] == 1:
        with st.form("cred_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_creds = st.form_submit_button("Επόμενο")
            
            if submit_creds:
                if check_credentials(username, password):
                    st.session_state['login_step'] = 2
                    st.rerun()
                else:
                    st.error("Λάθος Username ή Password.")

    # Βήμα 2: Google Authenticator OTP
    elif st.session_state['login_step'] == 2:
        st.info("✅ Τα στοιχεία είναι σωστά. Εισάγετε τον κωδικό 2FA.")
        with st.form("otp_form"):
            otp_code = st.text_input("Google Authenticator Code", max_chars=6)
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_otp = st.form_submit_button("Είσοδος")
            with col2:
                back_btn = st.form_submit_button("🔙 Πίσω")

            if back_btn:
                st.session_state['login_step'] = 1
                st.rerun()
            
            if submit_otp:
                if check_otp(otp_code):
                    st.session_state['login_step'] = 3
                    st.success("Επιτυχία!")
                    st.rerun()
                else:
                    st.error("Λάθος κωδικός OTP.")

# --- ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ (Μόνο αν Login Step == 3) ---
else:
    with st.sidebar:
        st.title("Μενού")
        if st.button("🚪 Έξοδος (Logout)"):
            st.session_state.clear()
            st.rerun()

    st.title("🔴 CU Vodafone Bot Control")

    # --- Vodafone Login Logic ---
    if not st.session_state['vf_token']:
        st.subheader("Σύνδεση στο CU")
        
        col1, col2 = st.columns(2)
        with col1:
            phone_input = st.text_input("Αριθμός Κινητού (χωρίς +30)", value=st.session_state.get('vf_phone', '') or '')
        
        if st.button("📨 Αποστολή SMS") and phone_input:
            with st.spinner("Αποστολή..."):
                if send_vodafone_sms(phone_input):
                    st.session_state['sms_sent'] = True
                    st.session_state['vf_phone'] = phone_input
                    st.success(f"SMS στο {phone_input}")
                else:
                    st.error("Error sending SMS. Δες τα logs.")

        if st.session_state['sms_sent']:
            otp_input = st.text_input("Κωδικός OTP (από SMS)")
            if st.button("✅ Επαλήθευση"):
                with st.spinner("Έλεγχος..."):
                    token = verify_vodafone_otp(st.session_state['vf_phone'], otp_input)
                    if token:
                        st.session_state['vf_token'] = token
                        st.rerun()
                    else:
                        st.error("Login Failed. Λάθος OTP ή Timeout.")

    # --- Tool Control Panel ---
    else:
        st.success(f"User: {st.session_state['vf_phone']}")
        st.divider()
        
        target_phone = st.text_input("Στόχος (Target MSISDN)", value=st.session_state['vf_phone'])
        
        pkg_choice = st.selectbox("Πακέτο", [
            "🥤 CU Shake (BDLCUShakeBon7)",
            "📞 Voice Bonus (BDLBonVoice3)"
        ])
        offering_id = "BDLCUShakeBon7" if "Shake" in pkg_choice else "BDLBonVoice3"
            
        loops = st.number_input("Επαναλήψεις", min_value=1, max_value=100, value=1)
        
        if st.button("🔥 ΕΝΑΡΞΗ"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Debug Log Area - Εδώ θα δούμε τι φταίει
            st.subheader("📜 Debug Logs")
            log_area = st.container()
            
            success_count = 0
            fail_count = 0
            limit_count = 0
            
            for i in range(loops):
                status_text.text(f"Ενέργεια {i+1}/{loops}...")
                
                # Κλήση της συνάρτησης που επιστρέφει ΚΑΙ το μήνυμα σφάλματος
                code, msg = activate_package(st.session_state['vf_token'], target_phone, offering_id)
                
                if code in [200, 201]:
                    success_count += 1
                    with log_area:
                        st.success(f"Hit #{i+1}: Success")
                elif code == 403:
                    limit_count += 1
                    with log_area:
                        st.warning(f"Hit #{i+1}: Limit Reached (403)")
                else:
                    fail_count += 1
                    with log_area:
                        # Εμφανίζει τον κωδικό και το μήνυμα από τη Vodafone
                        st.error(f"Hit #{i+1}: Failed ({code}) -> {msg}")
                
                progress_bar.progress((i + 1) / loops)
                time.sleep(0.5)
            
            status_text.text("Τέλος!")
            
            st.write("---")
            col1, col2, col3 = st.columns(3)
            col1.metric("✅ Επιτυχίες", success_count)
            col2.metric("⚠️ Limits", limit_count)
            col3.metric("❌ Σφάλματα", fail_count)
