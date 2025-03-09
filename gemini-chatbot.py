import streamlit as st
import os
from google import genai
from google.genai import types

st.title("Gemini Chatbot")

# Handle API key management
api_key = os.environ.get("GEMINI_API_KEY")

# If no API key in environment variables, provide a way for users to input it
if not api_key:
    st.markdown("### API Key Required")
    st.markdown("Please provide your Google Gemini API key to use this chatbot.")
    
    # Create a text input for the API key with password masking
    user_api_key = st.text_input("Enter your Gemini API key:", type="password")
    
    # Only proceed if an API key is provided
    if not user_api_key:
        st.info("You'll need a Gemini API key to continue. You can get one from [Google AI Studio](https://makersuite.google.com/)")
        st.stop()
    else:
        api_key = user_api_key

# Initialize the Gemini client with the API key
try:
    genai_client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Error initializing Gemini client: {str(e)}")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize system prompt in session state if it doesn't exist
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""

# Add system prompt expander
with st.sidebar:
    with st.expander("System Prompt"):
        new_system_prompt = st.text_area(
            "Define how the chatbot should behave:",
            value=st.session_state.system_prompt,
            height=200,
            placeholder="Example: You are a helpful assistant that specializes in Python programming."
        )
        
        # Check if system prompt has changed
        if st.button("Apply System Prompt"):
            if new_system_prompt != st.session_state.system_prompt:
                st.session_state.system_prompt = new_system_prompt
                st.session_state.messages = []  # Clear chat history
                
                # Mark that we need to recreate the chat
                if "gemini_chat" in st.session_state:
                    del st.session_state.gemini_chat

# Initialize Gemini chat in session state
if "gemini_chat" not in st.session_state:
    try:
        # Create a standard chat without system instructions first
        st.session_state.gemini_chat = genai_client.chats.create(
            model="gemini-2.0-flash"
        )
        
        # Then, if system prompt exists, send it using the proper method
        if st.session_state.system_prompt:
            try:
                first_message = st.session_state.gemini_chat.send_message(
                    "",
                    config=types.GenerateContentConfig(
                        system_instruction=st.session_state.system_prompt
                    )
                )
                st.success("System prompt applied successfully!")
            except Exception as e:
                st.warning(f"System prompt couldn't be applied: {str(e)}")
                st.warning("Continuing with default model behavior.")
    except Exception as e:
        st.error(f"Error initializing Gemini: {str(e)}")
        st.stop()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me anything..."):
# Add user message to chat history
    with st.chat_message("user"):
# Add user message to chat history
        st.markdown(prompt)
    
# Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        with st.spinner("Thinking..."):
            if st.session_state.system_prompt:
                response = st.session_state.gemini_chat.send_message(
                    prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=st.session_state.system_prompt
                    )
                )
            else:
                response = st.session_state.gemini_chat.send_message(prompt)
            
            response_text = response.text
        
        with st.chat_message("assistant"):
            st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")