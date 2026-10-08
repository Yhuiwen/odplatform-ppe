# English URL paths for three Streamlit pages

Date: 2026-10-07. Gate: PASS for navigation configuration.

The user showed URL bar paths encoded from Chinese page filenames. Streamlit `st.Page(url_path=...)` supports a URL pathname independent of the page title and script filename. The three pages now use `/Monitoring`, `/AI_Report`, and `/AI_Assistant`; their Chinese sidebar titles remain. Internal `st.switch_page` calls continue to use script paths and need no change. Existing bookmarks with Chinese paths should be updated to the English paths.

Focused `test_p9d_pages`, dashboard contract, and Agent Web boundary tests: 21 passed. The local server returned HTTP 200 for each new path. Because Streamlit can serve its shell on multiple paths, the HTTP response is an availability check, not a complete client-side routing proof. No API schema, event data, or monitoring pipeline changed.

Reference: [Streamlit `st.Page` documentation](https://docs.streamlit.io/1.55.0/develop/api-reference/navigation/st.page).
