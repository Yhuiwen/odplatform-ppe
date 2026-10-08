"""Centralized visual system for the Streamlit shell."""

import streamlit as st


def configure_page():
    st.set_page_config(page_title="PPE Safety Operations", page_icon="🦺", layout="wide", initial_sidebar_state="expanded")


def inject_global_styles():
    from web.ui.shell_localization import localize_streamlit_shell

    localize_streamlit_shell()
    st.markdown("""<style>
    :root{--navy:#14283f;--slate:#52657a;--line:#dbe3ec;--surface:#fff}
    .block-container{max-width:1540px;padding-top:1.5rem;padding-bottom:2rem}
    [data-testid="stSidebar"]{background:#14283f}
    [data-testid="stSidebar"] *{color:#edf4fb}
    [data-testid="stSidebarNav"]{padding-top:.5rem}
    .brand{padding:1.2rem .2rem 1rem;border-bottom:1px solid #35506a;margin-bottom:.8rem}
    .brand strong{display:block;font-size:1.08rem;line-height:1.35}
    .brand small{display:block;color:#b7c9da;margin-top:.3rem}
    .sidebar-status{margin-top:1rem;color:#b7c9da;font-size:.78rem}
    .sidebar-foot{margin-top:1.5rem;border-top:1px solid #35506a;padding-top:.9rem;color:#a8bfd3;font-size:.72rem}
    .page-kicker{font-size:.66rem;font-weight:700;letter-spacing:.13em;color:#c66a3c}
    .page-title{font-size:1.72rem;line-height:1.3;margin:.15rem 0 .1rem;color:#14283f;font-weight:750}
    .page-subtitle{font-size:.88rem;color:#65768a;margin:0 0 1.3rem}
    .section-title{font-size:1.04rem;margin:.7rem 0 .15rem;color:#14283f}
    .section-caption{font-size:.78rem;color:#6d7e90;margin:0 0 .45rem}
    .kpi-card{background:#fff;border:1px solid var(--line);border-top:3px solid #315c89;border-radius:10px;padding:.8rem 1rem;min-height:112px;box-shadow:0 2px 8px #14283f08}
    .kpi-card.red{border-top-color:#ca594c}.kpi-card.amber{border-top-color:#d49a3c}.kpi-card.green{border-top-color:#2f9b73}
    .kpi-top{display:flex;justify-content:space-between;color:#607187;font-size:.78rem;font-weight:600}
    .kpi-value{font-size:1.75rem;font-weight:750;color:#14283f;line-height:1.25;margin-top:.2rem}
    .kpi-detail{font-size:.7rem;color:#8190a0}
    .status-badge{display:inline-block;border-radius:999px;padding:.3rem .7rem;font-size:.78rem;background:#edf1f5;color:#5d6d7e;font-weight:650}
    .status-badge.green{background:#e5f5ed;color:#217b55}.status-badge.red{background:#fdebe8;color:#ae463b}.status-badge.amber{background:#fff2d9;color:#9b6a16}.status-badge.blue{background:#e8f0fa;color:#315c89}
    .empty-state{border:1px dashed #cad5e1;background:#f8fafc;border-radius:10px;min-height:120px;padding:1.1rem;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#64758a;text-align:center;gap:.15rem}
    .empty-state strong{color:#344b64;font-size:.9rem}.empty-state small{font-size:.76rem}.empty-icon{font-size:1.4rem;color:#8da5bd}
    .note-card{background:#f5f8fc;border-left:3px solid #315c89;padding:.8rem 1rem;border-radius:6px;color:#42566e;font-size:.85rem;margin-bottom:1rem}
    .preview-empty{aspect-ratio:16/9;min-height:220px;background:#17283b;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#cbd7e3}
    .preview-empty strong{color:#fff}.preview-empty small{margin-top:.3rem}
    .overview-hero{display:flex;justify-content:space-between;align-items:center;gap:1.5rem;padding:1.35rem 1.6rem;margin:.2rem 0 1rem;border-radius:14px;background:linear-gradient(115deg,#152d48,#244d73);color:#fff;box-shadow:0 8px 22px #14283f24}
    .overview-eyebrow{font-size:.72rem;letter-spacing:.12em;color:#bdd7eb;font-weight:700}
    .overview-hero h2{font-size:1.5rem;line-height:1.25;margin:.3rem 0;color:#fff}
    .overview-hero p{font-size:.83rem;color:#d7e6f1;margin:0}
    .overview-hero-number{display:flex;flex-direction:column;align-items:center;min-width:110px;padding:.25rem 0;border-left:1px solid #ffffff42}
    .overview-hero-number strong{font-size:2.6rem;line-height:1;font-weight:800}
    .overview-hero-number span{font-size:.72rem;color:#d7e6f1;margin-top:.35rem}
    button[kind="primary"]{background:#315c89;border-color:#315c89;color:#fff}
    button[kind="primary"]:hover{background:#24496f;border-color:#24496f;color:#fff}
    @media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.page-title{font-size:1.42rem}.kpi-card{min-height:95px}.overview-hero{padding:1rem}.overview-hero h2{font-size:1.2rem}.overview-hero-number strong{font-size:2rem}}
    </style>""", unsafe_allow_html=True)
