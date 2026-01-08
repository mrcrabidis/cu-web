import streamlit as st
import requests
import base64
import time
import urllib3

# --- SETUP ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU", 
    page_icon="🔴", 
    layout="centered", # Αυτό είναι σημαντικό
    initial_sidebar_state="collapsed"
)

# --- CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- CSS (PERFECT CENTERING FIX) ---
st.markdown("""
<style>
    /* 1. BACKGROUND */
    .stApp {
        background-color: #000000;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 2. REMOVE HEADER/FOOTER */
    #MainMenu, footer, header {visibility: hidden;}

    /* 3. CENTER THE MAIN CONTAINER (THE FIX) */
    div.block-container {
        max-width: 380px !important; /* Πλάτος iPhone */
        padding-top: 10vh !important; /* Κενό από πάνω για να μην είναι ταβάνι */
        padding-bottom: 5rem !important;
        margin-left: auto !important;  /* Αναγκαστικό κεντράρισμα */
        margin-right: auto !important; /* Αναγκαστικό κεντράρισμα */
        display: block !important;
    }

    /* 4. INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: #1C1C1E !important;
        color: white !important;
        border: 1px solid #333 !important; /* Λεπτό border για να φαίνεται */
        border-radius: 12px !important;
        height: 55px !important;
        padding-left: 20px !important;
        font-size: 16px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E60000 !important;
        background-color: #252525 !important;
    }

    /* 5. BUTTONS */
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        height: 55px !important;
        background-color: #E60000 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 18px !important;
        border: none !important;
        margin-top: 15px;
        transition: transform 0.1s;
    }
    .stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Secondary Button */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #444 !important;
        color: #888 !important;
    }

    /* 6. TYPOGRAPHY */
    h1 {
        text-align: center;
        font-weight: 800;
        font-size: 32px;
        color: white;
        margin-bottom: 30px;
        padding: 0;
    }
    
    .label {
        color: #8E8E93;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
        margin-left: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* SELECT & SLIDER FIXES */
    .stSelectbox > div > div {
        background-color: #1C1C1E !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
        height: 55px !important;
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

# --- APP FLOW ---
if 'step' not in st.session_state: st.session_state.step = 'login'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# >>>> LOGIN <<<<
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
            else: st.error("Connection Failed")
        else: st.warning("Invalid Number")

# >>>> OTP <<<<
elif st.session_state.step == 'otp':
    st.markdown("<h1>VERIFY</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#666; font-size:14px; margin-top:-20px;'>SMS sent to {st.session_state.phone}</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>SMS CODE</div>", unsafe_allow_html=True)
    otp = st.text_input("OTP", type="password", placeholder="••••", label_visibility="collapsed")
    
    if st.button("LOGIN", type="primary"):
        token = verify_otp(st.session_state.phone, otp)
        if token:
            st.session_state.token = token
            st.session_state.step = 'dashboard'
            st.rerun()
        else: st.error("Invalid Code")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("BACK", type="secondary"):
        st.session_state.step = 'login'
        st.rerun()

# >>>> DASHBOARD <<<<
elif st.session_state.step == 'dashboard':
    st.markdown(f"<h1>{st.session_state.phone}</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='label'>TARGET NUMBER</div>", unsafe_allow_html=True)
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    st.markdown("<div class='label'>PACKAGE</div>", unsafe_allow_html=True)
    ptype = st.selectbox("Type", ["🥤 CU Shake (Data)", "📞 Voice Bonus"], label_visibility="collapsed")
    
    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    st.markdown("<div class='label'>QUANTITY</div>", unsafe_allow_html=True)
    qty = st.slider("Qty", 1, 50, 1, label_visibility="collapsed")
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    
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
        
        cols = st.columns(3)
        cols[0].metric("Success", s)
        cols[1].metric("Limits", l)
        cols[2].metric("Error", f)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LOGOUT", type="secondary"):
        st.session_state.clear()
        st.rerun()
