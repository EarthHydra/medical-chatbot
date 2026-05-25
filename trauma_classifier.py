"""
SafeSpace — Real-Time Trauma Classifier
Classifies user messages into abuse/trauma categories using LLM.
Maintains a running session profile for the sidebar insights panel.
"""

import json
import streamlit as st
from langchain_groq import ChatGroq
from prompts import CLASSIFICATION_PROMPT_TEMPLATE


# Human-readable labels and colors for each category
CATEGORY_CONFIG = {
    "sexual_abuse": {"label": "Sexual Harassment / Abuse", "emoji": "🟣", "color": "#9b59b6"},
    "domestic_violence": {"label": "Domestic Violence", "emoji": "🔴", "color": "#e74c3c"},
    "cyberbullying": {"label": "Cyberbullying / Online Harassment", "emoji": "🟠", "color": "#e67e22"},
    "emotional_abuse": {"label": "Emotional / Psychological Abuse", "emoji": "🟡", "color": "#f1c40f"},
    "stalking": {"label": "Stalking", "emoji": "🔵", "color": "#3498db"},
    "child_abuse": {"label": "Child Abuse / Exploitation", "emoji": "🟢", "color": "#2ecc71"},
    "other": {"label": "Other / Unspecified", "emoji": "⚪", "color": "#95a5a6"},
}

SEVERITY_CONFIG = {
    "low": {"label": "Low", "color": "#2ecc71", "emoji": "🟢"},
    "medium": {"label": "Medium", "color": "#f39c12", "emoji": "🟡"},
    "high": {"label": "High", "color": "#e74c3c", "emoji": "🟠"},
    "critical": {"label": "Critical — Immediate Attention", "color": "#c0392b", "emoji": "🔴"},
}


def init_session_profile():
    """Initialize the session-level trauma profile in session state."""
    if "trauma_profile" not in st.session_state:
        st.session_state.trauma_profile = {
            "categories": {cat: 0.0 for cat in CATEGORY_CONFIG},
            "max_severity": "low",
            "message_count": 0,
            "immediate_danger_flagged": False,
        }


def classify_message(message: str, groq_api_key: str) -> dict | None:
    """
    Classify a single user message into trauma categories.
    Returns the parsed classification dict or None on failure.
    """
    try:
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.0,
            groq_api_key=groq_api_key,
        )

        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(message=message)
        response = llm.invoke(prompt)

        # Parse JSON from response
        content = response.content.strip()

        # Handle cases where the LLM wraps JSON in markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)
        return result

    except (json.JSONDecodeError, Exception) as e:
        # Silently fail classification — don't break the chat experience
        print(f"Classification error: {e}")
        return None


def update_session_profile(classification: dict):
    """
    Update the running session profile with new classification results.
    Uses exponential moving average to accumulate category scores.
    """
    profile = st.session_state.trauma_profile
    profile["message_count"] += 1

    if classification is None:
        return

    categories = classification.get("categories", {})
    severity = classification.get("severity", "low")
    immediate_danger = classification.get("immediate_danger", False)

    # Update category scores (exponential moving average)
    alpha = 0.4  # Weight for new observation
    for cat, score in categories.items():
        if cat in profile["categories"]:
            old = profile["categories"][cat]
            profile["categories"][cat] = round(old * (1 - alpha) + score * alpha, 3)

    # Update max severity (only escalate, never de-escalate during session)
    severity_order = ["low", "medium", "high", "critical"]
    current_idx = severity_order.index(profile["max_severity"])
    new_idx = severity_order.index(severity) if severity in severity_order else 0
    if new_idx > current_idx:
        profile["max_severity"] = severity

    # Flag immediate danger
    if immediate_danger:
        profile["immediate_danger_flagged"] = True


def render_session_insights():
    """Render the session insights panel in the Streamlit sidebar."""
    init_session_profile()
    profile = st.session_state.trauma_profile
    
    # Safety check: if profile is still None, return early
    if profile is None:
        st.sidebar.markdown(
            '<p style="color: #b0b0b0; font-style: italic;">Session insights will appear here as you chat.</p>',
            unsafe_allow_html=True,
        )
        return

    if profile["message_count"] == 0:
        st.sidebar.markdown(
            '<p style="color: #b0b0b0; font-style: italic;">Session insights will appear here as you chat.</p>',
            unsafe_allow_html=True,
        )
        return

    # Immediate danger alert
    if profile["immediate_danger_flagged"]:
        st.sidebar.error("⚠️ **Immediate danger has been detected in this session.** Please ensure the person has access to emergency services (112).")

    # Severity indicator
    sev = profile["max_severity"]
    sev_cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["low"])
    st.sidebar.markdown(
        f"**Session Severity:** {sev_cfg['emoji']} {sev_cfg['label']}",
    )

    st.sidebar.markdown("---")

    # Category breakdown — only show categories with score > 0.05
    st.sidebar.markdown("**Detected Categories:**")
    active_categories = {
        cat: score
        for cat, score in profile["categories"].items()
        if score > 0.05
    }

    if active_categories:
        for cat, score in sorted(active_categories.items(), key=lambda x: x[1], reverse=True):
            cfg = CATEGORY_CONFIG[cat]
            bar_width = int(score * 100)
            st.sidebar.markdown(
                f"{cfg['emoji']} **{cfg['label']}**"
            )
            st.sidebar.progress(min(score, 1.0))
    else:
        st.sidebar.markdown(
            '<p style="color: #b0b0b0; font-style: italic;">No specific categories detected yet.</p>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown(
        f"<br><small style='color: #888;'>Based on {profile['message_count']} message(s) in this session</small>",
        unsafe_allow_html=True,
    )
