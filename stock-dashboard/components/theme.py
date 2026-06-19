"""Design system: color tokens, typography and global CSS injection.

A single source of truth for the look and feel. Two palettes (light/dark) share
the same violet→indigo gradient signature so the brand reads consistently across
modes. The :func:`inject` function writes the CSS once per render.
"""

from __future__ import annotations

import streamlit as st

# --- Brand tokens -----------------------------------------------------------
# Signature accent: a violet→indigo gradient used on the rail, primary numbers
# and active states. Everything else stays quiet so the accent carries identity.
GRADIENT = "linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)"
ACCENT = "#6D28D9"
ACCENT_SOFT = "#8B5CF6"

POSITIVE = "#16A34A"
NEGATIVE = "#DC2626"
NEUTRAL = "#6366F1"

LIGHT = {
    "bg": "#F5F6FA",
    "surface": "#FFFFFF",
    "text": "#0F172A",
    "muted": "#64748B",
    "border": "#E5E7EB",
    "shadow": "0 1px 3px rgba(16,24,40,.06), 0 8px 24px rgba(16,24,40,.04)",
}

DARK = {
    "bg": "#0B1020",
    "surface": "#141A2E",
    "text": "#E8ECF6",
    "muted": "#94A3B8",
    "border": "#26304B",
    "shadow": "0 1px 3px rgba(0,0,0,.4), 0 12px 32px rgba(0,0,0,.35)",
}


def palette(dark: bool) -> dict:
    """Return the active token set for the requested mode."""
    return DARK if dark else LIGHT


def plotly_template(dark: bool) -> str:
    """Map the mode onto a Plotly base template name."""
    return "plotly_dark" if dark else "plotly_white"


def inject(dark: bool = False) -> None:
    """Inject the global stylesheet for the chosen mode.

    Styles native Streamlit containers so cards, metrics and the sidebar pick up
    the brand without bespoke HTML on every page.
    """
    c = palette(dark)
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

    .stApp {{
        background: {c['bg']};
        color: {c['text']};
        font-family: 'Inter', -apple-system, system-ui, sans-serif;
    }}
    h1, h2, h3, h4 {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
        letter-spacing: -0.02em;
        color: {c['text']};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {c['surface']};
        border-right: 1px solid {c['border']};
    }}
    section[data-testid="stSidebar"] .stRadio label {{ color: {c['text']}; }}

    /* Card surface applied to bordered containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {c['surface']};
        border: 1px solid {c['border']} !important;
        border-radius: 18px !important;
        box-shadow: {c['shadow']};
        padding: 4px 6px;
    }}

    /* Native metric cards */
    div[data-testid="stMetric"] {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: {c['shadow']};
    }}
    div[data-testid="stMetricLabel"] {{
        color: {c['muted']};
        font-weight: 600;
        font-size: .82rem;
        text-transform: uppercase;
        letter-spacing: .04em;
    }}
    div[data-testid="stMetricValue"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        color: {c['text']};
    }}

    /* Brand banner */
    .brand-banner {{
        background: {GRADIENT};
        border-radius: 20px;
        padding: 26px 30px;
        color: #fff;
        margin-bottom: 6px;
        box-shadow: 0 10px 30px rgba(79,70,229,.35);
    }}
    .brand-banner h1 {{ color:#fff; margin:0; font-size:1.7rem; }}
    .brand-banner p  {{ color:rgba(255,255,255,.85); margin:.3rem 0 0; }}

    /* Section eyebrow */
    .eyebrow {{
        display:inline-block; font-size:.72rem; font-weight:700;
        letter-spacing:.14em; text-transform:uppercase;
        color:{ACCENT_SOFT}; margin-bottom:.2rem;
    }}

    /* Pills */
    .pill {{
        display:inline-block; padding:4px 12px; border-radius:999px;
        font-size:.78rem; font-weight:700;
    }}
    .pill-pos {{ background:rgba(22,163,74,.12); color:{POSITIVE}; }}
    .pill-neg {{ background:rgba(220,38,38,.12); color:{NEGATIVE}; }}
    .pill-neu {{ background:rgba(99,102,241,.12); color:{NEUTRAL}; }}

    /* Insight row */
    .insight {{
        display:flex; gap:14px; align-items:flex-start;
        padding:14px 16px; border-radius:14px; margin-bottom:10px;
        background:{c['bg']}; border:1px solid {c['border']};
    }}
    .insight .ic {{ font-size:1.4rem; line-height:1; }}
    .insight .tt {{ font-weight:700; color:{c['text']}; margin:0; }}
    .insight .dd {{ color:{c['muted']}; font-size:.9rem; margin:.15rem 0 0; }}

    /* News */
    .news-item {{ padding:12px 0; border-bottom:1px solid {c['border']}; }}
    .news-item a {{ color:{c['text']}; font-weight:600; text-decoration:none; }}
    .news-item a:hover {{ color:{ACCENT}; }}
    .news-meta {{ color:{c['muted']}; font-size:.8rem; margin-top:2px; }}

    .stButton button {{
        border-radius:12px; font-weight:600; border:1px solid {c['border']};
    }}
    #MainMenu, footer {{ visibility:hidden; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def banner(title: str, subtitle: str) -> None:
    """Render the gradient hero banner used at the top of each page."""
    st.markdown(
        f"<div class='brand-banner'><h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def section(eyebrow: str, heading: str) -> None:
    """Render a consistent section header with an eyebrow label."""
    st.markdown(f"<div class='eyebrow'>{eyebrow}</div>", unsafe_allow_html=True)
    st.markdown(f"### {heading}")
