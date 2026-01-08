import streamlit as st
import requests
import base64
import time
import urllib3

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU BOOST",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- CUSTOM CSS (PROFESSIONAL & MODERN UI) ---
st.markdown("""
<style>
    /* Γενικό Στυλ & Φόντο */
    .stApp {
        background: linear-gradient(135deg, #0f1116 0%, #1a1c24 100%);
        color: #e0e0e0;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Εξαφάνιση των Streamlit στοιχείων */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Κύριος Τίτλος (Gradient) */
    .main-title {
        text-align: center;
        font-size: 3em;
        font-weight: 800;
        margin-bottom: 20px;
        background: linear-gradient(90deg, #E60000, #FF4B2B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }

    /* Κάρτες (Glassmorphism) */
    .css-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 25px;
        transition: transform 0.3s ease;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.08);
        color: #ffffff;
        border-radius: 12px;
        height: 55px;
        font-size: 18px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding-left: 20px;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E60000;
        box-shadow: 0 0 10px rgba(230, 0, 0, 0.5);
        background-color: rgba(255, 255, 255, 0.12);
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 60px;
        font-weight: 700;
        font-size: 18px;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        text-transform: uppercase;
    }

    /* Primary Button (Vodafone Gradient) */
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="primary"] {
        background: linear-gradient(90deg, #E60000 0%, #B30000 100%);
        border: none;
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="primary"]:hover {
        box-shadow: 0 0 20px rgba(230, 0, 0, 0.7);
        transform: translateY(-2px);
    }

    /* Secondary Button */
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #e0e0e0;
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }

    /* Metrics & Status */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
    }
    .stStatus {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
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
st.markdown("<h1 class='main-title'>🚀 CU BOOST</h1>", unsafe_allow_html=True)

# 1. LOGIN SCREEN
if st.session_state.step == 'login_phone':
    # Κεντράρισμα της κάρτας
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("👋 Welcome Back")
        st.write("Sign in to boost your CU number.")
        
        phone_input = st.text_input("Mobile Number", placeholder="Your 10-digit CU Number", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("SEND SMS CODE ➡️", type="primary"):
            if len(phone_input) == 10:
                with st.spinner("⏳ Connecting to Vodafone..."):
                    if request_otp(phone_input):
                        st.session_state.phone = phone_input
                        st.session_state.step = 'login_otp'
                        st.rerun()
                    else:
                        st.toast("❌ Failed to send SMS", icon="⚠️")
            else:
                st.toast("⚠️ Please enter a valid 10-digit number.", icon="📱")
        st.markdown("</div>", unsafe_allow_html=True)

# 2. OTP SCREEN
elif st.session_state.step == 'login_otp':
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader(f"🔐 Verification")
        st.write(f"Enter the code sent to **{st.session_state.phone}**")
        
        otp_input = st.text_input("OTP Code", type="password", placeholder="Your OTP Code", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("BACK"):
                st.session_state.step = 'login_phone'
                st.rerun()
        with c2:
            if st.button("LOGIN 🚀", type="primary"):
                with st.spinner("⏳ Verifying..."):
                    token = verify_otp(st.session_state.phone, otp_input)
                    if token:
                        st.session_state.token = token
                        st.session_state.step = 'dashboard'
                        st.balloons()
                        st.rerun()
                    else:
                        st.toast("❌ Invalid OTP Code", icon="⛔")
        st.markdown("</div>", unsafe_allow_html=True)

# 3. DASHBOARD
elif st.session_state.step == 'dashboard':
    
    # User Info Card
    st.markdown(f"""
    <div class='css-card' style='display: flex; justify-content: space-between; align-items: center; padding: 20px 30px;'>
        <div>
            <span style='font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px;'>Logged in as</span><br>
            <span style='font-size: 24px; font-weight: 800; background: linear-gradient(90deg, #E60000, #FF4B2B); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>{st.session_state.phone}</span>
        </div>
        <div style='font-size: 36px;'>👤</div>
    </div>
    """, unsafe_allow_html=True)

    # Control Card
    st.markdown("<div class='css-card'>", unsafe_allow_html=True)
    st.subheader("🎛️ Boost Controls")
    st.markdown("<br>", unsafe_allow_html=True)

    st.write("**🎯 Target Number**")
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed", placeholder="Enter Target Number")
    
    st.markdown("<br>", unsafe_allow_html=True)

    st.write("**🎁 Select Package**")
    option = st.selectbox("Offer", 
                          ["🥤 CU Shake (BDLCUShakeBon7)", "📞 Voice Bonus (BDLBonVoice3)"],
                          label_visibility="collapsed")
    
    offering_id = "BDLCUShakeBon7" if "Shake" in option else "BDLBonVoice3"
    
    st.markdown("<br>", unsafe_allow_html=True)

    st.write("**🔄 Quantity**")
    count = st.slider("Quantity", 1, 50, 1, label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.button("🔥 ACTIVATE NOW", type="primary"):
        clean_target = target.replace(" ", "").replace("+30", "")[-10:]
        
        # Modern Status Container
        with st.status("🚀 Processing Requests...", expanded=True) as status:
            success, limits, fails = 0, 0, 0
            
            my_bar = st.progress(0)
            
            for i in range(count):
                resp_code = activate_package(st.session_state.token, clean_target, offering_id)
                
                if resp_code in [200, 201]:
                    success += 1
                    status.write(f"✅ Hit {i+1}: Success")
                elif resp_code == 403:
                    limits += 1
                    status.write(f"⚠️ Hit {i+1}: Limit Reached")
                else:
                    fails += 1
                    status.write(f"❌ Hit {i+1}: Error {resp_code}")
                
                my_bar.progress((i + 1) / count)
                time.sleep(0.15)
            
            status.update(label="✅ Operation Complete!", state="complete", expanded=False)
        
        # Results Metrics
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Success", success, delta_color="normal")
        m2.metric("Limits", limits, delta_color="off")
        m3.metric("Errors", fails, delta_color="inverse")
        
        if success > 0:
            st.toast(f"Activated {success} packages!", icon="🎉")

    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🚪 LOGOUT"):
        st.session_state.clear()
        st.rerun()
