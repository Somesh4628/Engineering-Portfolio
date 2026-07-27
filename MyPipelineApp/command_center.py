import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION -----------------------------------------------------------
# We will fill these in during the next step.
GOOGLE_API_KEY = "AIzaSyBEEq30WlFq59g8X470N_uD3dABLqxQkIo"

# -----------------------------------------------------------------------------

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Forge V2 Command Center", page_icon="🤖", layout="wide")

st.title("Forge V2: The Living Codex - Command Center 🤖")
st.write(
    "Welcome, Architect. Discuss your upgrade plans here. When you are ready to execute, use the 'Go Ahead' button."
)

# --- GEMINI SETUP ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except Exception as e:
    st.error(f"Error configuring Gemini AI. Please check your API Key. Details: {e}")

# --- CHAT SESSION STATE ---
# This is crucial to make the chat remember the conversation.
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else message.role
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# --- USER INPUT & GO AHEAD BUTTON ---
# The chat input box at the bottom of the screen.
user_prompt = st.chat_input("Architect, what is your directive?")

# The "Go Ahead" button on the sidebar.
with st.sidebar:
    st.header("Execution")
    if st.button("Go Ahead", use_container_width=True, type="primary"):
        if not st.session_state.chat.history:
            st.warning("Cannot execute an empty plan. Please discuss the plan first.")
        else:
            with st.spinner(
                "Directive confirmed. Transmitting final plan to the Forge..."
            ):
                # Assemble the final plan from the conversation history
                final_plan = "Based on our conversation, execute the following plan:\n"
                for message in st.session_state.chat.history:
                    if message.role == "user":
                        final_plan += f"- {message.parts[0].text}\n"

                # N8N REMOVED: Simulation Mode Only
                st.success("SUCCESS: Directive processed locally (n8n link removed).")
                # Reset the chat for the next plan
                st.session_state.chat = model.start_chat(history=[])
                st.rerun()  # Rerender the page to clear the chat


# --- HANDLE NEW USER INPUT ---
if user_prompt:
    # Add user message to chat history and display it
    st.chat_message("user").markdown(user_prompt)

    # Send to Gemini and get response
    try:
        response = st.session_state.chat.send_message(user_prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"An error occurred while communicating with the AI. Details: {e}")
