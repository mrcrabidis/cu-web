import streamlit as st
import requests
import base64
import time
import urllib3
import pyotp  # Βιβλιοθήκη για Google Authenticator (TOTP)

# Απενεργοποίηση warnings για SSL (λόγω verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- ΡΥΘΜΙΣΕΙΣ ΧΡΗΣΤΗ ΕΦΑΡΜΟΓΗΣ (CREDENTIALS) ---
# Σε πραγματική εφαρμογή, αυτά θα ήταν σε βάση δεδομένων ή environment variables.
# Για το παράδειγμα, τα ορίζουμε εδώ:
APP_USERNAME = "admin"
APP_PASSWORD = "password123"
# Το Secret Key για το Google Authenticator (Base32 format).
# Μπορείς να δημιουργήσεις ένα νέο secret τρέχοντας: pyotp.random_base32()
APP_2FA_SECRET = "JBSWY3DPEHPK3PXP" 

# --- ΡΥΘΜΙΣΕΙΣ API VODAFONE ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΛΟΓΙΚΗΣ ---

def verify_app_login(username, password, otp_code):
    """Ελέγχει τα credentials και το 2FA για είσοδο στο App."""
    if username == APP_USERNAME and password == APP_PASSWORD:
        totp = pyotp.TOTP(APP_2FA_SECRET)
        if totp.verify(otp_code):
            return True
    return False

def send_vodafone_sms(phone):
    """Στέλνει το SMS για login στο Vodafone CU."""
    headers = {
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"login_hint": f"+30{phone}", "response_type": "code"}
    
    try:
        res = requests.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data=data, verify=False)
        return res.status_code in [200, 202]
    except Exception as e:
        st.error(f"Network Error: {e}")
        return False

def verify_vodafone_otp(phone, otp):
    """Κάνει verify το OTP της Vodafone και επιστρέφει το Token."""
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
        res = requests.post(f"{AUTH_OTP_URL}/token", headers=headers, data=data, verify=False)
        if res.status_code == 200:
            return res.json().get("access_token")
        return None
    except Exception:
        return None

def activate_package(token, target_msisdn, offering_id):
    """Ενεργοποιεί το πακέτο."""
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
        response = requests.post(ORDER_URL, headers=headers, json=payload, verify=False)
        return response.status_code
    except Exception as e:
        return str(e)

# --- STREAMLIT UI ---

st.set_page_config(page_title="CU Bot Panel", page_icon="🔴", layout="centered")

# Διαχείριση Session State
if 'app_logged_in' not in st.session_state:
    st.session_state['app_logged_in'] = False
if 'vf_token' not in st.session_state:
    st.session_state['vf_token'] = None
if 'vf_phone' not in st.session_state:
    st.session_state['vf_phone'] = None
if 'sms_sent' not in st.session_state:
    st.session_state['sms_sent'] = False

# --- ΦΑΣΗ 1: LOGIN ΣΤΗΝ ΕΦΑΡΜΟΓΗ ---
if not st.session_state['app_logged_in']:
    st.title("🔐 Secure Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        otp_code = st.text_input("Google Authenticator Code", max_chars=6)
        
        submit = st.form_submit_button("Είσοδος")
        
        if submit:
            if verify_app_login(username, password, otp_code):
                st.session_state['app_logged_in'] = True
                st.success("Επιτυχής σύνδεση!")
                st.rerun()
            else:
                st.error("Λάθος στοιχεία ή κωδικός 2FA.")
    
    # Βοηθητικό για να σετάρεις το Google Auth πρώτη φορά (σβήσε το σε production)
    with st.expander("Setup Google Auth (Demo info)"):
        st.write(f"Secret Key: `{APP_2FA_SECRET}`")
        st.write("Σκάναρε αυτό στο Google Authenticator app ή βάλε το κλειδί χειροκίνητα.")
        st.write(f"Demo User: `{APP_USERNAME}` / Pass: `{APP_PASSWORD}`")

# --- ΦΑΣΗ 2: ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ ---
else:
    st.sidebar.title("Μενού")
    if st.sidebar.button("🚪 Έξοδος (Logout)"):
        st.session_state.clear()
        st.rerun()

    st.title("🔴 CU Vodafone Bot Control")

    # --- ΥΠΟ-ΦΑΣΗ 2Α: ΣΥΝΔΕΣΗ ΜΕ VODAFONE ---
    if not st.session_state['vf_token']:
        st.header("1. Σύνδεση στο CU")
        
        col1, col2 = st.columns(2)
        with col1:
            phone_input = st.text_input("Αριθμός Κινητού (χωρίς +30)", value=st.session_state.get('vf_phone', '') or '')
        
        if st.button("📨 Αποστολή SMS") and phone_input:
            with st.spinner("Αποστολή..."):
                if send_vodafone_sms(phone_input):
                    st.session_state['sms_sent'] = True
                    st.session_state['vf_phone'] = phone_input
                    st.success(f"Το SMS στάλθηκε στο {phone_input}")
                else:
                    st.error("Αποτυχία αποστολής SMS.")

        if st.session_state['sms_sent']:
            otp_input = st.text_input("Κωδικός OTP (από SMS)")
            if st.button("✅ Επαλήθευση OTP"):
                with st.spinner("Έλεγχος..."):
                    token = verify_vodafone_otp(st.session_state['vf_phone'], otp_input)
                    if token:
                        st.session_state['vf_token'] = token
                        st.success("Συνδέθηκες επιτυχώς!")
                        st.rerun()
                    else:
                        st.error("Λάθος OTP ή σφάλμα σύνδεσης.")

    # --- ΥΠΟ-ΦΑΣΗ 2Β: CONTROL PANEL ---
    else:
        st.success(f"Συνδεδεμένος ως: {st.session_state['vf_phone']}")
        
        st.divider()
        st.header("🚀 Ενέργειες")
        
        # Επιλογή Στόχου
        target_phone = st.text_input("Στόχος (Target MSISDN)", value=st.session_state['vf_phone'])
        
        # Επιλογή Πακέτου
        pkg_choice = st.selectbox("Επίλεξε Πακέτο", [
            "🥤 CU Shake (BDLCUShakeBon7)",
            "📞 Voice Bonus (BDLBonVoice3)"
        ])
        
        if "Shake" in pkg_choice:
            offering_id = "BDLCUShakeBon7"
        else:
            offering_id = "BDLBonVoice3"
            
        # Επιλογή Επαναλήψεων
        loops = st.number_input("Πλήθος Επαναλήψεων", min_value=1, max_value=100, value=1)
        
        if st.button("🔥 ΕΝΑΡΞΗ"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            fail_count = 0
            limit_count = 0
            
            results_area = st.container()
            
            for i in range(loops):
                status_text.text(f"Εκτέλεση {i+1}/{loops}...")
                code = activate_package(st.session_state['vf_token'], target_phone, offering_id)
                
                if code in [200, 201]:
                    success_count += 1
                elif code == 403:
                    limit_count += 1
                else:
                    fail_count += 1
                
                # Update progress
                progress_bar.progress((i + 1) / loops)
                time.sleep(0.2) # Μικρή καθυστέρηση για να μην φάμε ban ακαριαία
            
            status_text.text("Ολοκληρώθηκε!")
            
            # Εμφάνιση αποτελεσμάτων
            with results_area:
                c1, c2, c3 = st.columns(3)
                c1.metric("Επιτυχίες", success_count)
                c2.metric("Limits (403)", limit_count)
                c3.metric("Σφάλματα", fail_count)
            
            if success_count > 0:
                st.balloons()
