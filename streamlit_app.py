import streamlit as st
import requests
import base64
import time
import urllib3

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU Boost Portal",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- CUSTOM CSS (MINIMALISTIC & PROFESSIONAL) ---
st.markdown("""
<style>
    /* Γενικό Στυλ & Φόντο */
    .stApp {
        background: linear-gradient(180deg, #121212 0%, #1E1E1E 100%);
        color: #E0E0E0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Εξαφάνιση των Streamlit στοιχείων */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Κύριος Τίτλος */
    .main-title {
        text-align: center;
        font-size: 2.2em;
        font-weight: 600;
        margin-bottom: 30px;
        color: #FFFFFF;
        letter-spacing: 1px;
    }

    /* Κάρτες (Minimal) */
    .css-card {
        background-color: #1E1E1E;
        border-radius: 12px;
        border: 1px solid #333333;
        padding: 40px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Subheaders */
    .css-card h3 {
        font-weight: 500;
        color: #FFFFFF;
        margin-bottom: 15px;
    }
    .css-card p {
        color: #AAAAAA;
        font-size: 15px;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #2C2C2C;
        color: #E0E0E0;
        border-radius: 8px;
        height: 45px;
        font-size: 16px;
        border: 1px solid #444444;
        padding: 0 15px;
        transition: border-color 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E60000;
        box-shadow: none;
        background-color: #333333;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-weight: 500;
        font-size: 16px;
        transition: all 0.2s ease;
        box-shadow: none;
        text-transform: none;
        border: 1px solid transparent;
    }

    /* Primary Button (Vodafone Red, Minimal) */
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="primary"] {
        background-color: #E60000;
        color: #FFFFFF;
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="primary"]:hover {
        background-color: #C40000;
        border-color: #C40000;
    }

    /* Secondary Button (Outline) */
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="secondary"] {
        background-color: transparent;
        border: 1px solid #555555;
        color: #E0E0E0;
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="secondary"]:hover {
        border-color: #E60000;
        color: #E60000;
    }

    /* Metrics & Status */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
        color: #FFFFFF;
    }
    .stStatus {
        background: #2C2C2C !important;
        border-radius: 10px !important;
        border: 1px solid #444444 !important;
    }
    .stStatus p {
        color: #E0E0E0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIC FUNCTIONS (ΙΔΙΕΣ ΜΕ ΠΡΙΝ) ---
def get_session():
    s = requests.Session()
    s.verify = False
    return s

def request_otp(phone):
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
    except:
        return False

def verify_otp(phone, otp):
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
    s = get_session()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {token}",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR"
    }
    payload = {
        "productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offering_id}}],
        "relatedParty": [{"role": "subscriber", "id": target_msisdn}]
    }
    try:
        response = s.post(ORDER_URL, headers=headers, json=payload)
        return response.status_code
    except:
        return 0

# --- APP FLOW ---

if 'step' not in st.session_state: st.session_state.step = 'login_phone'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# Header Logo area
st.markdown("<h1 class='main-title'>CU Boost Portal</h1>", unsafe_allow_html=True)

# 1. LOGIN SCREEN
if st.session_state.step == 'login_phone':
    # Κεντράρισμα της κάρτας
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("Welcome Back")
        st.write("Please sign in to continue.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        phone_input = st.text_input("Mobile Number", placeholder="", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Send SMS Code", type="primary"):
            if len(phone_input) == 10:
                with st.spinner("Connecting..."):
                    if request_otp(phone_input):
                        st.session_state.phone = phone_input
                        st.session_state.step = 'login_otp'
                        st.rerun()
                    else:
                        st.toast("Failed to send SMS", icon="⚠️")
            else:
                st.toast("Please enter a valid 10-digit number.", icon="ℹ️")
        st.markdown("</div>", unsafe_allow_html=True)

# 2. OTP SCREEN
elif st.session_state.step == 'login_otp':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("Verification")
        st.write(f"Enter the code sent to **{st.session_state.phone}**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        otp_input = st.text_input("OTP Code", type="password", placeholder="", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1.5])
        with c1:
            if st.button("Back", kind="secondary"):
                st.session_state.step = 'login_phone'
                st.rerun()
        with c2:
            if st.button("Sign In", type="primary"):
                with st.spinner("Verifying..."):
                    token = verify_otp(st.session_state.phone, otp_input)
                    if token:
                        st.session_state.token = token
                        st.session_state.step = 'dashboard'
                        st.rerun()
                    else:
                        st.toast("Invalid OTP Code", icon="⛔")
        st.markdown("</div>", unsafe_allow_html=True)

# 3. DASHBOARD
elif st.session_state.step == 'dashboard':
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        # User Info Card
        st.markdown(f"""
        <div class='css-card' style='padding: 25px; text-align: left; display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <span style='font-size: 13px; color: #AAAAAA; letter-spacing: 0.5px;'>ACCOUNT</span><br>
                <span style='font-size: 20px; font-weight: 600; color: #FFFFFF;'>{st.session_state.phone}</span>
            </div>
            <div style='font-size: 24px; color: #E60000;'>●</div>
        </div>
        """, unsafe_allow_html=True)

        # Control Card
        st.markdown("<div class='css-card' style='text-align: left;'>", unsafe_allow_html=True)
        st.subheader("Boost Controls")
        st.markdown("<br>", unsafe_allow_html=True)

        st.write("**Target Number**")
        target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed", placeholder="Enter Target Number")
        
        st.markdown("<br>", unsafe_allow_html=True)

        st.write("**Select Package**")
        option = st.selectbox("Offer", 
                              ["CU Shake (BDLCUShakeBon7)", "Voice Bonus (BDLBonVoice3)"],
                              label_visibility="collapsed")
        
        offering_id = "BDLCUShakeBon7" if "Shake" in option else "BDLBonVoice3"
        
        st.markdown("<br>", unsafe_allow_html=True)

        st.write("**Quantity**")
        count = st.slider("Quantity", 1, 50, 1, label_visibility="collapsed")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("Activate Now", type="primary"):
            clean_target = target.replace(" ", "").replace("+30", "")[-10:]
            
            # Modern Status Container
            with st.status("Processing...", expanded=True) as status:
                success, limits, fails = 0, 0, 0
                
                my_bar = st.progress(0)
                
                for i in range(count):
                    resp_code = activate_package(st.session_state.token, clean_target, offering_id)
                    
                    if resp_code in [200, 201]:
                        success += 1
                        status.write(f"Hit {i+1}: Success")
                    elif resp_code == 403:
                        limits += 1
                        status.write(f"Hit {i+1}: Limit Reached")
                    else:
                        fails += 1
                        status.write(f"Hit {i+1}: Error {resp_code}")
                    
                    my_bar.progress((i + 1) / count)
                    time.sleep(0.15)
                
                status.update(label="Complete", state="complete", expanded=False)
            
            # Results Metrics
            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Success", success)
            m2.metric("Limits", limits)
            m3.metric("Errors", fails)
            
            if success > 0:
                st.toast(f"Activated {success} packages.", icon="✅")

        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Logout", kind="secondary"):
            st.session_state.clear()
            st.rerun()
