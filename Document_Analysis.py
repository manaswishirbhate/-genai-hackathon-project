import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from streamlit_mic_recorder import mic_recorder

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="LegalEase - Document Analysis",
    page_icon="📑",
    layout="wide"
)

st.title("📑 LegalEase - Document Analysis Dashboard")

# --- 2. Configure API Key ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("🚨 GOOGLE_API_KEY not found! Add it to your Streamlit secrets.toml.", icon="🚨")
    st.stop()
except Exception as e:
    st.error(f"Error configuring GenAI: {e}", icon="🔥")
    st.stop()

# --- 3. Model Initialization ---
@st.cache_resource
def get_model():
    """Return a valid Gemini model."""
    # Replace with an available model from `genai.list_models()`
    try:
        return genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        st.stop()

model = get_model()

# --- 4. Helper Functions ---
def parse_document(uploaded_file):
    """Extracts text from PDF or TXT files."""
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                return "\n".join([page.get_text() for page in doc])
        else:
            st.error("Unsupported file type. Upload .txt or .pdf.", icon="🚫")
            return None
    except Exception as e:
        st.error(f"Error parsing file: {e}", icon="🔥")
        return None

@st.cache_data(show_spinner="Generating summary...")
def get_document_summary(doc_text, language):
    prompt = f"""
    Summarize this legal document in simple, easy-to-understand language.
    Focus on key obligations, rights, and potential risks.
    Translate the summary into {language}.

    DOCUMENT:
    {doc_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"API Error (Summary): {e}", icon="🔥")
        return None

@st.cache_data(show_spinner="Analyzing clauses...")
def get_clause_analysis(doc_text, language):
    prompt = f"""
    Extract and explain each major clause in this legal document.
    For each clause:
    - Title (if any)
    - Meaning in simple terms
    - Why it is important
    Translate entire analysis into {language}.

    DOCUMENT:
    {doc_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"API Error (Clauses): {e}", icon="🔥")
        return None

# --- 5. Sidebar UI ---
with st.sidebar:
    st.title("📘 LegalEase Settings")
    st.markdown("Upload a legal contract (.txt or .pdf) to analyze it.")

    language = st.selectbox(
        "Select Output Language:",
        ("English", "Spanish", "French", "German", "Japanese", "Hindi")
    )

    uploaded_file = st.file_uploader("📤 Upload Document", type=["txt", "pdf"])
    if uploaded_file:
        st.session_state.doc_text = parse_document(uploaded_file)
        if st.session_state.doc_text:
            st.success("✅ Document processed successfully!")

    st.divider()
    st.caption("Built for GenAI Exchange / Smart India Hackathon 2025 🚀")

# --- 6. Main UI ---
if "doc_text" not in st.session_state or not st.session_state.doc_text:
    st.info("👋 Upload a legal document to begin analysis.")
else:
    doc_text = st.session_state.doc_text
    summary = get_document_summary(doc_text, language)
    clauses = get_clause_analysis(doc_text, language)

    tab1, tab2, tab3 = st.tabs(["📄 Executive Summary", "📜 Clause Analysis", "💬 Chat with Document"])

    with tab1:
        st.header(f"Executive Summary ({language})")
        st.markdown(summary or "_No summary generated._")

    with tab2:
        st.header(f"Clause-by-Clause Analysis ({language})")
        st.markdown(clauses or "_No analysis available._")

    with tab3:
        st.header("Chat with Your Document")
        st.markdown(f"Ask questions about the contract. Responses in **{language}**.")
        st.divider()

        if "chat" not in st.session_state:
            st.session_state.chat = get_model().start_chat(history=[
                {"role": "user", "parts": [f"The user uploaded this legal document:\n{doc_text}"]},
                {"role": "model", "parts": ["Understood. Ready to answer questions."]}
            ])

        for message in st.session_state.chat.history[2:]:
            with st.chat_message(message.role):
                st.markdown(message.parts[0].text)

        st.write("🎙️ Ask with your voice:")
        audio_data = mic_recorder(start_prompt="Click to speak 🗣️", stop_prompt="Click to stop ⏹️", just_once=True)

        user_q = None
        if audio_data:
            st.audio(audio_data["bytes"])
            user_q = [
                genai.types.Part.from_data(audio_data["bytes"], mime_type="audio/wav"),
                "Answer this spoken question."
            ]
            display_content = "[User sent an audio question]"

        if text_q := st.chat_input("...or type your question here:"):
            user_q = [text_q]
            display_content = text_q

        if user_q:
            with st.chat_message("user"):
                st.markdown(display_content)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.chat.send_message(user_q)
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"API Error during chat: {e}", icon="🔥")

