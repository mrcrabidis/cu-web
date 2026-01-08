import streamlit as st
import requests
import base64
import time
import urllib3

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="CU Commander",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTS ---
BASE_URL = "https://eu3.api.vodafone.com"
AUTH_OTP_URL = f"{BASE_URL}/OAuth2OTPGrant/v1"
ORDER_URL = f"{BASE_URL}/productOrderingAndValidation/v1/productOrder"
USER_AGENT = "My%20CU/5.8.6.2 CFNetwork/3860.300.31 Darwin/25.2.0"

# --- CUSTOM CSS (MODERN UI) ---
st.markdown("""
<style>
    /* Γενικό Στυλ */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #262730;
        color: white;
        border-radius: 12px;
        height: 50px;
        font-size: 18px;
        border: 1px solid #444;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 55px;
        font-weight: bold;
        font-size: 18px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Primary Button (Vodafone Red) */
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="primary"] {
        background: linear-gradient(90deg, #E60000 0%, #B30000 100%);
        border: none;
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > button[kind="primary"]:hover {
        box-shadow: 0 0 15px rgba(230, 0, 0, 0.6);
        transform: scale(1.02);
    }

    /* Cards */
    .css-card {
        background-color: #1c1e24;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- LOGIC FUNCTIONS ---
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
st.markdown("<h1 style='text-align: center; color: #E60000;'>🔴 CU COMMANDER</h1>", unsafe_allow_html=True)
st.markdown("---")

# 1. LOGIN SCREEN
if st.session_state.step == 'login_phone':
    st.markdown("<div class='css-card'>", unsafe_allow_html=True)
    st.subheader("👋 Welcome")
    st.write("Εισάγετε τον αριθμό CU για σύνδεση")
    
    phone_input = st.text_input("Mobile Number", placeholder="69xxxxxxxx", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("SEND SMS ➡️", type="primary"):
        if len(phone_input) == 10:
            with st.spinner("⏳ Επικοινωνία με Vodafone..."):
                if request_otp(phone_input):
                    st.session_state.phone = phone_input
                    st.session_state.step = 'login_otp'
                    st.rerun()
                else:
                    st.toast("❌ Failed to send SMS", icon="⚠️")
        else:
            st.toast("⚠️ Ελέγξτε τον αριθμό", icon="📱")
    st.markdown("</div>", unsafe_allow_html=True)

# 2. OTP SCREEN
elif st.session_state.step == 'login_otp':
    st.markdown("<div class='css-card'>", unsafe_allow_html=True)
    st.subheader(f"🔐 Verify {st.session_state.phone}")
    st.write("Εισάγετε τον κωδικό που λάβατε")
    
    otp_input = st.text_input("OTP Code", type="password", placeholder="1234", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔙"):
            st.session_state.step = 'login_phone'
            st.rerun()
    with col2:
        if st.button("LOGIN 🚀", type="primary"):
            with st.spinner("⏳ Verifying..."):
                token = verify_otp(st.session_state.phone, otp_input)
                if token:
                    st.session_state.token = token
                    st.session_state.step = 'dashboard'
                    st.balloons()
                    st.rerun()
                else:
                    st.toast("❌ Λάθος κωδικός OTP", icon="⛔")
    st.markdown("</div>", unsafe_allow_html=True)

# 3. DASHBOARD
elif st.session_state.step == 'dashboard':
    
    # User Info Card
    st.markdown(f"""
    <div class='css-card' style='display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <span style='font-size: 14px; color: #888;'>LOGGED IN AS</span><br>
            <span style='font-size: 22px; font-weight: bold; color: #E60000;'>{st.session_state.phone}</span>
        </div>
        <div style='font-size: 30px;'>👤</div>
    </div>
    """, unsafe_allow_html=True)

    # Control Card
    st.markdown("<div class='css-card'>", unsafe_allow_html=True)
    st.write("🎯 **Target Number**")
    target = st.text_input("Target", value=st.session_state.phone, label_visibility="collapsed")
    
    st.write("🎁 **Package**")
    option = st.selectbox("Offer", 
                          ["🥤 Shake (BDLCUShakeBon7)", "📞 Voice (BDLBonVoice3)"],
                          label_visibility="collapsed")
    
    offering_id = "BDLCUShakeBon7" if "Shake" in option else "BDLBonVoice3"
    
    st.write("🔄 **Quantity**")
    count = st.slider("Quantity", 1, 50, 1, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔥 ACTIVATE NOW", type="primary"):
        clean_target = target.replace(" ", "").replace("+30", "")[-10:]
        
        # Modern Status Container
        with st.status("🚀 Processing Requests...", expanded=True) as status:
            success, limits, fails = 0, 0, 0
            
            progress_text = st.empty()
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
    
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
