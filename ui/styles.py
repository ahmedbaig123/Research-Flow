"""Visual system for the ResearchFlow workspace."""

from __future__ import annotations

import streamlit as st


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');

        :root { --ink: #f1effb; --muted: #a09bb7; --line: rgba(191, 180, 238, .13); --violet: #8b72f6; }
        .stApp { background: #0d0c12; color: var(--ink); font-family: 'DM Sans', sans-serif; }
        .stApp::before { content: ''; position: fixed; inset: 0; pointer-events: none; background: radial-gradient(850px 480px at 65% -12%, rgba(100, 75, 210, .15), transparent 70%), radial-gradient(600px 500px at 0% 90%, rgba(62, 47, 121, .10), transparent 70%); }
        [data-testid="stSidebar"] { background: #111016; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding: 1.2rem .85rem; }
        [data-testid="stSidebarNav"] { display: none; }
        .block-container { max-width: 1220px; padding: 2.1rem 3.1rem 3rem; }
        h1, h2, h3, p { color: var(--ink); }
        .rf-brand { display: flex; align-items: center; gap: .7rem; margin: .15rem .35rem 1.65rem; }
        .rf-mark { display:grid; place-items:center; width: 31px; height:31px; border-radius: 9px; font-family:'Newsreader',serif; font-weight:600; font-size:18px; color:#fff; background:linear-gradient(145deg,#9f8bff,#6250bd); box-shadow:0 8px 24px rgba(116,91,238,.28); }
        .rf-brand-name { letter-spacing:-.035em; font-weight:700; font-size:1.05rem; }
        .rf-brand-name span { color:#a89bf2; font-weight:500; }
        .eyebrow { color:#978cc9; font-family:'DM Mono',monospace; font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.55rem; }
        .workspace-title { font-size:1.55rem; letter-spacing:-.045em; margin:0; font-weight:650; }
        .workspace-subtitle { color:var(--muted); margin:.32rem 0 1.6rem; font-size:.91rem; }
        .welcome { margin: 2.8rem 0 1.35rem; max-width: 660px; }
        .welcome h1 { font: 500 clamp(2rem,4vw,3.35rem)/1.05 'Newsreader', serif; margin:.2rem 0 .65rem; letter-spacing:-.045em; }
        .welcome p { color:#b0aac5; max-width:560px; line-height:1.55; font-size:1rem; }
        .panel { border:1px solid var(--line); background:rgba(23,21,31,.86); border-radius:14px; padding:1rem; box-shadow:0 16px 50px rgba(0,0,0,.13); }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line); background:rgba(23,21,31,.78); border-radius:14px; box-shadow:0 16px 50px rgba(0,0,0,.13); }
        .document-canvas { border:1px solid rgba(192,180,237,.14); background:linear-gradient(135deg,rgba(33,30,43,.96),rgba(22,20,29,.97)); border-radius:14px; padding:clamp(1.35rem, 4vw, 3.2rem); min-height:350px; box-shadow:0 18px 70px rgba(0,0,0,.17); }
        .document-canvas h1,.document-canvas h2,.document-canvas h3 { font-family:'Newsreader',serif; letter-spacing:-.025em; }
        .document-canvas p,.document-canvas li { color:#d6d2e3; line-height:1.78; font-size:1rem; }
        .document-canvas a { color:#b4a7ff; }
        .document-label { font:500 .68rem 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.09em; color:#968abf; border-bottom:1px solid var(--line); padding-bottom:.9rem; margin-bottom:1.4rem; }
        .meta { color:#938da9; font-size:.78rem; }
        .suggestion-note { color:#918aa6; font-size:.78rem; margin:.7rem 0 .5rem; }
        .status { display:flex; align-items:center; gap:.45rem; border-top:1px solid var(--line); margin-top:1.4rem; padding:.9rem .25rem 0; color:#aaa3bc; font-size:.76rem; }
        .dot { width:7px;height:7px;border-radius:50%;background:#6ddd9a; box-shadow:0 0 0 3px rgba(109,221,154,.11); }
        .dot.off { background:#d88989; box-shadow:0 0 0 3px rgba(216,137,137,.11); }
        .sidebar-heading { color:#8e87a2; font:500 .68rem 'DM Mono',monospace; letter-spacing:.09em; text-transform:uppercase; margin:1.6rem .35rem .55rem; }
        div[data-testid="stButton"] > button { border:1px solid rgba(178,164,244,.2); background:#201c2d; color:#eae6f7; border-radius:8px; min-height:2.45rem; font:500 .85rem 'DM Sans',sans-serif; transition:background .18s ease, border-color .18s ease, transform .18s ease; }
        div[data-testid="stButton"] > button:hover { background:#2a243b; border-color:rgba(178,164,244,.48); transform:translateY(-1px); color:#fff; }
        div[data-testid="stButton"] > button[kind="primary"] { background:linear-gradient(135deg,#8068e9,#6752cf); border-color:#907bf2; box-shadow:0 8px 20px rgba(101,78,205,.24); }
        div[data-testid="stButton"] > button[kind="primary"]:hover { background:linear-gradient(135deg,#917cf0,#725cdb); }
        .stTextArea textarea { background:#16141d !important; border:1px solid rgba(185,175,224,.17) !important; border-radius:10px !important; color:#eeebf8 !important; font-family:'DM Sans',sans-serif !important; line-height:1.5 !important; }
        .stTextArea textarea:focus { border-color:#8772e4 !important; box-shadow:0 0 0 3px rgba(135,114,228,.13) !important; }
        [data-testid="stDownloadButton"] > button { border-radius:8px; background:transparent; border:1px solid rgba(185,175,224,.2); color:#d9d5e8; min-height:2.2rem; }
        [data-testid="stExpander"] { border:1px solid var(--line); border-radius:10px; background:rgba(22,20,29,.62); }
        [data-testid="stToast"] { background:#262130; }
        .stAlert { border-radius:10px; }
        @media (max-width: 700px) { .block-container { padding:1.2rem 1rem 2rem; } .welcome { margin-top:1.5rem; } .document-canvas { padding:1.25rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
