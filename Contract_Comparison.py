import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io

# --- 1. Page Configuration & API Key ---
st.set_page_config(page_title="Compare Contracts", page_icon="⚖️", layout="wide")
st.title("⚖️ Contract Comparison")
st.markdown("Upload two contracts to see a side-by-side analysis of their key differences.")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("🚨 GOOGLE_API_KEY not found! Please add it to your Streamlit secrets.", icon="🚨")
    st.stop()

# --- 2. Model Initialization ---
@st.cache_resource
def get_model():
    """Returns the generative model."""
    return genai.GenerativeModel("gemini-1.5-flash")

model = get_model()

# --- 3. Helper Function ---
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
        return None
    except Exception as e:
        st.error(f"Error parsing file: {e}", icon="🔥")
        return None

# --- 4. Comparison Page UI ---

doc_1_text = None
doc_2_text = None

col1, col2 = st.columns(2)

with col1:
    st.subheader("Document 1")
    file_1 = st.file_uploader("Upload first contract", type=["txt", "pdf"], key="file1")
    if file_1:
        doc_1_text = parse_document(file_1)
        with st.expander("Show Document 1 Text"):
            st.write(doc_1_text[:2000] + "...") # Show preview

with col2:
    st.subheader("Document 2")
    file_2 = st.file_uploader("Upload second contract", type=["txt", "pdf"], key="file2")
    if file_2:
        doc_2_text = parse_document(file_2)
        with st.expander("Show Document 2 Text"):
            st.write(doc_2_text[:2000] + "...") # Show preview

st.divider()

if doc_1_text and doc_2_text:
    if st.button("Compare Documents", type="primary", use_container_width=True):
        with st.spinner("Comparing contracts... This may take a minute."):
            try:
                # The "Magic" Comparison Prompt
                prompt = f"""
                You are a legal analyst AI. Compare the two legal documents provided.
                Identify the key differences, focusing on critical clauses like:
                - Term and Termination
                - Payment Obligations & Amounts
                - Liability and Indemnification
                - Confidentiality
                - Governing Law & Jurisdiction
                - Scope of Work or Deliverables

                Present your analysis in a clear, easy-to-read markdown format.
                Use bullet points for clarity. Start with a high-level summary.

                --- DOCUMENT 1 (Excerpt) ---
                {doc_1_text}

                --- DOCUMENT 2 (Excerpt) ---
                {doc_2_text}
                """
                response = model.generate_content(prompt)
                st.markdown("### Comparison Report")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"API Error during comparison: {e}", icon="🔥")
else:
    st.info("Please upload both documents to enable comparison.")