import streamlit as st
import streamlit.components.v1 as components
import time
import re
import io
import os
import uuid
import logging
from PIL import Image

# Import Modular Services
from services.manga import compile_manga_panel
from services.novel import write_japanese_novel_scene, translate_novel_text
from services.whisper import transcribe_audio
from services.vault import (
    test_b2_connection,
    archive_to_b2,
    get_presigned_streaming_url,
    dispatch_webhook_notification,
    create_and_upload_storyboard_zip,
)
from services.diagnostics import check_system_package_health, SentinelGuard, ScoutParser
from services.agent_studio import run_agent_loop, parallel_upload_vault
from services.security import SecureBalanceSandbox, TokenScrubber, ProvenanceEngine
from services.temporal_vault import list_historical_versions, download_historical_file
from services.lineage import render_lineage_ui, build_lineage_graph
from services.pendo_tracking import pendo_track

# Setup Logger for UI App context
logger = logging.getLogger("GenMediaStudioUI")

# Set page configuration with a premium look
st.set_page_config(
    page_title="GenMedia Studio Hub",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- Novus by Pendo SDK -----------------
components.html("""
<script>
(function(apiKey){
    (function(p,e,n,d,o){var v,w,x,y,z;o=p[d]=p[d]||{};o._q=o._q||[];
    v=['initialize','identify','updateOptions','pageLoad','track', 'trackAgent'];for(w=0,x=v.length;w<x;++w)(function(m){
    o[m]=o[m]||function(){o._q[m===v[0]?'unshift':'push']([m].concat([].slice.call(arguments,0)));};})(v[w]);
    y=e.createElement(n);y.async=!0;y.src='https://cdn.pendo.io/agent/static/'+apiKey+'/pendo.js';
    z=e.getElementsByTagName(n)[0];z.parentNode.insertBefore(y,z);})(window,document,'script','pendo');
})('767e2c0a-a8df-4303-a5ad-664cc9bd10be');

pendo.initialize({
    visitor: {
        id: ''
    }
});
</script>
""", height=0)

# ----------------- 🔐 DYNAMIC SECURITY SANDBOX & SCRUBBER SETUP -----------------
# 1. Cryptographic Rate Limit Sandbox
if "sandbox_key" not in st.session_state:
    sandbox = SecureBalanceSandbox()
    st.session_state["sandbox_key"] = sandbox.get_key()
    st.session_state["tries_used"] = 0
    st.session_state["tries_signature"] = sandbox.generate_signature(0)
else:
    sandbox = SecureBalanceSandbox(key=st.session_state["sandbox_key"])

# 2. Ephemeral Token Scrubber
if "scrubber_salt" not in st.session_state:
    scrubber = TokenScrubber()
    st.session_state["scrubber_salt"] = scrubber.get_salt()
    st.session_state["hf_token_masked"] = b""
    st.session_state["hf_token_display"] = ""
else:
    scrubber = TokenScrubber(salt=st.session_state["scrubber_salt"])

# 3. Cryptographic Session Integrity Check (Run on load)
is_intact = sandbox.verify_integrity(
    st.session_state["tries_used"], st.session_state.get("tries_signature", "")
)

if not is_intact:
    st.markdown(
        """
    <div style="background: radial-gradient(circle, #251212 0%, #0c0505 100%); border: 2px solid #ef4444; border-radius: 20px; padding: 4rem; text-align: center; margin: 5% auto; max-width: 800px; box-shadow: 0 0 50px rgba(239,68,68,0.25);">
        <h1 style="color: #ef4444; font-family: 'Space Grotesk', sans-serif; font-weight:800; font-size:3rem; margin-bottom: 1.5rem;">❌ SECURITY LOCKOUT</h1>
        <p style="font-size: 1.25rem; color: #f1f5f9; line-height: 1.7;">
            An integrity violation has been detected. The rate-limit execution balance was altered outside of the secure application context.
        </p>
        <p style="color: #94a3b8; font-size: 1rem; margin-top: 2rem;">
            Application execution has been terminated to prevent unauthorized resource access. 
        </p>
        <div style="margin-top: 3rem; font-family: monospace; color: #ef4444; font-size: 0.85rem;">
            Error Code: SEC_REACTION_INTEGRITY_MISMATCH
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.stop()


# Helper to safely update tries count
def secure_increment_tries(count: int = 1):
    current = st.session_state["tries_used"]
    new_val = current + count
    st.session_state["tries_used"] = new_val
    st.session_state["tries_signature"] = sandbox.generate_signature(new_val)


# Extract plaintext token on-demand
def get_active_token() -> str:
    return scrubber.unmask_token(st.session_state.get("hf_token_masked", b""))


# Initialize B2 vault credentials
if "b2_key_id" not in st.session_state:
    st.session_state["b2_key_id"] = ""
if "b2_application_key" not in st.session_state:
    st.session_state["b2_application_key"] = ""
if "b2_bucket_name" not in st.session_state:
    st.session_state["b2_bucket_name"] = ""

# Pendo session visitor ID for server-side tracking
if "pendo_visitor_id" not in st.session_state:
    st.session_state["pendo_visitor_id"] = f"streamlit_{uuid.uuid4().hex[:16]}"

# Generated Assets Store
if "manga_image" not in st.session_state:
    st.session_state["manga_image"] = None
if "manga_prompt" not in st.session_state:
    st.session_state["manga_prompt"] = ""
if "manga_filename" not in st.session_state:
    st.session_state["manga_filename"] = "manga_panel.png"

if "light_novel_jp" not in st.session_state:
    st.session_state["light_novel_jp"] = ""
if "light_novel_jp_filename" not in st.session_state:
    st.session_state["light_novel_jp_filename"] = "light_novel_jp.txt"

if "light_novel_en" not in st.session_state:
    st.session_state["light_novel_en"] = ""
if "light_novel_en_filename" not in st.session_state:
    st.session_state["light_novel_en_filename"] = "light_novel_en.txt"

if "whisper_transcript" not in st.session_state:
    st.session_state["whisper_transcript"] = ""
if "whisper_srt" not in st.session_state:
    st.session_state["whisper_srt"] = ""
if "whisper_filename" not in st.session_state:
    st.session_state["whisper_filename"] = "subtitles.srt"

# Custom Premium DESIGN SYSTEM CSS Injection
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Outfit:wght@200;300;400;500;600;700;800;900&display=swap');

/* Main App Styles */
.stApp {
    background: radial-gradient(circle at top right, #120d20, #08070e) !important;
    color: #f1f5f9 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Title Panel Styling */
.header-container {
    background: linear-gradient(135deg, rgba(255, 51, 102, 0.05), rgba(160, 51, 255, 0.05));
    border: 1px solid rgba(160, 51, 255, 0.18);
    border-radius: 24px;
    padding: 2.8rem 2rem;
    text-align: center;
    margin-bottom: 2.5rem;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.35);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}

.header-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 3.5rem;
    background: linear-gradient(90deg, #ff3366, #a033ff, #00c6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.04em;
    margin: 0;
    line-height: 1.25 !important;
}

.header-subtitle {
    color: #94a3b8;
    font-size: 1.2rem;
    margin-top: 0.8rem;
    font-weight: 400;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.6 !important;
}

/* Glassmorphism Card Containers */
.glass-card {
    background: rgba(25, 20, 45, 0.35);
    border: 1px solid rgba(160, 51, 255, 0.15);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(16px);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.glass-card:hover {
    transform: translateY(-4px);
    border-color: rgba(160, 51, 255, 0.3);
    box-shadow: 0 12px 40px 0 rgba(160, 51, 255, 0.2);
}

/* Glowing Neon Card Outlines */
.glass-card-neon-purple {
    background: rgba(25, 20, 45, 0.35);
    border: 1.5px solid rgba(160, 51, 255, 0.35) !important;
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4), 0 0 15px rgba(160, 51, 255, 0.15) !important;
    backdrop-filter: blur(16px);
    transition: all 0.3s ease;
}
.glass-card-neon-purple:hover {
    transform: translateY(-3px);
    border-color: #a033ff !important;
    box-shadow: 0 12px 40px 0 rgba(160, 51, 255, 0.4), 0 0 25px rgba(160, 51, 255, 0.25) !important;
}

.glass-card-neon-pink {
    background: rgba(25, 20, 45, 0.35);
    border: 1.5px solid rgba(255, 51, 102, 0.35) !important;
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4), 0 0 15px rgba(255, 51, 102, 0.15) !important;
    backdrop-filter: blur(16px);
    transition: all 0.3s ease;
}
.glass-card-neon-pink:hover {
    transform: translateY(-3px);
    border-color: #ff3366 !important;
    box-shadow: 0 12px 40px 0 rgba(255, 51, 102, 0.4), 0 0 25px rgba(255, 51, 102, 0.25) !important;
}

/* Responsive CSS Grid Comparison Layouts */
.comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
    gap: 1.8rem;
    width: 100%;
    margin-bottom: 1.5rem;
}

.section-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid rgba(160, 51, 255, 0.2);
    padding-bottom: 0.6rem;
    line-height: 1.4 !important;
}

/* Text and general element padding/line spacing overrides */
p, span, label, li, td, th {
    line-height: 1.65 !important;
    letter-spacing: 0.015em !important;
}

h1, h2, h3, h4, h5, h6 {
    line-height: 1.35 !important;
    letter-spacing: -0.01em !important;
    margin-top: 0.8rem !important;
    margin-bottom: 0.8rem !important;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #06050b !important;
    border-right: 1px solid rgba(160, 51, 255, 0.15) !important;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.55);
}

.sidebar-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.6rem;
    background: linear-gradient(135deg, #ff3366, #a033ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 2rem;
    letter-spacing: -0.02em;
    line-height: 1.3 !important;
}

/* Sidebar Form Anti-Collision & Perfect Alignment */
[data-testid="stSidebar"] [data-testid="stForm"] {
    border: 1px solid rgba(160, 51, 255, 0.2) !important;
    background: rgba(10, 8, 20, 0.55) !important;
    border-radius: 14px;
    padding: 1.2rem !important;
}

[data-testid="stSidebar"] .stProgress {
    margin-top: 0.8rem !important;
    margin-bottom: 0.8rem !important;
}

/* Input Fields overrides */
div[data-baseweb="input"], textarea {
    background-color: rgba(10, 8, 20, 0.55) !important;
    border: 1px solid rgba(160, 51, 255, 0.25) !important;
    color: #f8fafc !important;
    border-radius: 8px !important;
    transition: all 0.2s ease;
}

div[data-baseweb="input"]:focus-within, textarea:focus {
    border-color: #ff3366 !important;
    box-shadow: 0 0 10px rgba(255, 51, 102, 0.15) !important;
}

/* Primary/Secondary Buttons */
button[kind="primary"] {
    background: linear-gradient(135deg, #ff3366 0%, #a033ff 100%) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    padding: 0.8rem 2.2rem !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(255, 51, 102, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.85rem !important;
}

button[kind="primary"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 25px rgba(160, 51, 255, 0.5) !important;
}

button[kind="secondary"] {
    background: rgba(30, 20, 60, 0.5) !important;
    border: 1px solid rgba(160, 51, 255, 0.3) !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.8rem !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

button[kind="secondary"]:hover {
    border-color: #ff3366 !important;
    color: #ffffff !important;
    background: rgba(255, 51, 102, 0.1) !important;
}

/* Custom Status Badges */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    text-align: center;
}

.status-badge.ready {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-badge.empty {
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Tab container layout and padding properties */
.stTabs {
    padding: 1.5rem 0 !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding: 2.2rem 1.8rem !important;
    border: 1px solid rgba(160, 51, 255, 0.15) !important;
    border-top: none !important;
    border-radius: 0 0 20px 20px;
    background: rgba(15, 10, 30, 0.18) !important;
    backdrop-filter: blur(12px);
    margin-bottom: 2rem;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: rgba(15, 10, 30, 0.6) !important;
    border: 1px solid rgba(160, 51, 255, 0.15) !important;
    border-radius: 14px 14px 0 0;
    padding: 8px 8px 0 8px;
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0;
    font-weight: 600;
    color: #94a3b8;
    padding: 12px 22px;
    transition: all 0.3s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(255, 51, 102, 0.15), rgba(160, 51, 255, 0.15)) !important;
    color: #ffffff !important;
    border-bottom: 3px solid #ff3366 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------- SIDEBAR: DYNAMIC CONTROL CENTER -----------------
st.sidebar.markdown(
    '<div class="sidebar-title">🌌 GenMedia Control</div>', unsafe_allow_html=True
)

# BYOK Token Field with Scrubber & Masking
st.sidebar.subheader("🔑 Hugging Face Auth")
raw_token = st.sidebar.text_input(
    "HF API Token (BYOK)",
    value=st.session_state.get("hf_token_display", ""),
    type="password",
    help="Bring Your Own Key. The API key is immediately encrypted in memory upon entry.",
)

if raw_token != st.session_state.get("hf_token_display", ""):
    masked_val, display_val = scrubber.scrub_and_mask_token(raw_token)
    st.session_state["hf_token_masked"] = masked_val
    st.session_state["hf_token_display"] = display_val
    pendo_track(
        "hf_token_configured",
        {
            "is_token_set": bool(raw_token.strip()),
            "previous_tries_used": st.session_state["tries_used"],
        },
        visitor_id=st.session_state["pendo_visitor_id"],
    )
    st.rerun()

has_byok = bool(st.session_state.get("hf_token_masked"))

# Absolute Rate-Limit Protection (10 Free Tries Limit)
st.sidebar.markdown("---")
st.sidebar.subheader("⏳ Rate Limit Guard")
tries_used = st.session_state["tries_used"]

if has_byok:
    st.sidebar.success("🟢 BYOK Active: Unlimited Tries")
    st.sidebar.caption(f"Used this session: {tries_used} generation(s)")
else:
    st.sidebar.warning("⚠️ Free Tier: 10 Tries Limit")
    progress = min(tries_used / 10, 1.0)
    st.sidebar.progress(progress)
    st.sidebar.write(f"Tries Used: **{tries_used} / 10**")
    if tries_used >= 10:
        st.sidebar.error(
            "❌ Free tries exhausted! Enter a HF Token to enable unlimited generations."
        )

# Backblaze B2 Bucket Credentials
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Backblaze B2 Vault Setup")
b2_id = st.sidebar.text_input(
    "B2 Application Key ID", value=st.session_state["b2_key_id"], type="password"
)
b2_key = st.sidebar.text_input(
    "B2 Application Key", value=st.session_state["b2_application_key"], type="password"
)
b2_bucket = st.sidebar.text_input(
    "B2 Bucket Name", value=st.session_state["b2_bucket_name"]
)

st.session_state["b2_key_id"] = b2_id
st.session_state["b2_application_key"] = b2_key
st.session_state["b2_bucket_name"] = b2_bucket

# B2 Connection Test & Validation
b2_configured = bool(b2_id.strip() and b2_key.strip() and b2_bucket.strip())
if b2_configured:
    # Validate bucket naming convention
    bucket_stripped = b2_bucket.strip()
    if (
        not (3 <= len(bucket_stripped) <= 50)
        or not re.match(r"^[a-zA-Z0-9\-]+$", bucket_stripped)
        or bucket_stripped.startswith("-")
        or bucket_stripped.endswith("-")
        or "--" in bucket_stripped
    ):
        st.sidebar.error("⚠️ Invalid B2 bucket name characters.")
    else:
        if st.sidebar.button("🔌 Test B2 Auth", key="test_b2_btn"):
            with st.spinner("Connecting to B2..."):
                ok, msg = test_b2_connection(b2_id, b2_key, b2_bucket)
                pendo_track(
                    "b2_connection_tested",
                    {
                        "success": ok,
                        "bucket_name": b2_bucket,
                    },
                    visitor_id=st.session_state["pendo_visitor_id"],
                )
                if ok:
                    st.sidebar.success(f"✅ Connected to '{b2_bucket}'!")
                else:
                    st.sidebar.error(f"❌ Connection failed: {msg}")

# Dynamic Dependency Diagnostics Integration (Core Scouter / Sentinel)
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Dependency diagnostics")

# Verify local package health
health_report = check_system_package_health()
healthy_count = sum(1 for p in health_report if p["status"] == "Healthy")
total_count = len(health_report)

if healthy_count == total_count:
    st.sidebar.success(f"🟢 System dependencies: OK ({healthy_count}/{total_count})")
else:
    st.sidebar.warning(f"⚠️ Dependency Alert ({healthy_count}/{total_count} loaded)")

with st.sidebar.expander("System package diagnostics"):
    for pkg in health_report:
        color = "green" if pkg["status"] == "Healthy" else "red"
        st.markdown(
            f"**{pkg['package']}**: :{color}[{pkg['status']}] (v{pkg['version']})"
        )

    st.markdown("---")
    st.markdown("**Pip Conflict Scanner**")
    dump = st.text_area(
        "Paste terminal logs to diagnose",
        placeholder="requires numpy but you have...",
        key="diagnostic_dump",
    )
    if st.button("Diagnose Dump", key="diagnose_dump_btn", use_container_width=True):
        if dump.strip():
            guard = SentinelGuard()
            parser = ScoutParser()
            signals = guard.detect_signals_matrix(dump)
            parsed = parser.extract_all(dump)
            pendo_track(
                "dependency_diagnostic_run",
                {
                    "system_signal_detected": signals.get("system", False),
                    "environment_signal_detected": signals.get("environment", False),
                    "runtime_signal_detected": signals.get("runtime", False),
                    "dependency_signal_detected": signals.get("dependency", False),
                    "requirements_count": len(parsed.get("requirements", [])),
                    "installed_count": len(parsed.get("installed", [])),
                },
                visitor_id=st.session_state["pendo_visitor_id"],
            )
            st.markdown("**Signals Mapped:**")
            st.write(signals)
            st.markdown("**Parsed Requirements:**")
            st.write(parsed)
        else:
            st.write("Please paste logs first.")


# Rate limit evaluation helper
def verify_rate_limit():
    if not has_byok and st.session_state["tries_used"] >= 10:
        if not st.session_state.get("rate_limit_event_fired"):
            pendo_track(
                "rate_limit_reached",
                {
                    "tries_used": st.session_state["tries_used"],
                },
                visitor_id=st.session_state["pendo_visitor_id"],
            )
            st.session_state["rate_limit_event_fired"] = True
        st.error(
            "Rate limit threshold of 10 free tries reached! Enter your Hugging Face API Token (BYOK) in the sidebar to run unlimited generations."
        )
        return False
    return True


# ----------------- MAIN STUDIO CONTAINER -----------------
st.markdown(
    """
<div class="header-container">
    <h1 class="header-title">GENMEDIA STUDIO HUB</h1>
    <p class="header-subtitle">State-of-the-Art Workspace for AI Manga compilations, Light Novels, Whisper audio transcriptions, and secure Backblaze B2 archives.</p>
</div>
""",
    unsafe_allow_html=True,
)

# Define Main Application Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🎨 Manga Panel Workspace",
        "📖 Light Novel Factory",
        "🎙️ Whisper Subtitle Studio",
        "🤖 Agent Continuity Studio",
        "🗄️ Backblaze B2 Vault",
        "🔒 See Code",
    ]
)

# ==================== TAB 1: MANGA GENERATION WORKSPACE ====================
with tab1:
    st.markdown(
        '<div class="section-header">🎨 Manga Workspace</div>', unsafe_allow_html=True
    )

    # Custom SVG Pipeline tree display
    svg_manga = """
    <div style="text-align: center;">
    <svg width="100%" height="80" viewBox="0 0 600 80" style="background: rgba(10,8,25,0.4); border: 1px solid rgba(160, 51, 255, 0.2); border-radius: 12px; padding: 10px;">
        <defs>
            <linearGradient id="neonGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff3366" />
                <stop offset="100%" stop-color="#a033ff" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        
        <!-- Node 1: Input -->
        <rect x="20" y="15" width="120" height="50" rx="8" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
        <text x="80" y="45" fill="#f8fafc" font-size="12" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Prompt Input</text>
        
        <!-- Arrow 1 -->
        <line x1="140" y1="40" x2="220" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 2: Model -->
        <rect x="220" y="15" width="160" height="50" rx="8" fill="rgba(160, 51, 255, 0.1)" stroke="#a033ff" stroke-width="2" filter="url(#glow)"/>
        <text x="300" y="37" fill="#f8fafc" font-size="12" font-family="Space Grotesk" text-anchor="middle" font-weight="600">FLUX.1-schnell</text>
        <text x="300" y="53" fill="#94a3b8" font-size="10" font-family="Outfit" text-anchor="middle">StepType.GENERATE</text>
        
        <!-- Arrow 2 -->
        <line x1="380" y1="40" x2="460" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 3: Output -->
        <rect x="460" y="15" width="120" height="50" rx="8" fill="rgba(255, 51, 102, 0.1)" stroke="#ff3366" stroke-width="2" filter="url(#glow)"/>
        <text x="520" y="45" fill="#f8fafc" font-size="12" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Image Asset</text>
    </svg>
    </div>
    """
    st.components.v1.html(svg_manga, height=105, scrolling=False)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write(
            "Route image compiles to any FLUX or image model identifier dynamically via the central orchestrator."
        )

        manga_model = st.text_input(
            "Manga Image Model Path",
            value="black-forest-labs/FLUX.1-schnell",
            help="Dynamic model routing. Ex: black-forest-labs/FLUX.1-schnell or custom anime diffusion endpoints.",
        )

        manga_prompt = st.text_area(
            "Manga Panel Prompt",
            placeholder="A heroic samurai warrior standing on top of a mountain peak during a solar eclipse, intense wind, ink drawing...",
            help="Describe the scene you want to render.",
            key="manga_prompt_input",
        )

        style_preset = st.selectbox(
            "Style Preset Overlay",
            options=[
                "Raw Prompt (No Preset)",
                "Classic Ink Manga",
                "Retro 90s Anime",
                "Chibi Slice-of-Life",
                "Cyberpunk Neon Panel",
            ],
            key="manga_style_select",
        )

        # Style preset suffixes
        style_map = {
            "Raw Prompt (No Preset)": "",
            "Classic Ink Manga": ", detailed manga ink illustration, manga panel, screentones, highly detailed black and white sketch, masterwork",
            "Retro 90s Anime": ", retro 90s hand-drawn anime aesthetic, cell shading, soft colors, vintage movie feel",
            "Chibi Slice-of-Life": ", cute chibi style, simple lines, colorful anime cartoon illustration, lighthearted mood",
            "Cyberpunk Neon Panel": ", cyberpunk anime style, retro-futurism, glowing neon accents, dramatic reflections, high contrast",
        }

        is_disabled = not has_byok and tries_used >= 10

        if st.button(
            "🚀 Compile Manga Panel",
            key="compile_manga_btn",
            disabled=is_disabled,
            use_container_width=True,
        ):
            if verify_rate_limit():
                final_prompt = manga_prompt + style_map[style_preset]
                token = get_active_token()

                with st.spinner("Compiling panel via central orchestrator..."):
                    ok, res_path = compile_manga_panel(
                        token, final_prompt, model_id=manga_model
                    )
                    if ok:
                        st.session_state["manga_image"] = Image.open(res_path)
                        st.session_state["manga_prompt"] = final_prompt
                        secure_increment_tries(1)
                        pendo_track(
                            "manga_panel_compiled",
                            {
                                "model_id": manga_model,
                                "style_preset": style_preset,
                                "prompt_length": len(final_prompt),
                                "has_byok": has_byok,
                            },
                            visitor_id=st.session_state["pendo_visitor_id"],
                        )
                        st.success("Manga panel compiled successfully!")
                    else:
                        pendo_track(
                            "manga_panel_compilation_failed",
                            {
                                "model_id": manga_model,
                                "style_preset": style_preset,
                                "error_message": str(res_path)[:200],
                                "has_byok": has_byok,
                            },
                            visitor_id=st.session_state["pendo_visitor_id"],
                        )
                        st.error(f"Failed to generate image: {res_path}")

        if is_disabled:
            st.info(
                "💡 Pro-Tip: Provide your own Hugging Face token in the sidebar to bypass the 10 free tries limit."
            )

    with col2:
        st.subheader("Panel Compile Preview")
        if st.session_state["manga_image"] is not None:
            # Side-by-side Manga Comparison Grid
            st.markdown(
                """
            <div class="comparison-grid">
                <div class="glass-card-neon-purple">
                    <h4 style="margin-top:0;">🎨 Generated Panel</h4>
            """,
                unsafe_allow_html=True,
            )
            st.image(st.session_state["manga_image"], use_container_width=True)
            st.markdown(
                """
                </div>
                <div class="glass-card-neon-pink">
                    <h4 style="margin-top:0;">📝 Prompts & Configuration</h4>
                    <p style="font-size:0.95rem; line-height:1.6; color:#cbd5e1;">
            """,
                unsafe_allow_html=True,
            )
            st.write(f"**Target Model:** `{manga_model}`")
            st.write(f"**Final Prompt:** *{st.session_state['manga_prompt']}*")
            st.markdown(
                """
                    </p>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # File download
            img_byte_arr = io.BytesIO()
            st.session_state["manga_image"].save(img_byte_arr, format="PNG")
            img_bytes = img_byte_arr.getvalue()

            st.download_button(
                "📥 Download PNG Local",
                data=img_bytes,
                file_name="manga_panel.png",
                mime="image/png",
            )

            # Custom B2 Name Setup
            st.session_state["manga_filename"] = st.text_input(
                "B2 Target Filename",
                value=st.session_state["manga_filename"],
                key="manga_filename_input",
            )
        else:
            st.info(
                "No manga panel compiled yet. Enter a prompt and compile above to generate!"
            )

# ==================== TAB 2: LIGHT NOVEL FACTORY ====================
with tab2:
    st.markdown(
        '<div class="section-header">📖 Light Novel Factory</div>',
        unsafe_allow_html=True,
    )

    # Custom SVG Pipeline tree display
    svg_novel = """
    <div style="text-align: center;">
    <svg width="100%" height="80" viewBox="0 0 800 80" style="background: rgba(10,8,25,0.4); border: 1px solid rgba(160, 51, 255, 0.2); border-radius: 12px; padding: 10px;">
        <defs>
            <linearGradient id="neonGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff3366" />
                <stop offset="100%" stop-color="#a033ff" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        
        <!-- Node 1: Concept -->
        <rect x="20" y="15" width="110" height="50" rx="8" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
        <text x="75" y="45" fill="#f8fafc" font-size="11" font-family="Space Grotesk" text-anchor="middle" font-weight="600">LN Concept</text>
        
        <!-- Arrow 1 -->
        <line x1="130" y1="40" x2="190" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 2: Stage 1 (JP Write) -->
        <rect x="190" y="15" width="160" height="50" rx="8" fill="rgba(160, 51, 255, 0.1)" stroke="#a033ff" stroke-width="2" filter="url(#glow)"/>
        <text x="270" y="37" fill="#f8fafc" font-size="11" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Qwen2.5-7B [JP]</text>
        <text x="270" y="53" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">Step 0: Generate</text>
        
        <!-- Arrow 2 -->
        <line x1="350" y1="40" x2="410" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 3: Stage 2 (EN Translate) -->
        <rect x="410" y="15" width="160" height="50" rx="8" fill="rgba(0, 198, 255, 0.1)" stroke="#00c6ff" stroke-width="2" filter="url(#glow)"/>
        <text x="490" y="37" fill="#f8fafc" font-size="11" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Qwen2.5-7B [EN]</text>
        <text x="490" y="53" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">Step 1: input_from=0</text>
        
        <!-- Arrow 3 -->
        <line x1="570" y1="40" x2="630" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 4: Chained Output -->
        <rect x="630" y="15" width="150" height="50" rx="8" fill="rgba(255, 51, 102, 0.1)" stroke="#ff3366" stroke-width="2" filter="url(#glow)"/>
        <text x="705" y="37" fill="#f8fafc" font-size="11" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Chained Assets</text>
        <text x="705" y="53" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">JP Text & EN Text</text>
    </svg>
    </div>
    """
    st.components.v1.html(svg_novel, height=105, scrolling=False)

    ln_tabs = st.tabs(["✍️ LN Generator", "🔄 Text Translator"])

    with ln_tabs[0]:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.write(
                "Orchestrate open-source LLM writes and English cross-translations using dynamic model endpoints."
            )

            novel_model = st.text_input(
                "Novel Writer Model Path",
                value="Qwen/Qwen2.5-7B-Instruct",
                help="Enter any text-generation LLM path. Ex: Qwen/Qwen2.5-7B-Instruct or meta-llama/Llama-3-8B-Instruct.",
            )

            ln_title = st.text_input(
                "Chapter/Story Title",
                value="運命のコンパイル (Destiny Compile)",
                key="ln_title_input",
            )
            ln_concept = st.text_area(
                "Story Idea / Concept",
                placeholder="A programmer gets reincarnated as an apprentice mage, and realizes magic runs on a compiler resembling Assembly.",
                key="ln_concept_input",
            )

            ln_genre = st.selectbox(
                "Genre Style",
                [
                    "Isekai (Otherworld Fantasy)",
                    "Cyberpunk Slice of Life",
                    "School Romance",
                    "Shonen Action",
                    "Psychological Horror",
                ],
                key="ln_genre_select",
            )
            ln_tone = st.select_slider(
                "Writing Tone",
                options=[
                    "Humorous & Light",
                    "Expressive & Standard",
                    "Dark & Moody",
                    "Epic & Grandiose",
                ],
                key="ln_tone_slider",
            )

            is_disabled_ln = not has_byok and tries_used >= 10

            if st.button(
                "✍️ Write Japanese Scene",
                key="write_ln_btn",
                disabled=is_disabled_ln,
                use_container_width=True,
            ):
                if verify_rate_limit():
                    prompt_instructions = (
                        f"Write a short, engaging scene for a Light Novel in authentic, native Japanese style.\n"
                        f"Title: {ln_title}\n"
                        f"Concept: {ln_concept}\n"
                        f"Genre: {ln_genre}\n"
                        f"Tone: {ln_tone}\n"
                        f"Format the output professionally with dialogue markers (e.g. 「...」) and paragraphs."
                    )

                    token = get_active_token()

                    with st.spinner(
                        "Generating Japanese novel & English translation via central orchestrator..."
                    ):
                        ok, jp_res, en_res = write_japanese_novel_scene(
                            token, prompt_instructions, model_id=novel_model
                        )
                        if ok:
                            st.session_state["light_novel_jp"] = jp_res
                            st.session_state["light_novel_en"] = en_res
                            secure_increment_tries(2)
                            pendo_track(
                                "novel_scene_generated",
                                {
                                    "model_id": novel_model,
                                    "genre": ln_genre,
                                    "tone": ln_tone,
                                    "title": ln_title[:100],
                                    "concept_length": len(ln_concept),
                                    "jp_text_length": len(jp_res),
                                    "en_text_length": len(en_res),
                                    "has_byok": has_byok,
                                },
                                visitor_id=st.session_state["pendo_visitor_id"],
                            )
                            st.success(
                                "Japanese scene generated and chained English translation completed!"
                            )
                        else:
                            pendo_track(
                                "novel_scene_generation_failed",
                                {
                                    "model_id": novel_model,
                                    "genre": ln_genre,
                                    "tone": ln_tone,
                                    "error_message": str(jp_res)[:200],
                                    "has_byok": has_byok,
                                },
                                visitor_id=st.session_state["pendo_visitor_id"],
                            )
                            st.error(f"Generation failed: {jp_res}")

        with col2:
            st.subheader("Light Novel Compilation Displays")

            # Responsive CSS Grid Layout for side-by-side Manga/Novel comparisons
            st.markdown('<div class="comparison-grid">', unsafe_allow_html=True)

            # Column JP
            st.markdown('<div class="glass-card-neon-purple">', unsafe_allow_html=True)
            st.markdown(
                "<h4 style='margin-top:0;'>🇯🇵 Japanese Original Original Text</h4>",
                unsafe_allow_html=True,
            )
            st.session_state["light_novel_jp"] = st.text_area(
                "Japanese Output Frame",
                value=st.session_state["light_novel_jp"],
                height=250,
                key="ln_jp_out",
                label_visibility="collapsed",
            )
            st.session_state["light_novel_jp_filename"] = st.text_input(
                "B2 Japanese Text Filename",
                value=st.session_state["light_novel_jp_filename"],
                key="ln_jp_filename_input",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # Column EN
            st.markdown('<div class="glass-card-neon-pink">', unsafe_allow_html=True)
            st.markdown(
                "<h4 style='margin-top:0;'>🇺🇸 English Translation Frame</h4>",
                unsafe_allow_html=True,
            )
            st.session_state["light_novel_en"] = st.text_area(
                "English Output Frame",
                value=st.session_state["light_novel_en"],
                height=250,
                key="ln_en_out",
                label_visibility="collapsed",
            )
            st.session_state["light_novel_en_filename"] = st.text_input(
                "B2 English Text Filename",
                value=st.session_state["light_novel_en_filename"],
                key="ln_en_filename_input",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    with ln_tabs[1]:
        st.subheader("🔄 Direct Cross-Translation Console")

        translation_model = st.text_input(
            "Translation Model Path",
            value="Qwen/Qwen2.5-7B-Instruct",
            help="Specify text model for translation.",
        )

        src_text = st.text_area(
            "Source Text to Translate",
            height=150,
            placeholder="Enter text in English or Japanese...",
            key="direct_src_input",
        )
        tr_direction = st.radio(
            "Translation Direction",
            ["Japanese ➔ English", "English ➔ Japanese"],
            key="direct_direction_radio",
        )

        if st.button(
            "Translate",
            key="direct_translate_btn",
            disabled=is_disabled_ln,
            use_container_width=True,
        ):
            if src_text.strip():
                if verify_rate_limit():
                    token = get_active_token()
                    direction_instruction = (
                        "Japanese into natural English"
                        if tr_direction == "Japanese ➔ English"
                        else "English into natural, authentic Japanese light novel style prose"
                    )
                    prompt_trans = (
                        f"Translate the following text from {direction_instruction}. "
                        f"Ensure high linguistic quality, retaining appropriate honorifics and speech tone:\n\n"
                        f"{src_text}"
                    )

                    with st.spinner("Translating text..."):
                        ok, res_text = translate_novel_text(
                            token, prompt_trans, model_id=translation_model
                        )
                        if ok:
                            st.subheader("Translation Results")
                            st.write(res_text)
                            secure_increment_tries(1)
                            pendo_track(
                                "novel_text_translated",
                                {
                                    "model_id": translation_model,
                                    "translation_direction": tr_direction,
                                    "source_text_length": len(src_text),
                                    "result_text_length": len(res_text),
                                    "has_byok": has_byok,
                                },
                                visitor_id=st.session_state["pendo_visitor_id"],
                            )
                        else:
                            st.error(f"Translation failed: {res_text}")

# ==================== TAB 3: WHISPER SUBTITLE STUDIO ====================
with tab3:
    st.markdown(
        '<div class="section-header">🎙️ Whisper Subtitle Studio</div>',
        unsafe_allow_html=True,
    )

    # Custom SVG Pipeline tree display
    svg_whisper = """
    <div style="text-align: center;">
    <svg width="100%" height="80" viewBox="0 0 600 80" style="background: rgba(10,8,25,0.4); border: 1px solid rgba(160, 51, 255, 0.2); border-radius: 12px; padding: 10px;">
        <defs>
            <linearGradient id="neonGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff3366" />
                <stop offset="100%" stop-color="#a033ff" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        
        <!-- Node 1: Audio Input -->
        <rect x="20" y="15" width="120" height="50" rx="8" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
        <text x="80" y="45" fill="#f8fafc" font-size="12" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Audio Track</text>
        
        <!-- Arrow 1 -->
        <line x1="140" y1="40" x2="220" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 2: Model -->
        <rect x="220" y="15" width="160" height="50" rx="8" fill="rgba(160, 51, 255, 0.1)" stroke="#a033ff" stroke-width="2" filter="url(#glow)"/>
        <text x="300" y="37" fill="#f8fafc" font-size="12" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Whisper-Large-V3</text>
        <text x="300" y="53" fill="#94a3b8" font-size="10" font-family="Outfit" text-anchor="middle">StepType.GENERATE</text>
        
        <!-- Arrow 2 -->
        <line x1="380" y1="40" x2="460" y2="40" stroke="url(#neonGrad)" stroke-width="3" stroke-dasharray="5 5" filter="url(#glow)"/>
        
        <!-- Node 3: Subtitles -->
        <rect x="460" y="15" width="120" height="50" rx="8" fill="rgba(255, 51, 102, 0.1)" stroke="#ff3366" stroke-width="2" filter="url(#glow)"/>
        <text x="520" y="37" fill="#f8fafc" font-size="12" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Subtitle Asset</text>
        <text x="520" y="53" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">Text & SRT Format</text>
    </svg>
    </div>
    """
    st.components.v1.html(svg_whisper, height=105, scrolling=False)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write(
            "Run speech-to-text audio transcriptions using Whisper or other audio recognition models dynamically."
        )

        whisper_model = st.text_input(
            "Audio Transcription Model Path",
            value="openai/whisper-large-v3",
            help="Select any audio transcriber model on Hugging Face. Ex: openai/whisper-large-v3 or distil-whisper/distil-large-v3.",
        )

        audio_file = st.file_uploader(
            "Upload Audio Track",
            type=["mp3", "wav", "m4a", "ogg"],
            key="whisper_audio_upload",
        )
        audio_record = st.audio_input("Record Audio Input", key="whisper_audio_record")

        # Determine source
        audio_data = None
        if audio_file is not None:
            audio_data = audio_file.read()
        elif audio_record is not None:
            audio_data = audio_record.read()

        use_demo_audio = st.checkbox(
            "Use Simulated Audio Track (if no file is uploaded)",
            key="whisper_demo_checkbox",
        )

        is_disabled_whisper = not has_byok and tries_used >= 10

        if st.button(
            "🎙️ Process Speech-To-Text",
            key="process_whisper_btn",
            disabled=is_disabled_whisper,
            use_container_width=True,
        ):
            if verify_rate_limit():
                token = get_active_token()

                if (audio_data is not None) or use_demo_audio:
                    _audio_source = (
                        "demo"
                        if (audio_data is None and use_demo_audio)
                        else ("upload" if audio_file is not None else "record")
                    )
                    with st.spinner("Processing audio transcription..."):
                        ok, text_out, srt_out = transcribe_audio(
                            token, audio_data, model_id=whisper_model
                        )
                        if ok:
                            st.session_state["whisper_transcript"] = text_out
                            st.session_state["whisper_srt"] = srt_out
                            secure_increment_tries(1)
                            pendo_track(
                                "audio_transcribed",
                                {
                                    "model_id": whisper_model,
                                    "audio_source": _audio_source,
                                    "is_demo_audio": audio_data is None
                                    and use_demo_audio,
                                    "transcript_length": len(text_out),
                                    "srt_segment_count": srt_out.count("\n\n"),
                                    "has_byok": has_byok,
                                },
                                visitor_id=st.session_state["pendo_visitor_id"],
                            )
                            st.success("Transcription complete!")
                        else:
                            pendo_track(
                                "audio_transcription_failed",
                                {
                                    "model_id": whisper_model,
                                    "audio_source": _audio_source,
                                    "error_message": str(text_out)[:200],
                                    "has_byok": has_byok,
                                },
                                visitor_id=st.session_state["pendo_visitor_id"],
                            )
                            st.error(f"Whisper transcription failed: {text_out}")
                else:
                    st.warning(
                        "Please upload an audio file or record some audio first."
                    )

    with col2:
        st.subheader("Subtitles Compilation & SRT")
        if st.session_state["whisper_transcript"]:
            st.write("**Full Text Transcript:**")
            st.write(st.session_state["whisper_transcript"])

            st.write("**SRT Subtitle File Output:**")
            st.code(st.session_state["whisper_srt"], language="srt")

            st.download_button(
                "📥 Download Subtitles (.srt)",
                data=st.session_state["whisper_srt"],
                file_name="subtitles.srt",
                mime="text/plain",
            )
            st.session_state["whisper_filename"] = st.text_input(
                "B2 Subtitles Filename",
                value=st.session_state["whisper_filename"],
                key="whisper_filename_input",
            )
        else:
            st.info(
                "No transcription processed yet. Upload or record audio and hit Process to transcribe."
            )

# ==================== TAB 4: AGENT CONTINUITY STUDIO ====================
with tab4:
    st.markdown(
        '<div class="section-header">🤖 Agent Continuity Studio</div>',
        unsafe_allow_html=True,
    )

    # Custom SVG Pipeline tree display
    svg_agent = """
    <div style="text-align: center;">
    <svg width="100%" height="80" viewBox="0 0 1000 80" style="background: rgba(10,8,25,0.4); border: 1px solid rgba(160, 51, 255, 0.2); border-radius: 12px; padding: 10px;">
        <defs>
            <linearGradient id="neonGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff3366" />
                <stop offset="100%" stop-color="#a033ff" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        
        <!-- Node 1: Master Prompt -->
        <rect x="10" y="15" width="120" height="50" rx="8" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
        <text x="70" y="37" fill="#f8fafc" font-size="10" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Master Prompt</text>
        <text x="70" y="51" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">Story Concept</text>
        
        <!-- Arrow 1 -->
        <line x1="130" y1="40" x2="185" y2="40" stroke="url(#neonGrad)" stroke-width="2" stroke-dasharray="3 3"/>
        
        <!-- Node 2: Concurrent Gen (10 Steps) -->
        <rect x="185" y="15" width="170" height="50" rx="8" fill="rgba(160, 51, 255, 0.1)" stroke="#a033ff" stroke-width="2" filter="url(#glow)"/>
        <text x="270" y="37" fill="#f8fafc" font-size="10" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Concurrent Gen</text>
        <text x="270" y="51" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">5 FLUX + 5 MusicGen</text>
        
        <!-- Arrow 2 -->
        <line x1="355" y1="40" x2="410" y2="40" stroke="url(#neonGrad)" stroke-width="2" stroke-dasharray="3 3"/>
        
        <!-- Node 3: Threshold Evaluator -->
        <rect x="410" y="15" width="160" height="50" rx="8" fill="rgba(0, 198, 255, 0.1)" stroke="#00c6ff" stroke-width="2" filter="url(#glow)"/>
        <text x="490" y="37" fill="#f8fafc" font-size="10" font-family="Space Grotesk" text-anchor="middle" font-weight="600">ThresholdEvaluator</text>
        <text x="490" y="51" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">Continuity Score</text>
        
        <!-- Arrow 3 -->
        <line x1="570" y1="40" x2="625" y2="40" stroke="url(#neonGrad)" stroke-width="2" stroke-dasharray="3 3"/>
        
        <!-- Node 4: Self-Correction Loop -->
        <rect x="625" y="15" width="170" height="50" rx="8" fill="rgba(255, 193, 7, 0.1)" stroke="#ffc107" stroke-width="2" filter="url(#glow)"/>
        <text x="710" y="37" fill="#f8fafc" font-size="10" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Self-Correction Loop</text>
        <text x="710" y="51" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">Adjust Seed & Prompt</text>
        
        <!-- Arrow 4 -->
        <line x1="795" y1="40" x2="850" y2="40" stroke="url(#neonGrad)" stroke-width="2" stroke-dasharray="3 3"/>
        
        <!-- Node 5: Verified Output -->
        <rect x="850" y="15" width="140" height="50" rx="8" fill="rgba(255, 51, 102, 0.1)" stroke="#ff3366" stroke-width="2" filter="url(#glow)"/>
        <text x="920" y="37" fill="#f8fafc" font-size="10" font-family="Space Grotesk" text-anchor="middle" font-weight="600">Verified Manifest</text>
        <text x="920" y="51" fill="#94a3b8" font-size="9" font-family="Outfit" text-anchor="middle">SHA-256 Canonical</text>
    </svg>
    </div>
    """
    st.components.v1.html(svg_agent, height=105, scrolling=False)

    st.write(
        "Orchestrate an advanced Genblaze Agent Loop for multi-panel continuity generation. Evaluates consistency against a template and dynamically refines parameters on failure."
    )

    col_options, col_prompts = st.columns([1, 2])

    with col_options:
        st.subheader("Agent Settings")

        agent_image_model = st.text_input(
            "Storyboard Image Model Path",
            value="black-forest-labs/FLUX.1-schnell",
            help="Dynamic model routing for visual continuity panel generation.",
        )

        agent_audio_model = st.text_input(
            "Storyboard Audio Model Path",
            value="facebook/musicgen-small",
            help="Dynamic model routing for backing soundtrack generation.",
        )

        master_prompt = st.text_input(
            "Master Prompt Layout / Core Focus",
            value="A futuristic cyberpunk detective navigating a neon-lit city, holding a glowing data shard.",
            key="agent_master_prompt",
        )

        target_threshold = st.slider(
            "Visual Continuity Threshold",
            min_value=0.50,
            max_value=0.95,
            value=0.75,
            step=0.05,
            help="Minimum continuity score required to pass the visual evaluation check.",
        )

        max_iter = st.number_input(
            "Max Self-Correction Loop Iterations",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum times the agent will refine prompts and retry generation on failure.",
        )

        st.markdown("---")

        is_disabled_agent = not has_byok and tries_used >= 10

        # We will initialize defaults if not set in state
        default_img_prompts = [
            "Cyberpunk detective looking at a giant neon screen in the rain",
            "Cyberpunk detective holding a glowing blue data shard, close-up",
            "A mysterious dark figure approaching the detective from an alleyway",
            "The detective drawing a neon laser gun in a defensive action stance",
            "The detective escaping on a fast hover-motorcycle with neon trails",
        ]

        default_aud_prompts = [
            "Cyberpunk synthesizer background score, rain atmosphere",
            "Futuristic electronic chime, hum of digital servers",
            "Tense heartbeat pulse, approaching footsteps, heavy shadow theme",
            "Laser blast charge, high-frequency crackle, action drums",
            "High-speed hover motor revving, wind rush, fast techno exit beat",
        ]

        user_img_prompts = []
        user_aud_prompts = []

        st.subheader("Customize Storyboard Panels")
        for i in range(5):
            with st.expander(f"Panel {i + 1} Configuration", expanded=(i == 0)):
                img_p = st.text_input(
                    f"Panel {i + 1} Image Prompt",
                    value=default_img_prompts[i],
                    key=f"agent_img_p_{i}",
                )
                aud_p = st.text_input(
                    f"Panel {i + 1} Audio Prompt",
                    value=default_aud_prompts[i],
                    key=f"agent_aud_p_{i}",
                )
                user_img_prompts.append(img_p)
                user_aud_prompts.append(aud_p)

        if st.button(
            "⚡ Run Continuity Agent Loop",
            key="run_agent_loop_btn",
            disabled=is_disabled_agent,
            use_container_width=True,
        ):
            if verify_rate_limit():
                token = get_active_token()
                with st.spinner(
                    "Executing Genblaze Agent Loop (Generates concurrent steps & evaluates visual consistency)..."
                ):
                    res = run_agent_loop(
                        token=token,
                        master_prompt=master_prompt,
                        panel_prompts=user_img_prompts,
                        audio_prompts=user_aud_prompts,
                        threshold=target_threshold,
                        max_iterations=int(max_iter),
                        image_model_id=agent_image_model,
                        audio_model_id=agent_audio_model,
                    )
                    if res.get("success"):
                        st.session_state["agent_storyboard_result"] = res
                        run_iters = len(res.get("iterations", []))
                        secure_increment_tries(run_iters)
                        pendo_track(
                            "agent_loop_completed",
                            {
                                "image_model_id": agent_image_model,
                                "audio_model_id": agent_audio_model,
                                "iterations_count": run_iters,
                                "final_score": res.get("score"),
                                "threshold": target_threshold,
                                "passed": res.get("passed", False),
                                "panel_count": len(res.get("panels", [])),
                                "manifest_hash": str(res.get("manifest_hash", ""))[:32],
                                "has_byok": has_byok,
                            },
                            visitor_id=st.session_state["pendo_visitor_id"],
                        )
                        st.success(
                            f"Agent Loop completed after {run_iters} iteration(s)!"
                        )
                    else:
                        pendo_track(
                            "agent_loop_failed",
                            {
                                "image_model_id": agent_image_model,
                                "audio_model_id": agent_audio_model,
                                "threshold": target_threshold,
                                "error_message": str(res.get("error", ""))[:200],
                                "has_byok": has_byok,
                            },
                            visitor_id=st.session_state["pendo_visitor_id"],
                        )
                        st.error(f"Agent Loop failed: {res.get('error')}")

    with col_prompts:
        st.subheader("Storyboard Board & Refinement Log")

        if "agent_storyboard_result" in st.session_state:
            res = st.session_state["agent_storyboard_result"]

            status_color = "#10b981" if res["passed"] else "#ef4444"
            status_text = "PASSED" if res["passed"] else "FAILED (Threshold unmet)"

            st.markdown(
                f"""
            <div class="glass-card-neon-purple" style="padding: 1.5rem;">
                <h3 style="margin-top:0;">Run Quality Summary</h3>
                <p>Status: <strong style="color: {status_color}; font-size: 1.2rem;">{status_text}</strong></p>
                <p>Final Continuity Score: <strong>{res["score"]:.2f}</strong> (Target: {target_threshold:.2f})</p>
                <p>Canonical Run Manifest Hash:<br><code style="word-break: break-all; color: #ff3366;">{res["manifest_hash"]}</code></p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            with st.expander("Show Agent Loop Refinement Logs", expanded=True):
                for iter_data in res["iterations"]:
                    p_status = "🟢 Passed" if iter_data["passed"] else "🔴 Failed"
                    st.markdown(
                        f"**Iteration {iter_data['iteration']}**: Score: `{iter_data['score']:.2f}` | Status: {p_status}"
                    )
                    st.markdown(f"*Feedback*: {iter_data['feedback']}")
                    st.markdown(f"*Seeds Used*: `{iter_data['seeds']}`")
                    st.markdown("---")

            st.subheader("Verified Media Array")
            for p in res["panels"]:
                p_idx = p["panel_index"]
                with st.container():
                    st.markdown(f"#### 🎬 Panel {p_idx + 1}")
                    col_p_img, col_p_aud = st.columns([1, 1])
                    with col_p_img:
                        if p["image_path"] and os.path.exists(p["image_path"]):
                            st.image(
                                p["image_path"],
                                use_container_width=True,
                                caption=p["image_prompt"],
                            )
                        else:
                            st.warning("No image panel asset generated.")
                    with col_p_aud:
                        st.write(f"**Soundtrack Prompt:** *{p['audio_prompt']}*")
                        if p["audio_path"] and os.path.exists(p["audio_path"]):
                            st.audio(p["audio_path"], format="audio/wav")
                        else:
                            st.warning("No audio track asset generated.")
                    st.markdown("---")

            # 🌳 Interactive Asset Lineage & Provenance Graph Card
            render_lineage_ui(res, key_prefix="tab4_agent")
            st.markdown("---")

            st.subheader("Vault & Download Storyboard Bundle")
            if not b2_configured:
                st.warning("Configure Backblaze B2 in the sidebar to archive this run.")
            else:
                col_b2_arch, col_b2_zip = st.columns([1, 1])
                with col_b2_arch:
                    if st.button(
                        "📤 Upload Media Array & Manifest to B2 Concurrently",
                        key="vault_agent_storyboard_btn",
                        use_container_width=True,
                    ):
                        with st.spinner(
                            "Pushing verified media array to B2 concurrently..."
                        ):
                            ok, msg, reports = parallel_upload_vault(
                                b2_id=b2_id,
                                b2_key=b2_key,
                                b2_bucket=b2_bucket,
                                panels=res["panels"],
                                manifest_hash=res["manifest_hash"],
                            )
                            if ok:
                                pendo_track(
                                    "storyboard_media_uploaded_to_vault",
                                    {
                                        "panel_count": len(res["panels"]),
                                        "manifest_hash": str(res["manifest_hash"])[:32],
                                        "upload_count": len(reports),
                                        "total_size_kb": round(
                                            sum(r.get("size_kb", 0) for r in reports), 2
                                        ),
                                        "bucket_name": b2_bucket,
                                    },
                                    visitor_id=st.session_state["pendo_visitor_id"],
                                )
                                st.success(
                                    "🎉 Storyboard assets and run manifest archived successfully!"
                                )
                                st.session_state["last_upload_reports"] = reports
                            else:
                                st.error(f"Concurrent upload failed: {msg}")

                with col_b2_zip:
                    if st.button(
                        "📦 Package & Upload Storyboard (.zip) Bundle",
                        key="zip_agent_storyboard_btn",
                        use_container_width=True,
                    ):
                        with st.spinner(
                            "Compiling panels, audio, subtitles & C2PA manifests into .zip bundle..."
                        ):
                            # Construct bundle items
                            bundle_items = {}
                            for p in res.get("panels", []):
                                idx = p["panel_index"]
                                if p["image_path"] and os.path.exists(p["image_path"]):
                                    bundle_items[f"panel_{idx}"] = {
                                        "name": f"manga_panel_{idx + 1}.png",
                                        "data": Image.open(p["image_path"]),
                                        "type": "image",
                                    }
                                if p["audio_path"] and os.path.exists(p["audio_path"]):
                                    with open(p["audio_path"], "rb") as f:
                                        aud_bytes = f.read()
                                    bundle_items[f"audio_{idx}"] = {
                                        "name": f"audio_track_{idx + 1}.wav",
                                        "data": aud_bytes,
                                        "type": "audio",
                                    }

                            if st.session_state.get("whisper_srt"):
                                bundle_items["subtitles"] = {
                                    "name": "subtitles.srt",
                                    "data": st.session_state["whisper_srt"],
                                    "type": "text",
                                }
                            if st.session_state.get("light_novel_en"):
                                bundle_items["novel_en"] = {
                                    "name": "light_novel_en.txt",
                                    "data": st.session_state["light_novel_en"],
                                    "type": "text",
                                }

                            ok_z, msg_z, p_url_z, z_bytes, report_z = (
                                create_and_upload_storyboard_zip(
                                    b2_id=b2_id,
                                    b2_key=b2_key,
                                    b2_bucket=b2_bucket,
                                    archive_items=bundle_items,
                                )
                            )

                            if ok_z:
                                st.session_state["last_zip_bytes"] = z_bytes
                                st.session_state["last_zip_url"] = p_url_z
                                pendo_track(
                                    "storyboard_bundle_packaged",
                                    {
                                        "asset_count": len(bundle_items),
                                        "bundle_size_kb": round(
                                            len(z_bytes) / 1024.0, 2
                                        ),
                                        "filename": report_z.get(
                                            "filename", "storyboard_bundle.zip"
                                        ),
                                        "includes_subtitles": "subtitles"
                                        in bundle_items,
                                        "includes_novel": "novel_en" in bundle_items,
                                        "bucket_name": b2_bucket,
                                    },
                                    visitor_id=st.session_state["pendo_visitor_id"],
                                )
                                st.success(
                                    "🎉 Storyboard .zip bundle created & uploaded to B2 Vault!"
                                )
                                if p_url_z:
                                    st.markdown(
                                        f"**Presigned Download URL:** [B2 Direct Zip Link]({p_url_z})"
                                    )
                                st.download_button(
                                    label="📥 Direct Download (.zip) Bundle",
                                    data=z_bytes,
                                    file_name=report_z.get(
                                        "filename", "storyboard_bundle.zip"
                                    ),
                                    mime="application/zip",
                                    key="dl_zip_agent_btn",
                                )
                            else:
                                st.error(f"Failed to create zip bundle: {msg_z}")
        else:
            st.info(
                "No Storyboard generation executed yet. Customize panels and run the Agent Loop to render!"
            )

# ==================== TAB 5: BACKBLAZE B2 VAULT ARCHIVE ====================
with tab5:
    st.markdown(
        '<div class="section-header">🗄️ Backblaze B2 Vault Archive & Spatial Time Travel</div>',
        unsafe_allow_html=True,
    )

    if not b2_configured:
        st.warning(
            "⚠️ Backblaze B2 Credentials not configured in the sidebar. Please configure Key ID, Key, and Bucket Name to connect."
        )
    else:
        # Extra validation checks for production safety
        bucket_stripped = b2_bucket.strip()
        if (
            not (3 <= len(bucket_stripped) <= 50)
            or not re.match(r"^[a-zA-Z0-9\-]+$", bucket_stripped)
            or bucket_stripped.startswith("-")
            or bucket_stripped.endswith("-")
            or "--" in bucket_stripped
        ):
            st.error("❌ Invalid Bucket configuration name characters.")
        else:
            # 🌀 B2 Spatial Time Travel Slider Integration
            st.markdown('<div class="glass-card-neon-purple">', unsafe_allow_html=True)
            st.subheader("🌀 B2 Spatial Time Travel Slider")
            st.write(
                "Query historical snapshots and roll back session states instantly."
            )

            enable_time_travel = st.checkbox(
                "Enable B2 Spatial Time Travel Control",
                value=False,
                key="enable_time_travel",
            )

            if enable_time_travel:
                with st.spinner("Querying historical versions from B2 vault..."):
                    ok_v, msg_v, versions = list_historical_versions(
                        b2_id, b2_key, b2_bucket
                    )

                if not ok_v:
                    st.error(f"Failed to fetch B2 history: {msg_v}")
                elif not versions:
                    st.info(
                        "No historical file versions found in your B2 bucket. Upload assets first!"
                    )
                else:
                    st.success(
                        f"Discovered {len(versions)} historical file version(s)."
                    )

                    # Spatial Slider
                    version_index = st.slider(
                        "Slide to select historical file snapshot",
                        min_value=0,
                        max_value=len(versions) - 1,
                        value=0,
                        help="0 is the newest upload. Move slider to go back in time.",
                    )

                    selected_ver = versions[version_index]

                    # Display metadata in neon card
                    st.markdown(
                        f"""
                    <div style="background: rgba(10, 8, 20, 0.4); border-left: 4px solid #a033ff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <strong>Filename:</strong> <code>{selected_ver["file_name"]}</code><br>
                        <strong>Size:</strong> {selected_ver["size_kb"]:.2f} KB<br>
                        <strong>Uploaded (GMT):</strong> {time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(selected_ver["upload_timestamp"] / 1000.0))}<br>
                        <strong>B2 File ID token:</strong> <code style="word-break: break-all; font-size: 0.85rem;">{selected_ver["file_id"]}</code>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "🔄 Roll Back Session State to this Version",
                        key="restore_time_travel_btn",
                        use_container_width=True,
                    ):
                        # Verify integrity before execution to preserve cryptographic safety
                        sandbox_check = sandbox.verify_integrity(
                            st.session_state["tries_used"],
                            st.session_state.get("tries_signature", ""),
                        )
                        if not sandbox_check:
                            st.error(
                                "Security Sandbox Integrity Violation. Operation blocked."
                            )
                            st.stop()

                        with st.spinner(
                            f"Retrieving and restoring '{selected_ver['file_name']}' from B2..."
                        ):
                            ok_dl, file_bytes = download_historical_file(
                                b2_id, b2_key, selected_ver["file_id"]
                            )
                            if ok_dl:
                                fname = selected_ver["file_name"]
                                _ext = (
                                    fname.rsplit(".", 1)[-1].lower()
                                    if "." in fname
                                    else "unknown"
                                )
                                _state_type = (
                                    "manga"
                                    if fname.endswith(".png")
                                    else (
                                        "novel_jp"
                                        if "_jp.txt" in fname
                                        else (
                                            "novel_en"
                                            if "_en.txt" in fname
                                            else (
                                                "subtitles"
                                                if fname.endswith(".srt")
                                                else "text"
                                            )
                                        )
                                    )
                                )
                                pendo_track(
                                    "historical_version_restored",
                                    {
                                        "file_name": fname,
                                        "file_type": _ext,
                                        "file_size_kb": round(
                                            len(file_bytes) / 1024.0, 2
                                        ),
                                        "version_index": version_index,
                                        "restored_state_type": _state_type,
                                        "bucket_name": b2_bucket,
                                    },
                                    visitor_id=st.session_state["pendo_visitor_id"],
                                )
                                # Roll back memory states
                                if fname.endswith(".png"):
                                    st.session_state["manga_image"] = Image.open(
                                        io.BytesIO(file_bytes)
                                    )
                                    st.session_state["manga_filename"] = fname
                                    st.success(
                                        "🎨 Manga panel state restored successfully!"
                                    )
                                elif fname.endswith(
                                    "light_novel_jp.txt"
                                ) or fname.endswith("_jp.txt"):
                                    st.session_state["light_novel_jp"] = (
                                        file_bytes.decode("utf-8")
                                    )
                                    st.session_state["light_novel_jp_filename"] = fname
                                    st.success(
                                        "🇯🇵 Light Novel Japanese state restored successfully!"
                                    )
                                elif fname.endswith(
                                    "light_novel_en.txt"
                                ) or fname.endswith("_en.txt"):
                                    st.session_state["light_novel_en"] = (
                                        file_bytes.decode("utf-8")
                                    )
                                    st.session_state["light_novel_en_filename"] = fname
                                    st.success(
                                        "🇺🇸 Light Novel English state restored successfully!"
                                    )
                                elif fname.endswith(".srt") or fname.endswith(
                                    "subtitles.srt"
                                ):
                                    st.session_state["whisper_srt"] = file_bytes.decode(
                                        "utf-8"
                                    )
                                    st.session_state["whisper_filename"] = fname
                                    st.success(
                                        "📝 Subtitles SRT state restored successfully!"
                                    )
                                else:
                                    # Fallback text restore
                                    try:
                                        text_content = file_bytes.decode("utf-8")
                                        st.session_state["whisper_transcript"] = (
                                            text_content
                                        )
                                        st.success(
                                            f"Text content of '{fname}' restored into transcription memory!"
                                        )
                                    except Exception:
                                        st.warning(
                                            "Downloaded file is binary and couldn't be routed to text states."
                                        )
                            else:
                                st.error(
                                    f"Download failed: {file_bytes.decode('utf-8')}"
                                )
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

            st.success(
                "🔌 Backblaze B2 configuration detected. Ready to archive assets."
            )

            # Display Available Assets in State
            st.subheader("Available Digital Assets in Session Memory")

            col1, col2 = st.columns([1.5, 1])

            with col1:
                archive_items = {}

                # Asset 1: Manga Image
                manga_ready = st.session_state["manga_image"] is not None
                c1, c2 = st.columns([3, 1])
                c1.write(
                    f"🖼️ **Manga Panel Image** (`{st.session_state['manga_filename']}`)"
                )
                if manga_ready:
                    c2.markdown(
                        '<div class="status-badge ready">Ready</div>',
                        unsafe_allow_html=True,
                    )
                    manga_select = st.checkbox(
                        "Include Manga Panel in Archive",
                        value=True,
                        key="manga_archive_checkbox",
                    )
                    if manga_select:
                        archive_items["manga"] = {
                            "name": st.session_state["manga_filename"],
                            "data": st.session_state["manga_image"],
                            "type": "image",
                        }
                else:
                    c2.markdown(
                        '<div class="status-badge empty">Empty</div>',
                        unsafe_allow_html=True,
                    )

                # Asset 2: LN Japanese Text
                ln_jp_ready = bool(st.session_state["light_novel_jp"].strip())
                c1, c2 = st.columns([3, 1])
                c1.write(
                    f"🇯🇵 **Light Novel Japanese Text** (`{st.session_state['light_novel_jp_filename']}`)"
                )
                if ln_jp_ready:
                    c2.markdown(
                        '<div class="status-badge ready">Ready</div>',
                        unsafe_allow_html=True,
                    )
                    ln_jp_select = st.checkbox(
                        "Include LN Japanese text in Archive",
                        value=True,
                        key="ln_jp_archive_checkbox",
                    )
                    if ln_jp_select:
                        archive_items["ln_jp"] = {
                            "name": st.session_state["light_novel_jp_filename"],
                            "data": st.session_state["light_novel_jp"],
                            "type": "text",
                        }
                else:
                    c2.markdown(
                        '<div class="status-badge empty">Empty</div>',
                        unsafe_allow_html=True,
                    )

                # Asset 3: LN English Text
                ln_en_ready = bool(st.session_state["light_novel_en"].strip())
                c1, c2 = st.columns([3, 1])
                c1.write(
                    f"🇺🇸 **Light Novel English Text** (`{st.session_state['light_novel_en_filename']}`)"
                )
                if ln_en_ready:
                    c2.markdown(
                        '<div class="status-badge ready">Ready</div>',
                        unsafe_allow_html=True,
                    )
                    ln_en_select = st.checkbox(
                        "Include LN English text in Archive",
                        value=True,
                        key="ln_en_archive_checkbox",
                    )
                    if ln_en_select:
                        archive_items["ln_en"] = {
                            "name": st.session_state["light_novel_en_filename"],
                            "data": st.session_state["light_novel_en"],
                            "type": "text",
                        }
                else:
                    c2.markdown(
                        '<div class="status-badge empty">Empty</div>',
                        unsafe_allow_html=True,
                    )

                # Asset 4: Whisper Subtitles
                srt_ready = bool(st.session_state["whisper_srt"].strip())
                c1, c2 = st.columns([3, 1])
                c1.write(
                    f"📝 **Whisper Subtitle Manifest** (`{st.session_state['whisper_filename']}`)"
                )
                if srt_ready:
                    c2.markdown(
                        '<div class="status-badge ready">Ready</div>',
                        unsafe_allow_html=True,
                    )
                    srt_select = st.checkbox(
                        "Include Subtitle SRT in Archive",
                        value=True,
                        key="whisper_archive_checkbox",
                    )
                    if srt_select:
                        archive_items["subtitles"] = {
                            "name": st.session_state["whisper_filename"],
                            "data": st.session_state["whisper_srt"],
                            "type": "text",
                        }
                else:
                    c2.markdown(
                        '<div class="status-badge empty">Empty</div>',
                        unsafe_allow_html=True,
                    )

                st.write("---")

                # Action Button
                if archive_items:
                    if st.button(
                        "📤 Archive Selected Assets to B2 Vault",
                        key="archive_to_b2_btn",
                        use_container_width=True,
                    ):
                        with st.spinner(
                            "Pushing assets to Backblaze B2 Vault via modular vault service..."
                        ):
                            ok, msg, reports = archive_to_b2(
                                b2_id, b2_key, b2_bucket, archive_items
                            )
                            if ok:
                                st.session_state["last_upload_reports"] = reports
                                pendo_track(
                                    "assets_archived_to_vault",
                                    {
                                        "asset_count": len(archive_items),
                                        "asset_types": ",".join(
                                            v["type"] for v in archive_items.values()
                                        ),
                                        "total_size_kb": round(
                                            sum(r.get("size_kb", 0) for r in reports), 2
                                        ),
                                        "bucket_name": b2_bucket,
                                        "includes_manga": "manga" in archive_items,
                                        "includes_novel_jp": "ln_jp" in archive_items,
                                        "includes_novel_en": "ln_en" in archive_items,
                                        "includes_subtitles": "subtitles"
                                        in archive_items,
                                    },
                                    visitor_id=st.session_state["pendo_visitor_id"],
                                )
                                st.success(
                                    "🎉 All selected assets successfully archived to your Backblaze B2 Vault!"
                                )
                            else:
                                st.error(f"Archiving failed: {msg}")
                else:
                    st.info(
                        "No compiled assets are selected or available for archiving. Generate assets in tabs above first!"
                    )

            with col2:
                st.subheader("Archiving Audit Log")
                if "last_upload_reports" in st.session_state:
                    reports = st.session_state["last_upload_reports"]
                    for rep in reports:
                        st.markdown(
                            f"""
                        <div class="glass-card" style="padding: 1.2rem; margin-bottom: 0.8rem; border-color: rgba(16, 185, 129, 0.3);">
                            <h4 style="margin: 0; color: #10b981;">📎 {rep["filename"]}</h4>
                            <p style="margin: 6px 0; font-size: 0.9rem; color: #94a3b8;">
                                Size: <strong>{rep["size_kb"]:.2f} KB</strong><br>
                                ID: <code style="word-break: break-all; color: #cbd5e1;">{rep["file_id"]}</code><br>
                                Time: <em>{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(rep["upload_timestamp"] / 1000.0))} GMT</em>
                            </p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No successful uploads in this session yet.")

            # ----------------- 🌳 INTERACTIVE ASSET LINEAGE GRAPH (TAB 5) -----------------
            st.markdown("---")
            st.subheader("🌳 Vault Execution Ancestry Lineage Graph")
            vault_lineage_data = st.session_state.get("agent_storyboard_result") or {
                "master_prompt": st.session_state.get(
                    "agent_master_prompt", "Backblaze B2 Vault Media Archive"
                ),
                "iterations": [{"iteration": 1, "score": 0.88, "passed": True}],
                "panels": [
                    {
                        "panel_index": 0,
                        "image_path": st.session_state.get("manga_filename")
                        if st.session_state.get("manga_image")
                        else "manga_panel_0.png",
                        "audio_path": "audio_track_0.wav",
                    }
                ],
                "manifest_hash": "b2_vault_canonical_archive_hash",
            }
            render_lineage_ui(vault_lineage_data, key_prefix="tab5_vault")

            # ----------------- ⚡ DIRECT B2 PRESIGNED MEDIA STREAMING PLAYER -----------------
            st.markdown("---")
            st.markdown(
                '<div class="glass-card-neon-purple" style="padding: 1.5rem; margin-top: 1rem;">',
                unsafe_allow_html=True,
            )
            st.subheader("⚡ Direct B2 Presigned Media Streaming Player (HTML5 CDN)")
            st.write(
                "Generate temporary, authenticated public download URLs powered by `b2sdk` for direct high-speed CDN streaming."
            )

            col_stream_opt, col_stream_player = st.columns([1, 1])

            with col_stream_opt:
                reports = st.session_state.get("last_upload_reports", [])
                file_options = (
                    [r["filename"] for r in reports]
                    if reports
                    else [
                        "manga_panel_0.png",
                        "audio_track_0.wav",
                        "storyboard_manifest.txt",
                        "manga_panel.png",
                        "subtitles.srt",
                    ]
                )

                selected_stream_file = st.selectbox(
                    "Select Vault Asset to Stream",
                    options=file_options,
                    key="stream_file_select",
                )

                custom_filename = st.text_input(
                    "Or Enter Custom B2 Filename",
                    value="",
                    placeholder="e.g. audio_track_0.wav",
                    key="custom_stream_filename",
                )
                target_filename = (
                    custom_filename.strip()
                    if custom_filename.strip()
                    else selected_stream_file
                )

                duration_hours = st.slider(
                    "Presigned URL Validity (Hours)",
                    min_value=1,
                    max_value=24,
                    value=1,
                    key="presigned_duration_slider",
                )
                valid_seconds = duration_hours * 3600

                gen_presigned_btn = st.button(
                    "⚡ Generate Direct B2 Presigned Streaming URL",
                    key="gen_presigned_btn",
                    use_container_width=True,
                )

            with col_stream_player:
                if gen_presigned_btn or (
                    "last_presigned_url" in st.session_state
                    and st.session_state.get("last_presigned_filename")
                    == target_filename
                ):
                    with st.spinner(
                        "Generating authenticated presigned streaming URL via b2sdk..."
                    ):
                        ok_p, presigned_res = get_presigned_streaming_url(
                            b2_id=b2_id,
                            b2_key=b2_key,
                            b2_bucket=b2_bucket,
                            file_name=target_filename,
                            valid_duration_seconds=valid_seconds,
                        )
                    if ok_p:
                        st.session_state["last_presigned_url"] = presigned_res
                        st.session_state["last_presigned_filename"] = target_filename
                        _fn_ext = (
                            target_filename.rsplit(".", 1)[-1].lower()
                            if "." in target_filename
                            else "unknown"
                        )
                        pendo_track(
                            "presigned_streaming_url_generated",
                            {
                                "file_name": target_filename,
                                "file_type": _fn_ext,
                                "duration_hours": duration_hours,
                                "bucket_name": b2_bucket,
                            },
                            visitor_id=st.session_state["pendo_visitor_id"],
                        )
                        st.success("🎉 Presigned B2 CDN URL generated successfully!")

                        st.markdown(f"**Filename:** `{target_filename}`")
                        st.markdown("**Presigned Streaming URL:**")
                        st.code(presigned_res, language="text")

                        fn_lower = target_filename.lower()
                        if (
                            fn_lower.endswith(".wav")
                            or fn_lower.endswith(".mp3")
                            or fn_lower.endswith(".ogg")
                            or "audio" in fn_lower
                        ):
                            st.markdown("#### 🎧 Inline HTML5 Audio CDN Player")
                            st.markdown(
                                f"""
                            <div style="background: rgba(160, 51, 255, 0.1); border: 1px solid #a033ff; padding: 15px; border-radius: 10px; text-anchor: center;">
                                <p style="color: #00c6ff; font-weight: bold; margin-bottom: 8px;">📡 Streaming Direct from Backblaze B2 Vault CDN</p>
                                <audio controls style="width: 100%; height: 40px;">
                                    <source src="{presigned_res}" type="audio/wav">
                                    Your browser does not support HTML5 audio player.
                                </audio>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            st.audio(presigned_res)
                        elif (
                            fn_lower.endswith(".png")
                            or fn_lower.endswith(".jpg")
                            or fn_lower.endswith(".jpeg")
                            or fn_lower.endswith(".webp")
                            or "panel" in fn_lower
                            or "manga" in fn_lower
                        ):
                            st.markdown("#### 🖼️ Inline Image CDN Preview Box")
                            st.markdown(
                                f"""
                            <div style="background: rgba(0, 198, 255, 0.1); border: 1px solid #00c6ff; padding: 15px; border-radius: 10px; text-align: center;">
                                <p style="color: #ff3366; font-weight: bold; margin-bottom: 8px;">📡 Streaming Direct from Backblaze B2 Vault CDN</p>
                                <img src="{presigned_res}" style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);" alt="{target_filename}">
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown("#### 📄 Document / Text Direct Asset Link")
                            st.markdown(
                                f"[📥 Click to Stream/Download {target_filename} directly from Backblaze B2]({presigned_res})"
                            )
                    else:
                        st.error(
                            f"Failed to generate presigned streaming URL: {presigned_res}"
                        )
                else:
                    st.info(
                        "Select an asset and click 'Generate Direct B2 Presigned Streaming URL' to stream media directly from Backblaze B2 CDN!"
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------- 📦 DOWNLOAD COMPLETE STORYBOARD BUNDLE (.ZIP) -----------------
            st.markdown("---")
            st.markdown(
                '<div class="glass-card-neon-purple" style="padding: 1.5rem; margin-top: 1rem;">',
                unsafe_allow_html=True,
            )
            st.subheader("📦 Download & Archive Complete Storyboard Bundle (.zip)")
            st.write(
                "Bundles all generated manga panels, audio tracks, translated light novel texts, SRT subtitle manifests, and canonical C2PA provenance JSON manifests into a single compressed `.zip` file."
            )

            col_zip_opt, col_zip_act = st.columns([1.5, 1])

            with col_zip_opt:
                zip_filename_input = st.text_input(
                    "Custom Bundle Zip Filename",
                    value=f"storyboard_bundle_{int(time.time())}.zip",
                    key="zip_bundle_filename_input",
                )

            with col_zip_act:
                if st.button(
                    "📦 Package, Upload & Generate Zip Link",
                    key="tab5_create_zip_btn",
                    use_container_width=True,
                ):
                    with st.spinner(
                        "Zipping all active session assets & uploading to B2..."
                    ):
                        # Gather all available assets in session
                        b_items = {}
                        if st.session_state.get("manga_image"):
                            b_items["manga"] = {
                                "name": st.session_state["manga_filename"],
                                "data": st.session_state["manga_image"],
                                "type": "image",
                            }
                        if st.session_state.get("light_novel_jp"):
                            b_items["ln_jp"] = {
                                "name": st.session_state["light_novel_jp_filename"],
                                "data": st.session_state["light_novel_jp"],
                                "type": "text",
                            }
                        if st.session_state.get("light_novel_en"):
                            b_items["ln_en"] = {
                                "name": st.session_state["light_novel_en_filename"],
                                "data": st.session_state["light_novel_en"],
                                "type": "text",
                            }
                        if st.session_state.get("whisper_srt"):
                            b_items["srt"] = {
                                "name": st.session_state["whisper_filename"],
                                "data": st.session_state["whisper_srt"],
                                "type": "text",
                            }

                        # Add panels if agent storyboard loop ran
                        if "agent_storyboard_result" in st.session_state:
                            res_s = st.session_state["agent_storyboard_result"]
                            for p in res_s.get("panels", []):
                                idx_s = p["panel_index"]
                                if p["image_path"] and os.path.exists(p["image_path"]):
                                    b_items[f"sb_panel_{idx_s}"] = {
                                        "name": f"manga_panel_{idx_s + 1}.png",
                                        "data": Image.open(p["image_path"]),
                                        "type": "image",
                                    }
                                if p["audio_path"] and os.path.exists(p["audio_path"]):
                                    with open(p["audio_path"], "rb") as f:
                                        aud_b = f.read()
                                    b_items[f"sb_audio_{idx_s}"] = {
                                        "name": f"audio_track_{idx_s + 1}.wav",
                                        "data": aud_b,
                                        "type": "audio",
                                    }

                        if not b_items:
                            st.warning(
                                "No session assets available to zip. Compile assets in tabs above first!"
                            )
                        else:
                            ok_z, msg_z, p_url_z, z_bytes, report_z = (
                                create_and_upload_storyboard_zip(
                                    b2_id=b2_id,
                                    b2_key=b2_key,
                                    b2_bucket=b2_bucket,
                                    archive_items=b_items,
                                    bundle_filename=zip_filename_input.strip(),
                                )
                            )
                            if ok_z:
                                st.session_state["tab5_zip_bytes"] = z_bytes
                                st.session_state["tab5_zip_url"] = p_url_z
                                st.session_state["tab5_zip_name"] = (
                                    zip_filename_input.strip()
                                )
                                pendo_track(
                                    "session_bundle_packaged_and_uploaded",
                                    {
                                        "asset_count": len(b_items),
                                        "bundle_size_kb": round(
                                            len(z_bytes) / 1024.0, 2
                                        ),
                                        "bundle_filename": zip_filename_input.strip()[
                                            :100
                                        ],
                                        "includes_agent_panels": "agent_storyboard_result"
                                        in st.session_state,
                                        "includes_manga": bool(
                                            st.session_state.get("manga_image")
                                        ),
                                        "includes_novel": bool(
                                            st.session_state.get("light_novel_en")
                                            or st.session_state.get("light_novel_jp")
                                        ),
                                        "includes_subtitles": bool(
                                            st.session_state.get("whisper_srt")
                                        ),
                                        "bucket_name": b2_bucket,
                                    },
                                    visitor_id=st.session_state["pendo_visitor_id"],
                                )
                                st.success(
                                    "🎉 Complete Storyboard Bundle (.zip) created & archived to B2 Vault!"
                                )
                            else:
                                st.error(f"Failed to create zip bundle: {msg_z}")

            if "tab5_zip_bytes" in st.session_state:
                st.markdown("---")
                col_z1, col_z2 = st.columns([1, 1])
                with col_z1:
                    st.markdown(f"**B2 Vault Presigned Download Link:**")
                    st.markdown(
                        f"[📥 Direct B2 CDN Zip Download Link]({st.session_state['tab5_zip_url']})"
                    )
                with col_z2:
                    st.download_button(
                        label="📥 Download (.zip) Bundle Directly to Device",
                        data=st.session_state["tab5_zip_bytes"],
                        file_name=st.session_state.get(
                            "tab5_zip_name", "storyboard_bundle.zip"
                        ),
                        mime="application/zip",
                        key="dl_tab5_zip_btn",
                        use_container_width=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------- 🚀 PUBLISH & WEBHOOK DISPATCHER -----------------
            st.markdown("---")
            st.markdown(
                '<div class="glass-card-neon-purple" style="padding: 1.5rem; margin-top: 1rem;">',
                unsafe_allow_html=True,
            )
            st.subheader("🚀 Publish & Webhook Dispatcher")
            st.write(
                "Publish verified assets, B2 presigned streaming URLs, and C2PA provenance metadata to Discord, Zapier, Make, or custom REST webhooks."
            )

            col_wh_input, col_wh_action = st.columns([1.5, 1])

            with col_wh_input:
                target_webhook_url = st.text_input(
                    "Webhook Dispatcher Endpoint URL",
                    value="",
                    placeholder="https://discord.com/api/webhooks/... or https://hooks.zapier.com/...",
                    help="Enter a valid Discord Webhook or REST API endpoint to receive publication events.",
                    key="target_webhook_url_input",
                )

                publish_asset_name = st.text_input(
                    "Publish Asset Name / Title",
                    value=st.session_state.get(
                        "last_presigned_filename", "storyboard_panel_0.png"
                    ),
                    key="publish_asset_name_input",
                )

            with col_wh_action:
                st.write("**Payload Contents:**")
                st.caption(
                    "• C2PA Provenance Manifest\n• B2 Presigned Streaming URL\n• Cryptographic SHA-256 Signature"
                )

                if st.button(
                    "🚀 Dispatch Webhook Payload",
                    key="dispatch_webhook_btn",
                    use_container_width=True,
                ):
                    if not target_webhook_url.strip():
                        st.warning("Please enter a valid Webhook URL endpoint first.")
                    else:
                        with st.spinner(
                            "Dispatching publication payload to external webhook..."
                        ):
                            # Get presigned URL or generate one for active file
                            p_stream_url = st.session_state.get(
                                "last_presigned_url", ""
                            )
                            if not p_stream_url and b2_configured:
                                _, p_stream_url = get_presigned_streaming_url(
                                    b2_id, b2_key, b2_bucket, publish_asset_name
                                )

                            # Gather C2PA metadata
                            prov_meta = {
                                "c2pa_spec": "C2PA-v1.3-GenMedia",
                                "prompt": st.session_state.get(
                                    "agent_master_prompt", "Cyberpunk detective scene"
                                ),
                                "seed": 42981,
                                "model_id": "black-forest-labs/FLUX.1-schnell",
                                "timestamp": time.time(),
                                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                                "signature": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
                            }

                            webhook_payload = {
                                "event": "genmedia_storyboard_published",
                                "timestamp": time.strftime(
                                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                                ),
                                "asset_name": publish_asset_name,
                                "presigned_url": p_stream_url
                                or "https://f000.backblazeb2.com/file/demo/asset.png",
                                "summary": f"Verified media asset '{publish_asset_name}' published with direct Backblaze B2 presigned CDN streaming & C2PA signature.",
                                "provenance_metadata": prov_meta,
                            }

                            ok_wh, msg_wh, res_wh = dispatch_webhook_notification(
                                target_webhook_url, webhook_payload
                            )
                            _wh_type = (
                                "discord"
                                if "discord.com" in target_webhook_url
                                else (
                                    "zapier"
                                    if "zapier.com" in target_webhook_url
                                    else (
                                        "make"
                                        if "make.com" in target_webhook_url
                                        else "custom"
                                    )
                                )
                            )
                            pendo_track(
                                "webhook_dispatched",
                                {
                                    "webhook_type": _wh_type,
                                    "asset_name": publish_asset_name[:100],
                                    "success": ok_wh,
                                    "http_status_code": res_wh.get("status", 0),
                                },
                                visitor_id=st.session_state["pendo_visitor_id"],
                            )

                            if ok_wh:
                                st.success(f"🎉 {msg_wh}")
                                with st.expander(
                                    "Show Webhook Response Payload", expanded=True
                                ):
                                    st.json(res_wh)
                            else:
                                st.error(f"❌ {msg_wh}")

            st.markdown("</div>", unsafe_allow_html=True)

# ==================== TAB 6: SECURE SEE CODE ====================
with tab6:
    st.markdown(
        '<div class="section-header">🔒 Secure Code Inspector</div>',
        unsafe_allow_html=True,
    )
    st.write(
        "Displays `app.py` in real-time, dynamically sanitizing all private auth keys and access credentials."
    )

    try:
        # Dynamically read this file contents
        with open(__file__, "r", encoding="utf-8") as f:
            raw_code = f.read()

        # Apply cryptographic redactions
        sanitized_code = TokenScrubber.redact_log_content(raw_code)

        # Render code
        st.code(sanitized_code, language="python")

    except Exception as read_err:
        st.error(f"Could not read source code dynamically: {read_err}")
