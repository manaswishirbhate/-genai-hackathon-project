import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF for reading PDFs
import io

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

# --- 3. Model Initialization ---
@st.cache_resource
def get_model():
    """Safely load Gemini model with fallback in case of mismatch."""
    try:
        return genai.GenerativeModel(model_name="models/gemini-1.5-flash")
    except Exception as e:
        st.warning(f"⚠️ Falling back to Gemini 1.5 Pro due to: {e}")
        return genai.GenerativeModel(model_name="models/gemini-1.5-pro")

model = get_model()

# --- 4. Helper Function ---
def parse_document(uploaded_file):
    """Parses the uploaded file (TXT or PDF) and returns its text content."""
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                return text
        else:
            st.error("Unsupported file type. Please upload a .txt or .pdf file.", icon="🚫")
            return None
    except Exception as e:
        st.error(f"Error parsing file: {e}", icon="🔥")
        return None

# --- 5. UI Layout ---
col1, col2 = st.columns(2)
doc_1_text = None
doc_2_text = None

with col1:
    st.subheader("📄 Document 1")
    file_1 = st.file_uploader("Upload first contract", type=["txt", "pdf"], key="file1")
    if file_1:
        doc_1_text = parse_document(file_1)
        with st.expander("🔍 Preview Document 1"):
            st.write(doc_1_text[:2000] + "..." if doc_1_text else "No text extracted.")

with col2:
    st.subheader("📄 Document 2")
    file_2 = st.file_uploader("Upload second contract", type=["txt", "pdf"], key="file2")
    if file_2:
        doc_2_text = parse_document(file_2)
        with st.expander("🔍 Preview Document 2"):
            st.write(doc_2_text[:2000] + "..." if doc_2_text else "No text extracted.")

st.divider()

# --- 6. Comparison Logic ---
if doc_1_text and doc_2_text:
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
                {doc_1_text}

                --- DOCUMENT 2 ---
                {doc_2_text}
                """

                response = model.generate_content(prompt)
                st.success("✅ Comparison complete!")
                st.markdown("### 📘 Comparison Report")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"API Error during comparison: {e}", icon="🔥")
else:
    st.info("Please upload both contracts to enable comparison.", icon="📂")
