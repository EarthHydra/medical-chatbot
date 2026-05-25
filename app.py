"""
SafeSpace — Trauma-Informed AI Support Chatbot
A compassionate chat companion for survivors of abuse.
Built with Streamlit, LangChain, FAISS, and Groq.
"""

import os
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
    page_title="SafeSpace — You Are Not Alone",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────
# Custom CSS — Warm, Calming Design
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Main container ── */
    .stApp {
        background: linear-gradient(160deg, #1a1025 0%, #1e1232 30%, #1a1025 70%, #150d1f 100%);
    }

    /* ── Header ── */
    .safespace-header {
        text-align: center;
        padding: 1.5rem 1rem 1rem;
        margin-bottom: 0.5rem;
    }
    .safespace-header h1 {
        background: linear-gradient(135deg, #c084fc 0%, #a78bfa 30%, #818cf8 60%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    .safespace-header p {
        color: #a78bfa;
        font-size: 0.95rem;
        font-weight: 300;
        opacity: 0.85;
    }

    /* ── Chat message styling ── */
    .stChatMessage {
        border-radius: 16px !important;
        margin-bottom: 0.75rem !important;
        border: 1px solid rgba(139, 92, 246, 0.08) !important;
        animation: fadeInUp 0.4s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* ── User message ── */
    [data-testid="stChatMessage"][aria-label="user"] {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(109, 40, 217, 0.08) 100%) !important;
    }

    /* ── Assistant message ── */
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background: rgba(30, 20, 50, 0.6) !important;
        backdrop-filter: blur(10px);
    }

    /* ── Chat input ── */
    .stChatInput {
        border-radius: 24px !important;
    }
    .stChatInput > div {
        border-radius: 24px !important;
        border: 1.5px solid rgba(139, 92, 246, 0.25) !important;
        background: rgba(30, 20, 50, 0.7) !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stChatInput > div:focus-within {
        border-color: rgba(139, 92, 246, 0.5) !important;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.15) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1025 0%, #150d1f 100%) !important;
        border-right: 1px solid rgba(139, 92, 246, 0.12);
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #c084fc;
        font-weight: 600;
        font-size: 1rem;
    }

    /* ── Crisis resource card ── */
    .crisis-card {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(185, 28, 28, 0.06) 100%);
        border: 1px solid rgba(220, 38, 38, 0.2);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
    }
    .crisis-card p {
        margin: 0;
        font-size: 0.85rem;
    }
    .crisis-card .hotline-name {
        color: #fca5a5;
        font-weight: 500;
    }
    .crisis-card .hotline-number {
        color: #fecaca;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.5px;
    }

    /* ── Disclaimer box ── */
    .disclaimer-box {
        background: rgba(139, 92, 246, 0.06);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-top: 1rem;
    }
    .disclaimer-box p {
        color: #a78bfa;
        font-size: 0.78rem;
        margin: 0;
        line-height: 1.5;
        opacity: 0.8;
    }

    /* ── Insight section ── */
    .insight-section {
        background: rgba(139, 92, 246, 0.06);
        border: 1px solid rgba(139, 92, 246, 0.12);
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.75rem;
    }

    /* ── Expander styling ── */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        color: #a78bfa !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.5);
    }

    /* ── Hide default Streamlit branding ── */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
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
        st.markdown("### 💜 SafeSpace")
        st.markdown("---")

        # Crisis Resources
        st.markdown("### 🆘 Crisis Resources")
        st.markdown(
            '<p style="color: #fca5a5; font-size: 0.82rem; margin-bottom: 0.75rem;">'
            "If you're in immediate danger, please call these numbers:</p>",
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
                <p>⚠️ <strong>Disclaimer:</strong> SafeSpace is an AI support tool and 
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
        """<div class="safespace-header">
            <h1>💜 SafeSpace</h1>
            <p>A safe place to be heard. You are not alone.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show welcome message if no messages yet
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="💜"):
            st.markdown(WELCOME_MESSAGE)

    # Display chat history
    for message in st.session_state.messages:
        avatar = "💜" if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar if message["role"] == "assistant" else None):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Share what's on your mind... I'm here to listen 💜")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get API key
        groq_api_key = get_groq_api_key()

        # Generate response
        with st.chat_message("assistant", avatar="💜"):
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
                        model_name="llama-3.1-70b-versatile",
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
                    result = rag_chain.invoke(user_input)
                    
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
