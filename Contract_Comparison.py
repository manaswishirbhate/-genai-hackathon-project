import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF

# --- 1. Page Configuration ---
st.set_page_config(page_title="Compare Contracts", page_icon="⚖️", layout="wide")
st.title("⚖️ Contract Comparison")
st.markdown("Upload two contracts to analyze and compare their key clauses and differences.")

# --- 2. API Key Setup ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("🚨 GOOGLE_API_KEY not found! Please add it to your Streamlit secrets.toml file.", icon="🚨")
    st.stop()
except Exception as e:
    st.error(f"Error configuring GenAI: {e}", icon="🔥")
    st.stop()

# --- 3. Model Initialization ---
@st.cache_resource
def get_model():
    """Return the generative model (use a supported Gemini model)."""
    return genai.GenerativeModel("gemini-1.5")  # Use supported model name

model = get_model()

# --- 4. Helper Function ---
def parse_document(uploaded_file):
    """Parses TXT or PDF files and returns text."""
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                text = ""
                for page in doc:
                    try:
                        text += page.get_text()
                    except:
                        continue
                return text
        else:
            st.error("Unsupported file type. Please upload a .txt or .pdf file.", icon="🚫")
            return None
    except Exception as e:
        st.error(f"Error parsing file: {e}", icon="🔥")
        return None

# --- 5. Session State for Uploaded Files ---
if "doc_1_text" not in st.session_state:
    st.session_state.doc_1_text = None
if "doc_2_text" not in st.session_state:
    st.session_state.doc_2_text = None

# --- 6. Upload UI ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Document 1")
    file_1 = st.file_uploader("Upload first contract", type=["txt", "pdf"], key="file1")
    if file_1:
        st.session_state.doc_1_text = parse_document(file_1)
        with st.expander("🔍 Preview Document 1"):
            st.write(st.session_state.doc_1_text[:2000] + "..." if st.session_state.doc_1_text else "No text extracted.")

with col2:
    st.subheader("📄 Document 2")
    file_2 = st.file_uploader("Upload second contract", type=["txt", "pdf"], key="file2")
    if file_2:
        st.session_state.doc_2_text = parse_document(file_2)
        with st.expander("🔍 Preview Document 2"):
            st.write(st.session_state.doc_2_text[:2000] + "..." if st.session_state.doc_2_text else "No text extracted.")

st.divider()

# --- 7. Comparison Logic ---
if st.session_state.doc_1_text and st.session_state.doc_2_text:
    if st.button("🔎 Compare Documents", type="primary", use_container_width=True):
        with st.spinner("Comparing contracts... Please wait ⏳"):
            try:
                prompt = f"""
You are a legal analyst AI. Compare the two legal documents below.
Focus on key differences in clauses such as:
- Term and Termination
- Payment Obligations & Amounts
- Liability and Indemnification
- Confidentiality
- Governing Law & Jurisdiction
- Scope of Work or Deliverables

Output a professional, well-structured markdown report with:
1. A high-level summary of differences.
2. Clause-by-clause comparison.
3. Highlight any missing or conflicting terms.

--- DOCUMENT 1 ---
{st.session_state.doc_1_text}

--- DOCUMENT 2 ---
{st.session_state.doc_2_text}
"""
                response = model.generate_content(prompt)
                st.success("✅ Comparison complete!")
                st.markdown("### 📘 Comparison Report")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"API Error during comparison: {e}", icon="🔥")
else:
    st.info("Please upload both contracts to enable comparison.", icon="📂")
