import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
from streamlit_mic_recorder import mic_recorder # For Voice

# --- 1. Page Configuration & API Key ---
st.set_page_config(
    page_title="Document Analysis",
    page_icon="📄",
    layout="wide"
)

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("🚨 GOOGLE_API_KEY not found! Please add it to your Streamlit secrets.", icon="🚨")
    st.stop()
except Exception as e:
    st.error(f"Error configuring GenAI: {e}", icon="🔥")
    st.stop()

# --- 2. Model Initialization ---
@st.cache_resource
def get_model():
    """Returns the generative model."""
    return genai.GenerativeModel("gemini-1.5-flash")

model = get_model()

# --- 3. Helper Functions (These are still cached, which is good!) ---

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

@st.cache_data(show_spinner="Translating document summary...")
def get_document_summary(_doc_text, target_language): # <-- Still cached!
    """Generates a simple summary of the document in the target language."""
    if not _doc_text:
        return None
    
    prompt = f"""
    Summarize this legal document in simple, easy-to-understand plain English. 
    Focus on the key obligations, rights, and any potential risks.
    
    IMPORTANT: After your analysis, translate the *entire* final summary into {target_language}.
    
    DOCUMENT:
    {_doc_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"API Error (Summary): {e}", icon="🔥")
        return None

@st.cache_data(show_spinner="Translating clause analysis...")
def get_clause_analysis(_doc_text, target_language): # <-- Still cached!
    """Generates a clause-by-clause breakdown in the target language."""
    if not _doc_text:
        return None
    
    prompt = f"""
    Extract and explain each major clause from this legal document. 
    For each clause, provide its title (if any), a simple explanation of what it means, and why it is important.
    
    IMPORTANT: After your analysis, translate the *entire* breakdown into {target_language}.
    
    DOCUMENT:
    {_doc_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"API Error (Clauses): {e}", icon="🔥")
        return None

# --- 4. Session State Initialization & Callbacks ---
if "doc_text" not in st.session_state:
    st.session_state.doc_text = None
if "chat" not in st.session_state:
    st.session_state.chat = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None

# Callback function to clear chat when language changes
def clear_chat_session():
    """Clears the chat session from state."""
    st.session_state.chat = None

# --- 5. Sidebar UI (With the fixes) ---
with st.sidebar:
    st.title("📄 Document Analysis")
    st.markdown("Upload a legal contract (.txt or .pdf) to get instant insights.")
    
    st.divider()
    
    # Added on_change callback
    language = st.sidebar.selectbox(
        "Select Analysis Language",
        ("English", "Spanish", "French", "German", "Japanese", "Hindi"),
        on_change=clear_chat_session # <-- This resets the chat
    )
    
    uploaded_file = st.file_uploader(
        "Upload your document",
        type=["txt", "pdf"],
        help="We support .txt and .pdf files."
    )
    
    # This block is now simpler
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.file_name:
            st.session_state.file_name = uploaded_file.name
            st.info("Parsing document...")
            
            # 1. Parse the document
            doc_text = parse_document(uploaded_file)
            
            if doc_text:
                # 2. Store the text
                st.session_state.doc_text = doc_text
                # 3. Clear the chat (new file)
                clear_chat_session()
                st.success("Document processed! 🎉", icon="✅")
            else:
                st.session_state.doc_text = None
                
    st.divider()
    st.info("Built for the GenAI Exchange Hackathon 🚀")

# --- 6. Main Page UI (With the fixes) ---

st.title("📑 Document Analysis Dashboard")

if st.session_state.doc_text is None:
    st.info("👋 Welcome! Please upload a legal document using the sidebar to get started.")
else:
    # Run generation *here* instead of in the sidebar
    # The cache ensures this only runs the AI when 'doc_text' or 'language' changes.
    summary_text = get_document_summary(st.session_state.doc_text, language)
    clauses_text = get_clause_analysis(st.session_state.doc_text, language)
    
    tab1, tab2, tab3 = st.tabs(["📄 Executive Summary", "🔍 Clause-by-Clause", "🤖 AI Chat Q&A"])

    with tab1:
        st.header(f"Executive Summary (in {language})")
        st.markdown(summary_text or "Could not generate summary.")

    with tab2:
        st.header(f"Clause-by-Clause Analysis (in {language})")
        st.markdown(clauses_text or "Could not generate clause analysis.")

    # --- TAB 3: This logic is now fast and correct ---
    with tab3:
        st.header("Chat with Your Document")
        st.markdown(f"Ask specific questions. The AI will respond in **{language}**.")
        st.divider()

        # Check for 'chat' being None
        if "chat" not in st.session_state or st.session_state.chat is None:
            st.info(f"Initializing chat session in {language}...")
            try:
                chat_model = get_model()
                st.session_state.chat = chat_model.start_chat(
                    history=[
                        {
                            "role": "user",
                            "parts": [
                                f"""You are a helpful legal AI assistant. The user has provided the following document. 
                                Your job is to answer their questions based *only* on the content of this document. 
                                If the answer is not in the document, say so.
                                
                                The user's preferred language is {language}. Please respond in {language}.
                                
                                --- DOCUMENT TEXT --- 
                                {st.session_state.doc_text}
                                """
                            ]
                        },
                        {
                            "role": "model",
                            "parts": [f"Understood. I have read the document and am ready to answer your questions in {language}."]
                        }
                    ]
                )
                st.rerun() 
            except Exception as e:
                st.error(f"Failed to initialize chat: {e}")
                st.stop()

        # Display existing chat messages (skipping the first context-setting messages)
        for message in st.session_state.chat.history[2:]: 
            with st.chat_message(message.role):
                st.markdown(message.parts[0].text)

        # --- VOICE INPUT WIDGET ---
        st.write("Ask with your voice:")
        audio_data = mic_recorder(
            start_prompt="Click to speak 🗣️",
            stop_prompt="Click to stop ⏹️",
            just_once=True,
            key='audio_recorder'
        )

        user_q = None # Initialize user_q

        if audio_data:
            st.audio(audio_data["bytes"])
            # --- THIS IS THE CORRECTED LINE ---
            user_q = [
                genai.types.Part.from_data(audio_data["bytes"], mime_type="audio/wav"),
                "Please answer this spoken question."
            ]
            display_content = "[User sent an audio question]"
        
        if text_q := st.chat_input("...or type your question here:"):
            user_q = [text_q] # Send as a list
            display_content = text_q
        
        if user_q:
            with st.chat_message("user"):
                st.markdown(display_content)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # This 'send_message' call is now very fast
                        response = st.session_state.chat.send_message(user_q)
                        ai_response = response.text
                    except Exception as e:
                        ai_response = f"Sorry, I encountered an API error: {e}"
                    
                    st.markdown(ai_response)