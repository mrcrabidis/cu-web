import streamlit as st
import requests
import base64
import time
import urllib3

# --- 1. SETUP & CONFIG ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- 3. HIGH-END MOBILE CSS ---
st.markdown("""
<style>
    /* RESET & BACKGROUND */
    .stApp {
        background-color: #000000; /* True Black for OLED */
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    }

    /* CENTER LAYOUT LIKE A MOBILE APP */
    .block-container {
        max_width: 380px !important; /* Force Mobile Width */
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto !important; /* Perfect Center */
    }

    /* REMOVE CLUTTER */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* INPUT FIELDS (iOS Style) */
    .stTextInput > div > div > input {
        background-color: #1c1c1e !important; /* iOS Dark Gray */
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        height: 50px !important;
        font-size: 17px !important;
        padding-left: 15px !important;
    }
    .stTextInput > div > div > input:focus {
        background-color: #2c2c2e !important;
    }
    
    /* SELECT & SLIDER */
    .stSelectbox > div > div {
        background-color: #1c1c1e !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        height: 50px !important;
    }

    /* BUTTONS */
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        height: 52px !important;
        font-weight: 600 !important;
        font-size: 17px !important;
        border: none !important;
        transition: opacity 0.2s;
    }
    
    /* Primary (Red) */
    button[kind="primary"] {
        background-color: #E60000 !important;
        color: white !important;
    }
    button[kind="primary"]:active {
        opacity: 0.7;
    }

    /* Secondary (Gray) */
    button[kind="secondary"] {
        background-color: #1c1c1e !important;
        color: #E60000 !important; /* Red Text */
    }

    /* CUSTOM CARDS */
    .ios-group {
        background-color: #1c1c1e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
    }
    
    .label-header {
        color: #8e8e93;
        font-size: 13px;
        text-transform: uppercase;
        margin-left: 15px;
        margin-bottom: 8px;
        margin-top: 10px;
        font-weight: 500;
    }
    
    h1 {
        font-weight: 700;
        font-size: 28px;
        text-align: center;
        padding-bottom: 20px;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIC ---
def get_session():
    s = requests.Session()
    s.verify = False
    return s

def request_otp(phone):
    s = get_session()
    headers = {"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    try: return s.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data={"login_hint": f"+30{phone}", "response_type": "code"}).status_code in [200, 202]
    except: return False

def verify_otp(phone, otp):
    s = get_session()
    headers = {"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*"}
    try:
        res = s.post(f"{AUTH_OTP_URL}/token", headers=headers, data={"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": base64.b64encode(f"30{phone}:{otp}".encode()).decode()})
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def activate(token, target, offer):
    s = get_session()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT}
    try: return s.post(ORDER_URL, headers=headers, json={"productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer}}], "relatedParty": [{"role": "subscriber", "id": target}]}).status_code
    except: return 0

# --- 5. UI FLOW ---

if 'step' not in st.session_state: st.session_state.step = 'login'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# >>>> LOGIN <<<<
if st.session_state.step == 'login':
    st.markdown("<h1>CU</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='label-header'>SIGN IN</div>", unsafe_allow_html=True)
    st.markdown("<div class='ios-group'>", unsafe_allow_html=True)
    phone = st.text_input("Mobile Number", placeholder="69xxxxxxxx", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Continue", type="primary"):
        if len(phone) == 10:
            if request_otp(phone):
                st.session_state.phone = phone
                st.session_state.step = 'otp'
                st.rerun()
            else: st.error("Connection Failed")
        else: st.warning("Check Number")

# >>>> OTP <<<<
elif st.session_state.step == 'otp':
    st.markdown("<h1>Verify</h1>", unsafe_allow_html=True)
    st.caption(f"Code sent to {st.session_state.phone}")
    
    st.markdown("<div class='label-header'>SMS CODE</div>", unsafe_allow_html=True)
    st.markdown("<div class='ios-group'>", unsafe_allow_html=True)
    otp = st.text_input("Code", type="password", placeholder="••••", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Login", type="primary"):
        token = verify_otp(st.session_state.phone, otp)
        if token:
            st.session_state.token = token
            st.session_state.step = 'app'
            st.rerun()
        else: st.error("Invalid Code")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Back", type="secondary"):
        st.session_state.step = 'login'
        st.rerun()

# >>>> DASHBOARD <<<<
elif st.session_state.step == 'app':
    
    # Status Header
    st.markdown(f"""
    <div style='text-align:center; padding-bottom:20px;'>
        <div style='font-size:32px; font-weight:700;'>{st.session_state.phone}</div>
        <div style='color:#4CD964; font-size:14px; font-weight:600;'>● Active</div>
    </div>
    """, unsafe_allow_html=True)

    # Settings Group
    st.markdown("<div class='label-header'>CONFIGURATION</div>", unsafe_allow_html=True)
    st.markdown("<div class='ios-group'>", unsafe_allow_html=True)
    
    st.caption("Target Number")
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True) # Spacer
    
    st.caption("Package")
    ptype = st.selectbox("Type", ["CU Shake (Data)", "Voice Bonus"], label_visibility="collapsed")
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True) # Spacer
    
    st.caption("Quantity")
    qty = st.slider("Qty", 1, 50, 1, label_visibility="collapsed")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Action
    offer_id = "BDLCUShakeBon7" if "Shake" in ptype else "BDLBonVoice3"
    
    if st.button(f"Activate {qty} Packages", type="primary"):
        clean_trg = target.replace(" ", "").replace("+30", "")[-10:]
        
        # Clean Progress UI
        box = st.empty()
        bar = st.progress(0)
        s, l, f = 0, 0, 0
        
        for i in range(qty):
            c = activate(st.session_state.token, clean_trg, offer_id)
            if c in [200, 201]: s += 1
            elif c == 403: l += 1
            else: f += 1
            bar.progress((i+1)/qty)
            time.sleep(0.05)
            
        box.empty()
        bar.empty()
        
        # Simple Results
        cols = st.columns(3)
        cols[0].metric("Success", s)
        cols[1].metric("Limits", l)
        cols[2].metric("Errors", f)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign Out", type="secondary"):
        st.session_state.clear()
        st.rerun()
