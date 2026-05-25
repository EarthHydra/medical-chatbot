"""
Nayi Disha — Trauma-Informed AI Support Chatbot
A compassionate chat companion for survivors of abuse.
Built with Streamlit, LangChain, FAISS, and Groq.
"""

import os
import re
import streamlit as st

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from prompts import CHAT_PROMPT_TEMPLATE, WELCOME_MESSAGE, CRISIS_RESOURCES
from trauma_classifier import (
    init_session_profile,
    classify_message,
    update_session_profile,
    render_session_insights,
)

# Try to load .env for local development
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass


# ─────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nayi Disha — A New Direction",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────
# Custom CSS — Professional, Soothing, Warm Design
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Outfit', sans-serif;
    }

    /* ── Main container — deep calming teal-black gradient ── */
    .stApp {
        background: linear-gradient(160deg, #0b1a1a 0%, #0f2424 25%, #0d1f1f 50%, #0a1616 100%);
    }

    /* ── Header ── */
    .nd-header {
        text-align: center;
        padding: 2rem 1rem 1.2rem;
        margin-bottom: 0.5rem;
    }
    .nd-header .nd-icon {
        font-size: 2.4rem;
        margin-bottom: 0.3rem;
        display: block;
        animation: gentlePulse 4s ease-in-out infinite;
    }
    .nd-header h1 {
        background: linear-gradient(135deg, #5eadad 0%, #7ec8c8 35%, #a8dcd0 70%, #5eadad 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'Outfit', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
        letter-spacing: -0.5px;
    }
    .nd-header .nd-subtitle {
        color: #7ec8c8;
        font-size: 0.88rem;
        font-weight: 300;
        font-style: italic;
        opacity: 0.85;
        letter-spacing: 0.3px;
    }
    .nd-header .nd-tagline {
        color: #8fb8b0;
        font-size: 0.82rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.7;
    }

    @keyframes gentlePulse {
        0%, 100% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.05); opacity: 1; }
    }

    /* ── Chat message styling ── */
    .stChatMessage {
        border-radius: 18px !important;
        margin-bottom: 0.85rem !important;
        border: 1px solid rgba(94, 173, 173, 0.06) !important;
        animation: fadeInUp 0.45s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(14px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* ── User message — soft warm rose tint ── */
    [data-testid="stChatMessage"][aria-label="user"] {
        background: linear-gradient(135deg, rgba(173, 124, 124, 0.10) 0%, rgba(140, 100, 100, 0.06) 100%) !important;
        border: 1px solid rgba(173, 124, 124, 0.10) !important;
    }

    /* ── Assistant message — glassmorphism teal ── */
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background: rgba(14, 30, 30, 0.65) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(94, 173, 173, 0.10) !important;
    }

    /* ── Chat input ── */
    .stChatInput {
        border-radius: 28px !important;
    }
    .stChatInput > div {
        border-radius: 28px !important;
        border: 1.5px solid rgba(94, 173, 173, 0.20) !important;
        background: rgba(14, 30, 30, 0.75) !important;
        transition: border-color 0.35s ease, box-shadow 0.35s ease;
    }
    .stChatInput > div:focus-within {
        border-color: rgba(94, 173, 173, 0.45) !important;
        box-shadow: 0 0 24px rgba(94, 173, 173, 0.10) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1a1a 0%, #091414 100%) !important;
        border-right: 1px solid rgba(94, 173, 173, 0.08);
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #7ec8c8;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 1rem;
    }

    /* ── Sidebar brand block ── */
    .sidebar-brand {
        text-align: center;
        padding: 1rem 0.5rem 0.6rem;
    }
    .sidebar-brand .brand-icon {
        font-size: 1.6rem;
        margin-bottom: 0.2rem;
    }
    .sidebar-brand h2 {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #5eadad, #a8dcd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 0;
    }
    .sidebar-brand p {
        color: #6ea8a0;
        font-size: 0.72rem;
        font-style: italic;
        margin: 0;
        opacity: 0.8;
    }

    /* ── Crisis resource card ── */
    .crisis-card {
        background: linear-gradient(135deg, rgba(220, 80, 80, 0.08) 0%, rgba(180, 60, 60, 0.04) 100%);
        border: 1px solid rgba(220, 80, 80, 0.15);
        border-radius: 14px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.3s ease, background 0.3s ease;
    }
    .crisis-card:hover {
        border-color: rgba(220, 80, 80, 0.30);
        background: linear-gradient(135deg, rgba(220, 80, 80, 0.12) 0%, rgba(180, 60, 60, 0.06) 100%);
    }
    .crisis-card p {
        margin: 0;
        font-size: 0.84rem;
    }
    .crisis-card .hotline-name {
        color: #e8a0a0;
        font-weight: 500;
    }
    .crisis-card .hotline-number {
        color: #f0c0c0;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
    }

    /* ── Disclaimer box ── */
    .disclaimer-box {
        background: rgba(94, 173, 173, 0.05);
        border: 1px solid rgba(94, 173, 173, 0.10);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-top: 1rem;
    }
    .disclaimer-box p {
        color: #7eb8b0;
        font-size: 0.76rem;
        margin: 0;
        line-height: 1.55;
        opacity: 0.8;
    }

    /* ── Insight section ── */
    .insight-section {
        background: rgba(94, 173, 173, 0.05);
        border: 1px solid rgba(94, 173, 173, 0.10);
        border-radius: 14px;
        padding: 1rem;
        margin-top: 0.75rem;
    }

    /* ── Expander styling ── */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        color: #7ec8c8 !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {
        width: 5px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(94, 173, 173, 0.25);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(94, 173, 173, 0.45);
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 14px !important;
        border: 1px solid rgba(94, 173, 173, 0.20) !important;
        background: rgba(94, 173, 173, 0.08) !important;
        color: #a8dcd0 !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        border-color: rgba(94, 173, 173, 0.40) !important;
        background: rgba(94, 173, 173, 0.15) !important;
        box-shadow: 0 4px 16px rgba(94, 173, 173, 0.10) !important;
    }

    /* ── Progress bars ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #5eadad, #7ec8c8) !important;
        border-radius: 8px !important;
    }

    /* ── Hide default Streamlit branding ── */
    #MainMenu {visibility: hidden;}
    /* header {visibility: hidden;}  <- Commented out so the sidebar expand button remains visible */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Vectorstore Loading (Cached)
# ─────────────────────────────────────────────────────────────
DB_FAISS_PATH = "vectorstore/db_counseling"

@st.cache_resource
def get_vectorstore():
    """Load the FAISS vectorstore with counseling embeddings."""
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    db = FAISS.load_local(
        DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True
    )
    return db


def get_groq_api_key() -> str:
    """Get Groq API key from environment or Streamlit secrets."""
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    # Fall back to environment variable
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    # If still not found, show error
    st.error(
        "🔑 **GROQ_API_KEY not found.** Please set it in your `.env` file "
        "or in Streamlit secrets. See the README for setup instructions."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
def render_sidebar():
    """Render the sidebar with crisis resources and session insights."""
    with st.sidebar:
        # Brand block
        st.markdown(
            """<div class="sidebar-brand">
                <div class="brand-icon">🌿</div>
                <h2>Nayi Disha</h2>
                <p>A new direction towards healing</p>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Crisis Resources
        st.markdown("### 🆘 Crisis Resources")
        st.markdown(
            '<p style="color: #e8a0a0; font-size: 0.82rem; margin-bottom: 0.75rem;">'
            "If you're in immediate danger, please reach out:</p>",
            unsafe_allow_html=True,
        )

        for name, number in CRISIS_RESOURCES.items():
            st.markdown(
                f"""<div class="crisis-card">
                    <p class="hotline-name">{name}</p>
                    <p class="hotline-number">📞 {number}</p>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Session Insights
        st.markdown("### 🔍 Session Insights")
        render_session_insights()

        # Disclaimer
        st.markdown(
            """<div class="disclaimer-box">
                <p>⚠️ <strong>Disclaimer:</strong> Nayi Disha is an AI support tool and 
                does <strong>not</strong> replace professional counseling, therapy, or 
                legal advice. If you are in danger, please contact emergency services 
                immediately. All conversations are processed in real-time and are 
                <strong>not stored</strong> after your session ends.</p>
            </div>""",
            unsafe_allow_html=True,
        )

        # New session button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Start New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.trauma_profile = None
            st.rerun()


# ─────────────────────────────────────────────────────────────
# Main Chat Interface
# ─────────────────────────────────────────────────────────────
def main():
    # Initialize
    init_session_profile()
    render_sidebar()

    # Header
    st.markdown(
        """<div class="nd-header">
            <span class="nd-icon">🌿</span>
            <h1>Nayi Disha</h1>
            <p class="nd-subtitle">A new direction towards healing</p>
            <p class="nd-tagline">You are safe here. You are heard. You are not alone.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show welcome message if no messages yet
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🌿"):
            st.markdown(WELCOME_MESSAGE)

    # Display chat history
    for message in st.session_state.messages:
        avatar = "🌿" if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar if message["role"] == "assistant" else None):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Share what's on your mind... I'm here to listen 🌿")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get API key
        groq_api_key = get_groq_api_key()

        # Generate response
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner(""):
                try:
                    # Load vectorstore
                    vectorstore = get_vectorstore()

                    # Build RAG chain using modern LangChain approach
                    prompt = PromptTemplate(
                        template=CHAT_PROMPT_TEMPLATE,
                        input_variables=["context", "question"],
                    )

                    llm = ChatGroq(
                        model_name="llama-3.3-70b-versatile",
                        temperature=0.3,
                        groq_api_key=groq_api_key,
                    )
                    
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
                    
                    # Create RAG chain: retriever -> format docs -> prompt -> llm
                    def format_docs(docs):
                        return "\n\n".join([doc.page_content for doc in docs])
                    
                    rag_chain = (
                        {"context": retriever | format_docs, "question": RunnablePassthrough()}
                        | prompt
                        | llm
                    )
                    
                    # Get response and source documents
                    source_docs = retriever.invoke(user_input)
                    response = rag_chain.invoke(user_input)
                    result = response.content  # Extract just the text content

                    # Ensure response contains actionable 'how-to' steps; if not, append concise steps
                    try:
                        has_action_words = re.search(r'\b(try|do|practice|exercise|step|steps|ground|breathe|breath|breathing|journal|plan|routine|task)\b', result, re.I)
                        has_list = re.search(r'(^\s*[-*•]|\d+\.)', result, re.M)
                        if not (has_action_words or has_list):
                            steps_prompt = (
                                "In a gentle, supportive tone, provide 4 concise, numbered, and practical steps "
                                f"(one sentence each) that the person can try right away for this message: \"{user_input}\". "
                                "Start each step with a verb and keep them actionable and safe."
                            )
                            steps_resp = llm.invoke(steps_prompt)
                            steps_text = steps_resp.content
                            result = result.strip() + "\n\nPractical steps:\n" + steps_text.strip()
                    except Exception:
                        # If augmentation fails, continue with original result
                        pass

                    # Display response
                    st.markdown(result)
                    
                    # Show source context in expander
                    if source_docs:
                        with st.expander("📚 Counseling context used", expanded=False):
                            for i, doc in enumerate(source_docs):
                                dialogue_id = doc.metadata.get("dialogue_id", "N/A")
                                st.caption(f"Source {i+1} — Dialogue #{dialogue_id}")
                                st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
                                if i < len(source_docs) - 1:
                                    st.markdown("---")

                    # Store assistant message
                    st.session_state.messages.append(
                        {"role": "assistant", "content": result}
                    )

                except FileNotFoundError:
                    st.error(
                        "📂 **Vectorstore not found.** Please run "
                        "`python ingest_counseling_data.py` first to build "
                        "the knowledge base."
                    )
                except Exception as e:
                    st.error(f"Something went wrong: {str(e)}")

        # Run trauma classification in the background (after response)
        try:
            classification = classify_message(user_input, groq_api_key)
            update_session_profile(classification)
            # Rerun to update sidebar insights
            st.rerun()
        except Exception:
            pass  # Don't break the experience if classification fails


if __name__ == "__main__":
    main()
