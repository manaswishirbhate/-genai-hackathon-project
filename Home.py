import streamlit as st

st.set_page_config(
    page_title="LegalEase- GenAI Legal Assistant",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ Welcome to LegalEase!")
st.subheader("Your GenAI-Powered Legal Assistant")

st.markdown("""

It's designed to help anyone understand complex legal documents quickly and easily.

---

### Features:

* **📄 Document Analysis:** Upload a contract to get a simple summary, a clause-by-clause breakdown, and chat with your document using text or voice.
* **⚖️ Contract Comparison:** Upload two different contracts to get a high-level comparison of their key differences.

**Navigate to a feature using the sidebar on the left to get started!**
""")

st.sidebar.success("Select a feature above.")

st.sidebar.divider()