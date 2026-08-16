import streamlit as st


RTL_CSS = """
<style>

/* =========================================
   GLOBAL
========================================= */

.stApp {
    direction: rtl;

    background:
        radial-gradient(
            circle at 10% 5%,
            rgba(190, 120, 80, 0.08),
            transparent 25%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(120, 55, 65, 0.06),
            transparent 25%
        ),
        #f8f4ef;
}

.block-container {
    max-width: 1400px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}


/* =========================================
   TYPOGRAPHY
========================================= */

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6,
.stApp p,
.stApp label,
.stApp [data-testid="stMarkdownContainer"] {
    direction: rtl;
    text-align: right !important;
}

.stApp h1 {
    font-size: 2.4rem;
    font-weight: 800;
    color: #4b2026;
}

.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    color: #54272d;
    font-weight: 750;
}


/* =========================================
   SIDEBAR
========================================= */

section[data-testid="stSidebar"] {
    direction: rtl;

    background:
        linear-gradient(
            180deg,
            #482128 0%,
            #5b2930 100%
        );

    border-left: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] * {
    color: #f9eee7;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #fff8f2;
}

section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #e8b982;
}


/* =========================================
   FILE UPLOADER
========================================= */

[data-testid="stFileUploader"] {
    background: #fffdf9;

    border: 1px solid #eadbd0;
    border-radius: 18px;

    padding: 10px;

    box-shadow:
        0 5px 18px rgba(80, 45, 35, 0.05);
}


/* =========================================
   TABS
========================================= */

[data-baseweb="tab-list"] {
    direction: rtl;

    gap: 8px;

    background: #eee4dc;

    padding: 7px;

    border-radius: 14px;
}

[data-baseweb="tab"] {
    direction: rtl;

    cursor: pointer !important;
    pointer-events: auto !important;

    border-radius: 10px;

    padding: 10px 20px;

    color: #765b59;

    font-weight: 650;

    transition:
        background 0.2s ease,
        color 0.2s ease;
}

[data-baseweb="tab"]:hover {
    background: #f8eee7;
    color: #692d35;
}

[data-baseweb="tab"][aria-selected="true"] {
    background:
        linear-gradient(
            135deg,
            #6a2c35,
            #8a3d46
        );

    color: #ffffff;

    box-shadow:
        0 5px 14px rgba(106,44,53,0.22);
}


/* =========================================
   KPI CARDS
========================================= */

[data-testid="stMetric"] {
    position: relative;

    background: #fffdf9;

    border: 1px solid #eadfd6;

    border-radius: 20px;

    padding: 22px;

    box-shadow:
        0 8px 24px rgba(80,45,35,0.07);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

[data-testid="stMetric"]::after {
    content: "";

    position: absolute;

    right: 0;
    top: 18px;
    bottom: 18px;

    width: 4px;

    border-radius: 5px 0 0 5px;

    background:
        linear-gradient(
            180deg,
            #a85d4c,
            #d6a05f
        );
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);

    box-shadow:
        0 14px 32px rgba(80,45,35,0.11);
}

[data-testid="stMetricLabel"] {
    color: #806b68;

    font-size: 0.9rem;

    font-weight: 600;
}

[data-testid="stMetricValue"] {
    direction: ltr;

    color: #4b2026;

    font-size: 1.7rem;

    font-weight: 800;
}

[data-testid="stMetricDelta"] {
    direction: ltr;
}


/* =========================================
   BUTTONS
========================================= */

.stButton > button {
    border-radius: 11px;

    border: 1px solid #71313b;

    background:glo
        linear-gradient(
            135deg,
            #71313b,
            #8c414b
        );

    color: white;

    font-weight: 650;

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

.stButton > button:hover {
    background:
        linear-gradient(
            135deg,
            #5d252e,
            #76343d
        );

    border-color: #5d252e;

    color: white;

    transform: translateY(-1px);

    box-shadow:
        0 6px 15px rgba(100,40,50,0.20);
}


/* =========================================
   DOWNLOAD BUTTON
========================================= */

.stDownloadButton > button {
    border-radius: 11px;

    border: 1px solid #dfc39f;

    background: #fbf0df;

    color: #6a3a2e;

    font-weight: 650;
}

.stDownloadButton > button:hover {
    background: #f5e3c9;
}


/* =========================================
   INPUTS
========================================= */

.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {
    border-radius: 11px;

    border-color: #e3d4ca;

    background: #fffdf9;
}


/* =========================================
   EXPANDERS
========================================= */

[data-testid="stExpander"] {
    background: #fffdf9;

    border: 1px solid #e7d9cf;

    border-radius: 15px;
}


/* =========================================
   DATAFRAME
========================================= */

[data-testid="stDataFrame"] {
    direction: ltr;

    border-radius: 14px;

    border: 1px solid #e3d6cc;

    overflow: hidden;
}


/* =========================================
   ALERTS
========================================= */

[data-testid="stAlert"] {
    border-radius: 13px;
}


/* =========================================
   DIVIDERS
========================================= */

hr {
    border-color: #e3d5ca;
}


/* =========================================
   PROGRESS
========================================= */

.stProgress > div > div {
    border-radius: 20px;
}


/* =========================================
   TAB OVERLAYS
========================================= */

[data-baseweb="tab-list"],
[data-baseweb="tab"] {
    position: relative;
    z-index: 10;
}

</style>
"""


def inject_style(theme: str = "warm"):
    st.markdown(
        RTL_CSS,
        unsafe_allow_html=True
    )