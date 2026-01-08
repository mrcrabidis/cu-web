import streamlit as st
import requests
import base64
import time
import urllib3

# --- 1. SETUP ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU", 
    page_icon="🔴", 
    layout="wide",  # Χρησιμοποιούμε όλο το πλάτος
    initial_sidebar_state="collapsed"
)

# --- 2. THE LOGIC ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

def get_session():
    s = requests.Session()
    s.verify = False
    return s

def request_otp(phone):
    try:
        s = get_session()
        res = s.post(f"{AUTH_OTP_URL}/authorize", headers={"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}, data={"login_hint": f"+30{phone}", "response_type": "code"})
        return res.status_code in [200, 202]
    except: return False

def verify_otp(phone, otp):
    try:
        s = get_session()
        code = base64.b64encode(f"30{phone}:{otp}".encode()).decode()
        res = s.post(f"{AUTH_OTP_URL}/token", headers={"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*"}, data={"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": code})
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def activate(token, target, offer):
    try:
        s = get_session()
        res = s.post(ORDER_URL, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT}, json={"productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer}}], "relatedParty": [{"role": "subscriber", "id": target}]})
        return res.status_code
    except: return 0

# --- 3. THE "NATIVE APP" CSS ---
st.markdown("""
<style>
    /* Full Black Background */
    .stApp {
        background-color: #000000;
        font-family: -apple-system, Helvetica, sans-serif;
    }

    /* REMOVE ALL DEFAULT PADDING */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;  /* Κενό αριστερά */
        padding-right: 1.5rem !important; /* Κενό δεξιά */
        max-width: 100% !important;
    }

    /* HIDE JUNK */
    #MainMenu, footer, header {display: none !important;}

    /* INPUTS: Full Width, No Borders, Native Look */
    .stTextInput > div > div > input {
        background-color: #1C1C1E !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 55px !important;
        font-size: 17px !important;
        padding-left: 20px !important;
    }
    .stTextInput > div > div > input:focus {
        background-color: #2C2C2E !important; /* Lighter on focus */
    }

    /* SELECT BOX */
    .stSelectbox > div > div {
        background-color: #1C1C1E !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 55px !important;
    }

    /* BUTTONS: Big, Red, Bottom */
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        height: 55px !important;
        background-color: #E60000 !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        border: none !important;
        margin-top: 20px;
    }
    
    /* Secondary Button (Logout/Back) */
    button[kind="secondary"] {
        background-color: transparent !important;
        color: #666 !important;
        margin-top: 0px;
    }

    /* TYPOGRAPHY */
    h1 {
        text-align: center;
        color: white;
        font-weight: 800;
        margin-bottom: 40px;
        font-size: 28px;
    }
    
    /* Labels small and uppercase */
    .label {
        font-size: 12px;
        color: #888;
        font-weight: 600;
        margin-bottom: 8px;
        margin-left: 5px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. APP FLOW ---
if 'step' not in st.session_state: st.session_state.step = 'login'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# >>>> 1. LOGIN SCREEN <<<<
if st.session_state.step == 'login':
    st.markdown("<h1>CU</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>MOBILE NUMBER</div>", unsafe_allow_html=True)
    phone = st.text_input("Mobile", placeholder="69...", label_visibility="collapsed")
    
    if st.button("CONTINUE", type="primary"):
        if len(phone) == 10:
            if request_otp(phone):
                st.session_state.phone = phone
                st.session_state.step = 'otp'
                st.rerun()
            else: st.error("Error connecting")
        else: st.warning("Invalid number")

# >>>> 2. OTP SCREEN <<<<
elif st.session_state.step == 'otp':
    st.markdown("<h1>VERIFY</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#555; margin-top:-30px; margin-bottom:30px;'>{st.session_state.phone}</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>SMS CODE</div>", unsafe_allow_html=True)
    otp = st.text_input("OTP", type="password", placeholder="••••", label_visibility="collapsed")
    
    if st.button("LOGIN", type="primary"):
        token = verify_otp(st.session_state.phone, otp)
        if token:
            st.session_state.token = token
            st.session_state.step = 'dash'
            st.rerun()
        else: st.error("Invalid Code")
    
    if st.button("Back", type="secondary"):
        st.session_state.step = 'login'
        st.rerun()

# >>>> 3. DASHBOARD SCREEN <<<<
elif st.session_state.step == 'dash':
    st.markdown(f"<h2 style='text-align:center; color:white; margin-bottom:40px;'>{st.session_state.phone}</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>TARGET</div>", unsafe_allow_html=True)
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>PACKAGE</div>", unsafe_allow_html=True)
    ptype = st.selectbox("Type", ["🥤 CU Shake (Data)", "📞 Voice Bonus"], label_visibility="collapsed")
    
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>QUANTITY</div>", unsafe_allow_html=True)
    qty = st.slider("Qty", 1, 50, 1, label_visibility="collapsed")
    
    if st.button("ACTIVATE", type="primary"):
        offer = "BDLCUShakeBon7" if "Shake" in ptype else "BDLBonVoice3"
        clean = target.replace(" ", "").replace("+30", "")[-10:]
        
        bar = st.progress(0)
        s, l, f = 0, 0, 0
        for i in range(qty):
            c = activate(st.session_state.token, clean, offer)
            if c in [200,201]: s+=1
            elif c==403: l+=1
            else: f+=1
            bar.progress((i+1)/qty)
            time.sleep(0.05)
        bar.empty()
        
        # Minimal Results
        c1, c2, c3 = st.columns(3)
        c1.metric("OK", s)
        c2.metric("Limit", l)
        c3.metric("Err", f)

    if st.button("LOGOUT", type="secondary"):
        st.session_state.clear()
        st.rerun()
