# Chinese native Streamlit shell

Date: 2026-10-08. Targeted presentation gate: PASS.

The requested native menu and deployment chooser now display Chinese text. `web/ui/shell_zh.js` translates an explicit dictionary inside `stToolbar`, `stMainMenuPopover`, and the native deployment dialog identified by its deployment icons. It updates text-node data and accessibility attributes rather than replacing elements. A single observer per browser document reapplies translations to newly opened UI and React updates. `shell_localization.py` loads only trusted repository-owned JavaScript via `st.html`; there is no user data interpolation. The existing shared theme mounts this on all pages.

Browser verification on the running app confirmed Chinese menu/theme/footer text and every deployment description/action label. Rerun and deployment chooser open/close succeeded after translation. Focused page and Agent Web boundary tests: 19 passed. No actual deployment, recording or printing was performed. Third-party product names remain proper nouns. Frontend selectors need review if Streamlit is upgraded.

Evidence: [menu](P9D_CHINESE_SHELL_MENU.png), [deployment chooser](P9D_CHINESE_SHELL_DEPLOY.png).

Reference: [official st.html API](https://docs.streamlit.io/develop/api-reference/text/st.html).
