import streamlit as st
import requests
import base64
import time
import urllib3

# --- SETUP ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="CU", page_icon="🔴", layout="centered", initial_sidebar_state="collapsed")

# --- CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- CSS (CLEAN & FLAT) ---
st.markdown("""
<style>
    /* 1. BACKGROUND */
    .stApp {
        background-color: #000000;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 2. REMOVE STREAMLIT PADDING/HEADER */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 3rem !important;
        max-width: 400px !important; /* Mobile Width Only */
        margin: auto;
    }

    /* 3. INPUT FIELD STYLING (The Box) */
    /* Αυτό φτιάχνει το input να είναι το ΜΟΝΑΔΙΚΟ κουτί */
    .stTextInput > div > div > input {
        background-color: #1C1C1E !important; /* Dark Gray */
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 55px !important;
        padding-left: 20px !important;
        font-size: 18px !important;
    }
    
    /* Όταν πατάς κλικ να μην βγάζει κόκκινο περίγραμμα, απλά να φωτίζει λίγο */
    .stTextInput > div > div > input:focus {
        background-color: #2C2C2E !important;
        color: white !important;
    }

    /* 4. BUTTON STYLING */
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        height: 55px !important;
        background-color: #E60000 !important; /* Vodafone Red */
        color: white !important;
        font-weight: 600 !important;
        font-size: 18px !important;
        border: none !important;
        margin-top: 10px;
    }
    .stButton > button:active {
        opacity: 0.7;
    }
    
    /* Secondary Button (Gray) */
    button[kind="secondary"] {
        background-color: transparent !important;
        color: #666 !important;
        border: 1px solid #333 !important;
    }

    /* 5. TEXT LABELS */
    .label {
        color: #888;
        font-size: 13px;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 8px;
        margin-left: 5px;
        letter-spacing: 0.5px;
    }
    
    h1 {
        color: white; 
        font-weight: 800; 
        text-align: center; 
        margin-bottom: 30px;
        font-size: 30px;
    }
    
    /* Select Box Styling to match */
    .stSelectbox > div > div {
        background-color: #1C1C1E !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 55px !important;
        display: flex;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_session():
    s = requests.Session()
    s.verify = False
    return s

def request_otp(phone):
    try:
        s = get_session()
        res = s.post(f"{AUTH_OTP_URL}/authorize", 
                     headers={"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}, 
                     data={"login_hint": f"+30{phone}", "response_type": "code"})
        return res.status_code in [200, 202]
    except: return False

def verify_otp(phone, otp):
    try:
        s = get_session()
        code = base64.b64encode(f"30{phone}:{otp}".encode()).decode()
        res = s.post(f"{AUTH_OTP_URL}/token", 
                     headers={"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*"}, 
                     data={"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": code})
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def activate(token, target, offer):
    try:
        s = get_session()
        res = s.post(ORDER_URL, 
                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT}, 
                     json={"productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer}}], "relatedParty": [{"role": "subscriber", "id": target}]})
        return res.status_code
    except: return 0

# --- UI LOGIC ---
if 'step' not in st.session_state: st.session_state.step = 'login'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# > SCREEN 1: LOGIN
if st.session_state.step == 'login':
    st.markdown("<h1>CU LOGIN</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>MOBILE NUMBER</div>", unsafe_allow_html=True)
    phone = st.text_input("Mobile", placeholder="69...", label_visibility="collapsed")
    
    if st.button("GET CODE", type="primary"):
        if len(phone) == 10:
            if request_otp(phone):
                st.session_state.phone = phone
                st.session_state.step = 'otp'
                st.rerun()
            else: st.error("Connection Failed")
        else: st.warning("Invalid Number")

# > SCREEN 2: OTP
elif st.session_state.step == 'otp':
    st.markdown("<h1>VERIFY</h1>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center; color:#666; margin-bottom:20px;'>SMS sent to {st.session_state.phone}</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>ENTER CODE</div>", unsafe_allow_html=True)
    otp = st.text_input("OTP", type="password", placeholder="••••", label_visibility="collapsed")
    
    if st.button("LOGIN", type="primary"):
        token = verify_otp(st.session_state.phone, otp)
        if token:
            st.session_state.token = token
            st.session_state.step = 'dashboard'
            st.rerun()
        else: st.error("Invalid Code")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Go Back", type="secondary"):
        st.session_state.step = 'login'
        st.rerun()

# > SCREEN 3: DASHBOARD
elif st.session_state.step == 'dashboard':
    st.markdown(f"<h1>{st.session_state.phone}</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>TARGET NUMBER</div>", unsafe_allow_html=True)
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>PACKAGE</div>", unsafe_allow_html=True)
    ptype = st.selectbox("Type", ["🥤 CU Shake (Data)", "📞 Voice Bonus"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>QUANTITY</div>", unsafe_allow_html=True)
    qty = st.slider("Qty", 1, 50, 1, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(f"ACTIVATE ({qty})", type="primary"):
        offer = "BDLCUShakeBon7" if "Shake" in ptype else "BDLBonVoice3"
        clean_trg = target.replace(" ", "").replace("+30", "")[-10:]
        
        bar = st.progress(0)
        s, l, f = 0, 0, 0
        
        for i in range(qty):
            code = activate(st.session_state.token, clean_trg, offer)
            if code in [200, 201]: s += 1
            elif code == 403: l += 1
            else: f += 1
            bar.progress((i+1)/qty)
            time.sleep(0.05)
            
        bar.empty()
        
        # Simple Stats
        cols = st.columns(3)
        cols[0].metric("✅", s)
        cols[1].metric("⚠️", l)
        cols[2].metric("❌", f)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LOGOUT", type="secondary"):
        st.session_state.clear()
        st.rerun()
