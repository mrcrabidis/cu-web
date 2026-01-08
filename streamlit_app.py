import streamlit as st
import requests
import base64
import time
import urllib3

# --- 1. CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU Mobile",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- 3. MOBILE CSS (IPHONE OPTIMIZED) ---
st.markdown("""
<style>
    /* Reset & Dark Mode Base */
    .stApp {
        background-color: #000000;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif; /* San Francisco Font */
    }
    
    /* Hide Streamlit Bloat */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        max-width: 100%;
    }

    /* INPUTS: Big & Tappable */
    .stTextInput > div > div > input {
        background-color: #1c1c1e; /* iOS Dark Gray */
        color: white;
        border: none;
        border-radius: 12px;
        height: 60px !important;
        font-size: 20px !important;
        padding-left: 20px;
        text-align: center;
    }
    .stTextInput > div > div > input:focus {
        box-shadow: 0 0 0 2px #E60000; /* Red Focus */
    }

    /* BUTTONS: Full Width & Actionable */
    .stButton > button {
        width: 100%;
        border-radius: 14px;
        height: 60px !important;
        font-weight: 600;
        font-size: 18px !important;
        border: none;
        margin-top: 10px;
    }

    /* Primary Button (Action) */
    button[kind="primary"] {
        background-color: #E60000 !important; /* Vodafone Red */
        color: white !important;
    }
    
    /* Secondary Button (Navigation) */
    button[kind="secondary"] {
        background-color: #2c2c2e !important;
        color: #98989d !important;
    }

    /* SLIDER & SELECTBOX */
    .stSelectbox > div > div {
        background-color: #1c1c1e;
        color: white;
        border-radius: 12px;
        height: 50px;
        border: none;
    }
    
    /* RESULTS METRICS */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #E60000;
    }
    
    /* CUSTOM CARD LIKE iOS WIDGET */
    .ios-card {
        background-color: #1c1c1e;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .label-text {
        color: #8e8e93;
        font-size: 13px;
        text-transform: uppercase;
        margin-bottom: 5px;
        font-weight: 600;
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
    headers = {
        "Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==",
        "api-key-name": "CUAPP",
        "vf-country-code": "GR",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        res = s.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data={"login_hint": f"+30{phone}", "response_type": "code"})
        return res.status_code in [200, 202]
    except: return False

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
    raw = f"30{phone}:{otp}"
    enc = base64.b64encode(raw.encode()).decode()
    try:
        res = s.post(f"{AUTH_OTP_URL}/token", headers=headers, data={"grant_type": "urn:vodafone:params:oauth:grant-type:otp", "code": enc})
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def activate(token, target, offer):
    s = get_session()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT}
    payload = {"productOrderItem": [{"action": "adhoc", "quantity": 1, "productOffering": {"id": offer}}], "relatedParty": [{"role": "subscriber", "id": target}]}
    try:
        return s.post(ORDER_URL, headers=headers, json=payload).status_code
    except: return 0

# --- 5. UI FLOW ---

if 'step' not in st.session_state: st.session_state.step = 'login'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# >>>> SCREEN 1: LOGIN <<<<
if st.session_state.step == 'login':
    st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 30px;'>CU LOGIN</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='label-text'>MOBILE NUMBER</div>", unsafe_allow_html=True)
    phone = st.text_input("Mobile", placeholder="69...", label_visibility="collapsed")
    
    st.write("") # Spacer
    
    if st.button("GET CODE", type="primary"):
        if len(phone) == 10:
            with st.spinner(""):
                if request_otp(phone):
                    st.session_state.phone = phone
                    st.session_state.step = 'otp'
                    st.rerun()
                else: st.toast("Failed", icon="❌")
        else: st.toast("Check number", icon="⚠️")

# >>>> SCREEN 2: OTP <<<<
elif st.session_state.step == 'otp':
    st.markdown(f"<h3 style='text-align: center; margin-bottom: 20px;'>Verify {st.session_state.phone}</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='label-text'>SMS CODE</div>", unsafe_allow_html=True)
    otp = st.text_input("OTP", type="password", placeholder="1234", label_visibility="collapsed")
    
    st.write("") # Spacer
    
    if st.button("LOGIN", type="primary"):
        with st.spinner(""):
            tk = verify_otp(st.session_state.phone, otp)
            if tk:
                st.session_state.token = tk
                st.session_state.step = 'app'
                st.rerun()
            else: st.toast("Wrong Code", icon="⛔")
            
    if st.button("Back", type="secondary"):
        st.session_state.step = 'login'
        st.rerun()

# >>>> SCREEN 3: APP <<<<
elif st.session_state.step == 'app':
    # Status Bar
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 10px; background: #1c1c1e; border-radius: 12px;'>
        <span style='color: #8e8e93; font-size: 14px;'>CONNECTED</span>
        <span style='color: white; font-weight: bold;'>{st.session_state.phone}</span>
    </div>
    """, unsafe_allow_html=True)

    # Main Controls in a Card
    st.markdown("<div class='ios-card'>", unsafe_allow_html=True)
    
    st.markdown("<div class='label-text'>TARGET NUMBER</div>", unsafe_allow_html=True)
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.markdown("<br><div class='label-text'>PACKAGE</div>", unsafe_allow_html=True)
    ptype = st.selectbox("Type", ["🥤 Shake (Data)", "📞 Voice (Bonus)"], label_visibility="collapsed")
    offer_id = "BDLCUShakeBon7" if "Shake" in ptype else "BDLBonVoice3"
    
    st.markdown("<br><div class='label-text'>QUANTITY</div>", unsafe_allow_html=True)
    qty = st.slider("Qty", 1, 50, 1, label_visibility="collapsed")
    
    st.markdown("</div>", unsafe_allow_html=True) # End Card

    # ACTION BUTTON
    if st.button(f"ACTIVATE ({qty})", type="primary"):
        clean_trg = target.replace(" ", "").replace("+30", "")[-10:]
        
        # Minimal Status
        status_box = st.empty()
        bar = st.progress(0)
        
        s, l, f = 0, 0, 0
        for i in range(qty):
            c = activate(st.session_state.token, clean_trg, offer_id)
            if c in [200, 201]: s += 1
            elif c == 403: l += 1
            else: f += 1
            
            bar.progress((i + 1) / qty)
            status_box.caption(f"Processing... {i+1}/{qty}")
            time.sleep(0.1)
            
        status_box.empty()
        bar.empty()
        
        # Results
        if s > 0: st.success(f"✅ Success: {s}")
        if l > 0: st.warning(f"⚠️ Limits: {l}")
        if f > 0: st.error(f"❌ Errors: {f}")

    # Spacer at bottom
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Logout", type="secondary"):
        st.session_state.clear()
        st.rerun()
