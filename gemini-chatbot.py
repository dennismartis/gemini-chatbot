import streamlit as st
import os
from google import genai
from google.genai import types
import io

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

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "reset_uploader" not in st.session_state:
    st.session_state.reset_uploader = False

# Sidebar content
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
    
    # Add file uploader section
    with st.expander("Upload Documents", expanded=True):
        st.write("Upload documents to chat with your data")
        
        # Always render the file uploader widget with a dynamic key
        uploader_key = f"document_uploader_{len(st.session_state.uploaded_files)}"
        uploaded_file = st.file_uploader(
            "Upload PDF or text documents",
            type=["pdf", "txt", "csv", "md", "html", "css", "js", "py", "xml"],
            help="Max file size: 20MB. For larger files, the API will handle them differently.",
            key=uploader_key
        )
        
        if uploaded_file is not None:
            # Check if file is already uploaded (by name)
            if uploaded_file.name not in [f["name"] for f in st.session_state.uploaded_files]:
                # Process the file
                try:
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        # Read file bytes
                        file_bytes = uploaded_file.getvalue()
                        
                        # Determine mime type based on file extension
                        file_extension = uploaded_file.name.split(".")[-1].lower()
                        mime_type = {
                            "pdf": "application/pdf",
                            "txt": "text/plain",
                            "csv": "text/csv",
                            "md": "text/md",
                            "html": "text/html",
                            "css": "text/css",
                            "js": "text/javascript", 
                            "py": "application/x-python",
                            "xml": "text/xml"
                        }.get(file_extension, "application/octet-stream")
                        
                        # Upload to Gemini API
                        file_obj = genai_client.files.upload(
                            file=io.BytesIO(file_bytes),
                            config=dict(mime_type=mime_type)
                        )
                        
                        # Store file info in session state
                        st.session_state.uploaded_files.append({
                            "name": uploaded_file.name,
                            "file_obj": file_obj,
                            "mime_type": mime_type
                        })
                        
                        st.success(f"Successfully uploaded {uploaded_file.name}")
                        # Force a rerun to reset the file uploader
                        st.rerun()
                except Exception as e:
                    st.error(f"Error uploading file: {str(e)}")
        
        # Display uploaded files and allow removal
        if st.session_state.uploaded_files:
            st.write("### Uploaded Documents")
            for idx, file_info in enumerate(st.session_state.uploaded_files):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{idx+1}. {file_info['name']}")
                with col2:
                    if st.button("Remove", key=f"remove_{idx}"):
                        try:
                            # Delete from Gemini API
                            genai_client.files.delete(name=file_info["file_obj"].name)
                            # Remove from session state
                            st.session_state.uploaded_files.pop(idx)
                            # Reset the chat session to avoid referencing deleted files
                            if "gemini_chat" in st.session_state:
                                del st.session_state.gemini_chat
                            # Instead of directly modifying the uploader, use the key_exists trick
                            if "document_uploader" in st.session_state:
                                del st.session_state["document_uploader"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error removing file: {str(e)}")

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
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        with st.spinner("Thinking..."):
            # Prepare message with files included
            message = prompt
            
            # Create a message that includes any uploaded files
            contents = []
            if st.session_state.uploaded_files:
                for file_info in st.session_state.uploaded_files:
                    contents.append(file_info["file_obj"])
            contents.append(message)
            
            # Generate response
            if st.session_state.system_prompt:
                response = st.session_state.gemini_chat.send_message(
                    message=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=st.session_state.system_prompt
                    )
                )
            else:
                response = st.session_state.gemini_chat.send_message(
                    message=contents
                )
            response_text = response.text
        
        with st.chat_message("assistant"):
            st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")

# Add a function to clear uploaded files
if st.session_state.uploaded_files:
    if st.button("Clear All Documents"):
        try:
            # Delete all files from Gemini API
            for file_info in st.session_state.uploaded_files:
                genai_client.files.delete(name=file_info["file_obj"].name)
            
            # Clear session state
            st.session_state.uploaded_files = []
            
            # Reset the chat session to avoid referencing deleted files
            if "gemini_chat" in st.session_state:
                del st.session_state.gemini_chat
                
            st.success("All documents cleared")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing documents: {str(e)}")