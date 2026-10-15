import os
import time
import streamlit as st
import yt_dlp
from google import genai

# --- 1. Page Configuration (Mobile-Friendly & Responsive) ---
st.set_page_config(
    page_title="Islamic Kids Media Analyzer",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. PWA Meta Tags & Responsive Mobile Styling ---
st.markdown("""
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Kids Analyzer">
    <meta name="application-name" content="Kids Analyzer">
    <meta name="theme-color" content="#059669">
    <link rel="apple-touch-icon" href="https://api.iconify.design/noto:shield.svg">
    <link rel="manifest" href="data:application/manifest+json;utf8,%7B%22name%22%3A%22Islamic%20Kids%20Media%20Analyzer%22%2C%22short_name%22%3A%22Kids%20Analyzer%22%2C%22start_url%22%3A%22%2F%22%2C%22display%22%3A%22standalone%22%2C%22background_color%22%3A%22%23ffffff%22%2C%22theme_color%22%3A%22%23059669%22%2C%22icons%22%3A%5B%7B%22src%22%3A%22https%3A%2F%2Fapi.iconify.design%2Fnoto%3Ashield.svg%22%2C%22sizes%22%3A%22192x192%22%2C%22type%22%3A%22image%2Fsvg%2Bxml%22%7D%5D%7D">
</head>
<style>
    /* Responsive Mobile Container adjustments */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 760px !important;
    }

    /* Hero Header Card */
    .hero-card {
        background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%);
        color: white;
        padding: 1.5rem 1.25rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(5, 150, 105, 0.3);
        text-align: center;
    }
    .hero-title {
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.3;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        margin-top: 0.5rem;
        opacity: 0.95;
        line-height: 1.4;
    }

    /* Touch-friendly inputs and buttons */
    .stButton>button {
        width: 100% !important;
        height: 52px !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 14px 0 rgba(5, 150, 105, 0.39) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:active {
        transform: scale(0.98) !important;
    }

    /* Responsive Markdown Table */
    .stMarkdown table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        margin: 1.2rem 0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        font-size: 0.92rem !important;
    }
    .stMarkdown th {
        background: #047857 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 12px 14px !important;
        text-align: left !important;
        border: none !important;
    }
    .stMarkdown td {
        padding: 11px 13px !important;
        border-bottom: 1px solid #f3f4f6 !important;
        vertical-align: top !important;
        line-height: 1.45 !important;
    }
    .stMarkdown tr:last-child td {
        border-bottom: none !important;
    }
    .stMarkdown tr:nth-child(even) td {
        background-color: #f9fafb !important;
    }
    div[data-testid="stMarkdownContainer"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }
</style>
""", unsafe_allow_html=True)


# --- 3. Backend Gemini API Key Configuration ---
# Admin can optionally set the API key in .streamlit/secrets.toml or as an environment variable.
# Parents and general users will NEVER see this key in the UI.
BACKEND_GEMINI_API_KEY = ""

def get_backend_api_key():
    """
    Retrieves Gemini API key securely from:
    1. Streamlit Secrets (.streamlit/secrets.toml)
    2. Environment Variables (GEMINI_API_KEY or GOOGLE_API_KEY)
    3. Backend code variable (BACKEND_GEMINI_API_KEY)
    """
    # 1. Streamlit Secrets
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        if secret_key and str(secret_key).strip() and str(secret_key).strip() != "YOUR_GEMINI_API_KEY_HERE":
            return str(secret_key).strip()
    except Exception:
        pass

    # 2. Environment Variables
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key and env_key.strip() and env_key.strip() != "YOUR_GEMINI_API_KEY_HERE":
        return env_key.strip()

    # 3. Hardcoded backend configuration
    if BACKEND_GEMINI_API_KEY and BACKEND_GEMINI_API_KEY.strip() and BACKEND_GEMINI_API_KEY.strip() != "YOUR_GEMINI_API_KEY_HERE":
        return BACKEND_GEMINI_API_KEY.strip()

    return None


# --- 4. YouTube Anti-Bot & Downloader Logic (Auto cookies.txt) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_cookie_file():
    """Detects cookies.txt or cookies.txt.txt in the project directory."""
    for name in ["cookies.txt", "cookies.txt.txt"]:
        path = os.path.join(BASE_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    return None

def get_yt_dlp_options(output_template="temp_video_%(ext)s", use_cookies=True):
    """
    Configures yt-dlp with anti-bot mobile/TV player clients and automatically
    attaches cookies.txt if present in the same directory.
    """
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'overwrites': True,
        'quiet': True,
        'no_warnings': False,
        'noplaylist': True,
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
        'no_color': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'navigate',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'tv_downgraded', 'web_creator', 'mweb'],
                'player_skip': ['webpage', 'configs'],
            }
        }
    }

    if use_cookies:
        cookie_file = get_cookie_file()
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file

    return ydl_opts

def download_video(url, output_template="temp_video_%(ext)s"):
    """
    Downloads video using yt-dlp with anti-bot arguments, auto cookies, and fallback to bypass 403 errors.
    """
    ydl_opts = get_yt_dlp_options(output_template, use_cookies=True)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)
            if os.path.exists(downloaded_path) and os.path.getsize(downloaded_path) > 0:
                return downloaded_path
            raise RuntimeError("Video download hui lekin disk par dastyab nahi hai.")
    except Exception as primary_error:
        err_str = str(primary_error)

        # Fallback 1: Try with focused mobile clients (Android/iOS) to bypass 403 / PO-Token restrictions
        try:
            fallback_opts = get_yt_dlp_options(output_template, use_cookies=True)
            fallback_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['android', 'ios'],
                    'player_skip': ['webpage']
                }
            }
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_path = ydl.prepare_filename(info)
                if os.path.exists(downloaded_path) and os.path.getsize(downloaded_path) > 0:
                    return downloaded_path
        except Exception:
            pass

        # Fallback 2: If cookies were invalid/expired causing HTTP 403 Forbidden, retry without cookies
        try:
            no_cookie_opts = get_yt_dlp_options(output_template, use_cookies=False)
            with yt_dlp.YoutubeDL(no_cookie_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_path = ydl.prepare_filename(info)
                if os.path.exists(downloaded_path) and os.path.getsize(downloaded_path) > 0:
                    return downloaded_path
        except Exception:
            pass

        if "403" in err_str or "Forbidden" in err_str:
            raise RuntimeError(
                "YouTube HTTP Error 403 (Forbidden): YouTube ne access block kar diya hai.\n"
                "Barah-e-karam video ko direct browser se download kar ke upar 'Direct Video File Upload' ke zariye upload karein."
            )
        elif "Sign in to confirm you’re not a bot" in err_str or "bot" in err_str.lower() or "429" in err_str:
            raise RuntimeError(
                "YouTube Bot Protection: YouTube ne download ko block kar diya.\n"
                "Hal: Video ko direct browser se download kar ke file upload karein ya cookies.txt update karein."
            )
        elif "This video is not available" in err_str or "Video unavailable" in err_str:
            raise RuntimeError("Yeh video YouTube par dastyab nahi hai ya restrict ho chuki hai.")
        elif "Private video" in err_str or "Sign in" in err_str:
            raise RuntimeError("Yeh video private ya age-restricted hai.")
        else:
            raise RuntimeError(f"Video download nahi ho saki: {primary_error}")


# --- 5. Clean, Parent-Focused UI Layout ---
st.markdown("""
<div class="hero-card">
    <h1 class="hero-title">🛡️ Islamic Kids Media Analyzer</h1>
    <p class="hero-subtitle">Cartoons aur bachon ki videos ko Islamic nazarye aur safe parenting ke mutabiq screen karein.</p>
</div>
""", unsafe_allow_html=True)

# PWA Mobile Installation Quick Guide
with st.expander("📲 Mobile App Ki Tarah Install Karein (Home Screen Shortcut)", expanded=False):
    st.markdown("""
    **📱 Android (Chrome):**
    1. Browser ke upar 3 dots (**⋮**) par click karein.
    2. **"Add to Home screen"** ya **"Install app"** select karein.
    
    **🍎 iPhone (Safari):**
    1. Neeche Share button (⬆️) par tap karein.
    2. Scroll kar ke **"Add to Home Screen"** (**+**) select karein.
    
    *Iske baad yeh app aapke mobile par bilkul native app ki tarah open hogi.*
    """)

# User inputs: Only YouTube Link and Direct Video File Upload
video_url = st.text_input("🔗 Video Link Paste Karein (YouTube, etc.):", placeholder="https://www.youtube.com/watch?v=...")
uploaded_file = st.file_uploader("📁 Ya Direct Video File Upload Karein (MP4 / WebM)", type=["mp4", "webm", "mov", "mkv"])

st.write("") # Spacing

# --- 6. Analysis Trigger & Processing ---
if st.button("🔍 Video Analyze Karein", type="primary", use_container_width=True):
    api_key = get_backend_api_key()

    if not api_key:
        st.error(
            "⚙️ **System Configuration Missing**: Gemini API Key backend mein set nahi hai.\n\n"
            "Barah-e-karam `.streamlit/secrets.toml` file mein ya environment variable `GEMINI_API_KEY` configure karein."
        )
    elif not video_url and not uploaded_file:
        st.error("⚠️ Barah-e-karam video ka link paste karein ya direct file upload karein.")
    else:
        video_path = None
        gemini_file = None
        client = None
        timestamp = int(time.time())

        try:
            # Download or save video
            with st.spinner("⏳ Video download aur analyze ke liye prepare ho rahi hai..."):
                if uploaded_file:
                    ext = uploaded_file.name.split(".")[-1] if "." in uploaded_file.name else "mp4"
                    video_path = f"temp_upload_{timestamp}.{ext}"
                    with open(video_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                else:
                    video_path = download_video(
                        video_url.strip(),
                        output_template=f"temp_video_{timestamp}.%(ext)s"
                    )

            if not video_path or not os.path.exists(video_path):
                st.error("❌ Video file ready nahi ho saki.")
                st.stop()

            # Upload to Gemini & Poll Processing
            with st.spinner("🤖 Gemini video dekh aur sun raha hai (1-2 minute lag sakte hain)..."):
                client = genai.Client(api_key=api_key)
                gemini_file = client.files.upload(file=video_path)

                while gemini_file.state.name == "PROCESSING":
                    time.sleep(3)
                    gemini_file = client.files.get(name=gemini_file.name)

                if gemini_file.state.name == "FAILED":
                    st.error("❌ Gemini video processing fail ho gayi.")
                    st.stop()

                # Optimized prompt requiring Markdown Table format
                prompt = """
                Aap ek senior aur qabil Islamic Media Safety Analyst hain. Is video ke visual frames aur audio dialogue dono ka gehra aur tafseeli tajziya karein.
                Aapka maqsad Muslim waldain (parents) ko rehnumai dena hai ke yeh content bachon ke liye safe hai ya nahi.

                Apna jawab Roman Urdu mein dein aur is structure ko laazmi follow karein:

                ### 🎯 Khulasa (Executive Summary)
                - **Safe Age Group:** (Jaise: Safe for All, 7+, 12+, ya Bilkul Na Dikhayein)
                - **Overall Status:** (🟢 Safe / 🟡 Caution / 🔴 Warning)
                - **Aik Line Ka Faisla:** (Mukhtasir wazeh faisla)

                ### 📊 Tafseeli Tajziya (Analysis Table)
                Neeche diye gaye format ke mutabiq ek saaf aur mukammal Markdown Table banayein:

                | Category / Rule | Status (Safe/Warning) | Detailed Findings / Timestamp |
                | :--- | :--- | :--- |
                | **Satr & Modesty (Libas)** | 🟢 Safe ya 🟡 Caution ya 🔴 Warning | Characters (khaas tor par female figures/dolls) ka libas kaisa hai? Kya revealing, tight ya be-hijab hai? Masla ho to exact timestamp (e.g. 01:23) likhein. |
                | **Romance & Inappropriate Gestures** | 🟢 Safe ya 🟡 Caution ya 🔴 Warning | Pyar mohabbat, flirting, kissing, ya ghair-shari harkaat. Exact timestamps darj karein. |
                | **Zubaan & Akhlaq (Manners & Slang)** | 🟢 Safe ya 🟡 Caution ya 🔴 Warning | Bad-tameezi, gaaliyan, bad-zubani, waldain/teachers ki na-farmani, ya na-munasib alfaz. Exact timestamps darj karein. |
                | **Aqaid & Faith (Islamic Values)** | 🟢 Safe ya 🟡 Caution ya 🔴 Warning | Magic/jaadu, shirk, superstitious items, ya Islamic values ke khilaf koi tasawwur. Exact timestamps darj karein. |
                | **Tashaddud & Violence (Fear/Violence)** | 🟢 Safe ya 🟡 Caution ya 🔴 Warning | Be-ja cheekh-pukaar, violent acts, ya bachon ko darrane wale scenes. Exact timestamps darj karein. |

                ### 👨‍👩‍👧‍👦 Waldain Ke Liye Faisla (Actionable Parent Advice)
                - Parents ko kya karna chahiye? (Khatam karein, sath baith kar samjha kar dikhayein, ya be-fikr ho kar dekhne dein).
                - Bachon ko is video ke bare mein kya samjhana zaroori hai.
                """

                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[gemini_file, prompt]
                )

                st.success("✅ Tajziya Mukammal Ho Gaya!")
                st.markdown("---")
                st.markdown("### 📋 Media Safety Report")
                st.markdown(response.text)

        except Exception as e:
            st.error(f"❌ Masla pesh aaya: {e}")
            if not uploaded_file:
                st.info("💡 **Tip**: Agar YouTube link se issue aaye, to aap video ko directly browser se download kar ke upar 'Direct Video File Upload' option ke zariye bhi screen kar sakte hain.")

        finally:
            # Guaranteed cleanup of Gemini cloud file
            if gemini_file and client:
                try:
                    client.files.delete(name=gemini_file.name)
                except Exception:
                    pass

            # Guaranteed cleanup of local video
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception:
                    pass
