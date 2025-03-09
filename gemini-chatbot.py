import streamlit as st
import os
from google import genai

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

# Initialize Gemini chat in session state
if "gemini_chat" not in st.session_state:
    try:
        st.session_state.gemini_chat = genai_client.chats.create(model="gemini-2.0-flash")
    except Exception as e:
        st.error(f"Error initializing Gemini: {str(e)}")
        st.stop()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me anything..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        # Display a spinner while generating the response
        with st.spinner("Thinking..."):
            # Generate response using Gemini
            response = st.session_state.gemini_chat.send_message(prompt)
            response_text = response.text
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response_text)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")