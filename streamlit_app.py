import streamlit as st
import requests
import base64
import time
import urllib3

# --- 1. SETUP ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU Glass",
    page_icon="💎",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- 3. iOS GLASSMORPHISM CSS ---
st.markdown("""
<style>
    /* 1. BACKGROUND: Deep Abstract Gradient to show off the glass effect */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(30, 0, 0) 0%, rgb(10, 10, 15) 40%, rgb(0, 0, 0) 90%);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Hide Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 2. THE GLASS CARD CONTAINER */
    .glass-container {
        background: rgba(255, 255, 255, 0.05); /* Ultra low opacity white */
        backdrop-filter: blur(20px);            /* Heavy Blur */
        -webkit-backdrop-filter: blur(20px);    /* Safari Support */
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 30px 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
    }

    /* 3. INPUT FIELDS (Glassy Look) */
    .stTextInput > div > div > input {
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        height: 55px !important;
        font-size: 18px !important;
        padding-left: 15px !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #ff3b30 !important; /* iOS Red */
        background-color: rgba(0, 0, 0, 0.5) !important;
        box-shadow: 0 0 15px rgba(255, 59, 48, 0.3);
    }

    /* 4. BUTTONS (iOS Style) */
    .stButton > button {
        width: 100%;
        border-radius: 16px;
        height: 55px !important;
        font-weight: 600;
        font-size: 17px !important;
        border: none;
        backdrop-filter: blur(10px);
        transition: transform 0.2s;
    }
    
    /* Primary Button: Vibrant Gradient */
    button[kind="primary"] {
        background: linear-gradient(135deg, #ff3b30 0%, #d70015 100%) !important;
        box-shadow: 0 4px 15px rgba(215, 0, 21, 0.4);
        color: white !important;
    }
    button[kind="primary"]:active {
        transform: scale(0.97);
    }

    /* Secondary Button: Frosted Glass */
    button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
    }

    /* 5. TYPOGRAPHY & TITLES */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.5px;
        color: white;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        font-weight: 600;
    }

    /* 6. SELECT BOX & SLIDER */
    .stSelectbox > div > div {
        background-color: rgba(0, 0, 0, 0.3);
        color: white;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: 50px;
    }
    
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIC (Unchanged) ---
def get_session():
    s = requests.Session()
    s.verify = False
    return s

def request_otp(phone):
    s = get_session()
    headers = {"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = s.post(f"{AUTH_OTP_URL}/authorize", headers=headers, data={"login_hint": f"+30{phone}", "response_type": "code"})
        return res.status_code in [200, 202]
    except: return False

def verify_otp(phone, otp):
    s = get_session()
    headers = {"Authorization": "Basic RTBqanJibnB3em9KUkxJZFRpYzZBOWJZMzU1Yzh5QlI6RGczaUFVWUVHSXFCVHB1Tw==", "api-key-name": "CUAPP", "vf-country-code": "GR", "User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*"}
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
    try: return s.post(ORDER_URL, headers=headers, json=payload).status_code
    except: return 0

# --- 5. UI LAYOUT ---

if 'step' not in st.session_state: st.session_state.step = 'login'
if 'phone' not in st.session_state: st.session_state.phone = ""
if 'token' not in st.session_state: st.session_state.token = None

# >>>> SCREEN 1: LOGIN <<<<
if st.session_state.step == 'login':
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Glass Card Start
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>CU LOGIN</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 14px;'>Premium Tool</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">MOBILE NUMBER</p>', unsafe_allow_html=True)
    phone = st.text_input("Mobile", placeholder="69...", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Get Code", type="primary"):
        if len(phone) == 10:
            with st.spinner("Connecting..."):
                if request_otp(phone):
                    st.session_state.phone = phone
                    st.session_state.step = 'otp'
                    st.rerun()
                else: st.toast("Failed", icon="❌")
        else: st.toast("Invalid Format", icon="⚠️")
        
    st.markdown('</div>', unsafe_allow_html=True) # End Glass

# >>>> SCREEN 2: OTP <<<<
elif st.session_state.step == 'otp':
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center;'>Verify</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: rgba(255,255,255,0.7);'>Sent to {st.session_state.phone}</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">SMS CODE</p>', unsafe_allow_html=True)
    otp = st.text_input("OTP", type="password", placeholder="••••", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Back", type="secondary"):
            st.session_state.step = 'login'
            st.rerun()
    with col2:
        if st.button("Enter", type="primary"):
            token = verify_otp(st.session_state.phone, otp)
            if token:
                st.session_state.token = token
                st.session_state.step = 'app'
                st.rerun()
            else: st.toast("Wrong OTP", icon="⛔")
            
    st.markdown('</div>', unsafe_allow_html=True)

# >>>> SCREEN 3: DASHBOARD <<<<
elif st.session_state.step == 'app':
    
    # Header Info
    st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: space-between; padding: 10px 10px;'>
        <h2 style='margin:0;'>Control</h2>
        <div style='background: rgba(255,59,48,0.2); padding: 5px 12px; border-radius: 20px; border: 1px solid rgba(255,59,48,0.4);'>
            <span style='color: #ff3b30; font-weight: bold; font-size: 14px;'>● {st.session_state.phone}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # MAIN GLASS CARD
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">TARGET NUMBER</p>', unsafe_allow_html=True)
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">PACKAGE TYPE</p>', unsafe_allow_html=True)
    ptype = st.selectbox("Type", ["🥤 CU Shake (Data)", "📞 Voice Bonus"], label_visibility="collapsed")
    offer_id = "BDLCUShakeBon7" if "Shake" in ptype else "BDLBonVoice3"
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">QUANTITY</p>', unsafe_allow_html=True)
    qty = st.slider("Qty", 1, 50, 1, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(f"Activate ({qty})", type="primary"):
        clean_trg = target.replace(" ", "").replace("+30", "")[-10:]
        
        status_text = st.empty()
        bar = st.progress(0)
        
        s, l, f = 0, 0, 0
        for i in range(qty):
            c = activate(st.session_state.token, clean_trg, offer_id)
            if c in [200, 201]: s += 1
            elif c == 403: l += 1
            else: f += 1
            
            bar.progress((i + 1) / qty)
            status_text.markdown(f"<p style='color:white; text-align:center;'>Processing {i+1} / {qty}...</p>", unsafe_allow_html=True)
            time.sleep(0.1)
            
        status_text.empty()
        bar.empty()
        
        # Results Display
        if s > 0: st.markdown(f"<div style='background:rgba(50,205,50,0.2); padding:10px; border-radius:10px; text-align:center; margin-bottom:5px; border:1px solid rgba(50,205,50,0.4);'>✅ Success: {s}</div>", unsafe_allow_html=True)
        if l > 0: st.markdown(f"<div style='background:rgba(255,204,0,0.2); padding:10px; border-radius:10px; text-align:center; margin-bottom:5px; border:1px solid rgba(255,204,0,0.4);'>⚠️ Limit: {l}</div>", unsafe_allow_html=True)
        if f > 0: st.markdown(f"<div style='background:rgba(255,59,48,0.2); padding:10px; border-radius:10px; text-align:center; border:1px solid rgba(255,59,48,0.4);'>❌ Error: {f}</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # End Glass
    
    if st.button("Log Out", type="secondary"):
        st.session_state.clear()
        st.rerun()
