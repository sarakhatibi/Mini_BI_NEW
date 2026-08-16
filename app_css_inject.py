# app_css_inject.py
import streamlit as st

RTL_CSS = """<style>
/* Right-to-left layout for the Persian interface */
.stApp, .block-container, section[data-testid="stSidebar"] { direction: rtl; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label { text-align: right; }
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] { direction: ltr; text-align: right; }
[data-testid="stDataFrame"] { direction: ltr; }
</style>"""


def inject_style(theme: str = "muted"):
    """
    theme: "muted" | "vibrant" | "dark"
    Call this early in app.py (after st.set_page_config).
    """
    if theme == "vibrant":
        css = """<style>
/* Vibrant background (compact) */
.stApp { position:relative; overflow:hidden; background: linear-gradient(180deg,#f8fbfa 0%,#eef6f2 50%,#f6faf6 100%); min-height:100vh; }
.blob{ position:absolute; width:40vmax; height:40vmax; filter: blur(80px) saturate(120%); opacity:0.55; mix-blend-mode:screen; z-index:0; }
.blob.one{ background: radial-gradient(circle at 30% 30%, rgba(99,102,241,0.95), rgba(99,102,241,0.40) 40%, transparent 60%); left:-20%; top:-25%; animation:float1 18s ease-in-out infinite; }
.blob.two{ background: radial-gradient(circle at 70% 70%, rgba(16,185,129,0.92), rgba(16,185,129,0.35) 40%, transparent 60%); right:-18%; top:10%; animation:float2 22s ease-in-out infinite; }
.blob.three{ background: radial-gradient(circle at 50% 40%, rgba(249,115,22,0.92), rgba(249,115,22,0.30) 40%, transparent 60%); left:10%; bottom:-30%; animation:float3 26s ease-in-out infinite; }
@keyframes float1 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(6vw,8vh,0)}100%{transform:translate3d(0,0,0)} }
@keyframes float2 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(-8vw,-6vh,0)}100%{transform:translate3d(0,0,0)} }
@keyframes float3 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(10vw,6vh,0)}100%{transform:translate3d(0,0,0)} }
.block-container, .reportview-container .main { position:relative; z-index:2; background:rgba(255,255,255,0.72); border-radius:14px; padding:28px; box-shadow:0 10px 30px rgba(16,24,40,0.06); backdrop-filter: blur(6px) saturate(120%); }
.element-container, .stDataFrame, .stMarkdown { position:relative; z-index:3; }
</style>
<div class="blob one" aria-hidden="true"></div>
<div class="blob two" aria-hidden="true"></div>
<div class="blob three" aria-hidden="true"></div>
"""
    elif theme == "dark":
        css = """<style>
/* Dark, low-contrast background */
.stApp { position:relative; overflow:hidden; background: linear-gradient(180deg,#0b1220 0%, #071427 100%); color:#e6eef6; min-height:100vh; }
.blob{ position:absolute; width:36vmax; height:36vmax; filter: blur(72px) saturate(90%); opacity:0.22; mix-blend-mode:screen; z-index:0; }
.blob.one{ background: radial-gradient(circle at 30% 30%, rgba(124,58,237,0.9), rgba(99,102,241,0.25) 40%, transparent 60%); left:-18%; top:-28%; animation:float1 30s ease-in-out infinite; }
.blob.two{ background: radial-gradient(circle at 70% 70%, rgba(6,182,212,0.9), rgba(6,182,212,0.22) 40%, transparent 60%); right:-16%; top:6%; animation:float2 34s ease-in-out infinite; }
@keyframes float1 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(4vw,5vh,0)}100%{transform:translate3d(0,0,0)} }
@keyframes float2 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(-5vw,-4vh,0)}100%{transform:translate3d(0,0,0)} }
.block-container, .reportview-container .main { position:relative; z-index:2; background:rgba(10,18,28,0.6); border-radius:12px; padding:22px; box-shadow:0 8px 24px rgba(0,0,0,0.5); backdrop-filter: blur(6px) saturate(80%); color:#e6eef6; border:1px solid rgba(255,255,255,0.03); }
.element-container, .stDataFrame, .stMarkdown { position:relative; z-index:3; color:#e6eef6; }
</style>
<div class="blob one" aria-hidden="true"></div>
<div class="blob two" aria-hidden="true"></div>
"""
    else:
        # muted (پیشنهادی)
        css = """<style>
/* Muted / professional background */
.stApp { position:relative; overflow:hidden; background: linear-gradient(180deg,#fbfcfd 0%, #f6f9f7 50%, #fafcfb 100%); min-height:100vh; }
.blob{ position:absolute; width:34vmax; height:34vmax; filter: blur(56px) saturate(90%); opacity:0.28; mix-blend-mode:normal; z-index:0; }
.blob.one{ background: radial-gradient(circle at 30% 30%, rgba(88,101,242,0.18), rgba(88,101,242,0.10) 40%, transparent 70%); left:-18%; top:-22%; animation:float1 28s ease-in-out infinite; }
.blob.two{ background: radial-gradient(circle at 70% 70%, rgba(34,197,94,0.16), rgba(34,197,94,0.08) 40%, transparent 70%); right:-16%; top:8%; animation:float2 32s ease-in-out infinite; }
.blob.three{ background: radial-gradient(circle at 50% 40%, rgba(249,115,22,0.12), rgba(249,115,22,0.06) 40%, transparent 70%); left:8%; bottom:-28%; width:28vmax; height:28vmax; filter: blur(46px); opacity:0.16; animation:float3 36s ease-in-out infinite; }
@keyframes float1 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(3vw,4vh,0)}100%{transform:translate3d(0,0,0)} }
@keyframes float2 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(-4vw,-3vh,0)}100%{transform:translate3d(0,0,0)} }
@keyframes float3 { 0%{transform:translate3d(0,0,0)}50%{transform:translate3d(6vw,4vh,0)}100%{transform:translate3d(0,0,0)} }
.block-container, .reportview-container .main { position:relative; z-index:2; background:rgba(255,255,255,0.82); border-radius:12px; padding:24px; box-shadow:0 8px 24px rgba(16,24,40,0.05); backdrop-filter: blur(6px); border:1px solid rgba(255,255,255,0.6); }
.element-container, .stDataFrame, .stMarkdown { position:relative; z-index:3; }
</style>
<div class="blob one" aria-hidden="true"></div>
<div class="blob two" aria-hidden="true"></div>
<div class="blob three" aria-hidden="true"></div>
"""
    st.markdown(RTL_CSS + css, unsafe_allow_html=True)