"""Chinese presentation for the Streamlit toolbar and deployment dialog."""

from pathlib import Path

import streamlit as st


def localize_streamlit_shell() -> None:
    script = Path(__file__).with_name("shell_zh.js").read_text(encoding="utf-8")
    # Only repository-owned static code is executed; no user or API text is injected.
    st.html(
        '<span class="ppe-shell-localization" hidden></span>'
        '<style>[data-testid="stElementContainer"]:has(.ppe-shell-localization)'
        '{display:none}</style>'
        f"<script>{script}</script>",
        unsafe_allow_javascript=True,
    )
