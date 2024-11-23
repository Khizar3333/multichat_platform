import streamlit as st
import requests
import os

# Configuration
BASE_URL = "https://khizar3333-multichat.hf.space/"

# Session state for managing authentication tokens
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None


# login and signup page
def login_signup_page():
    st.title("Multi-Chatbot Platform")
    
    tab1, tab2 = st.tabs(["Login", "Signup"])
    
    with tab1:
        st.header("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            try:
                response = requests.post(
                    f"{BASE_URL}/token",
                    data={"username": login_username, "password": login_password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.auth_token = token_data["access_token"]
                    
                    user_response = requests.get(
                        f"{BASE_URL}/user/me",
                        headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
                    )
                    if user_response.status_code == 200:
                        st.session_state.user_id = user_response.json()["id"]
                        st.success("Login successful!")
                        st.experimental_set_query_params(page="chatbot")
                        # st.query_params['page'] = "chatbot"
                        st.rerun()
                    else:
                        st.error("Failed to retrieve user details")
                else:
                    st.error(response.json().get("detail", "Login failed"))
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
    
    with tab2:
        st.header("Signup")
        signup_username = st.text_input("Choose a Username", key="signup_username")
        signup_email = st.text_input("Email Address", key="signup_email")
        signup_password = st.text_input("Create Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Signup", key="signup_button"):
            if signup_password != confirm_password:
                st.error("Passwords do not match")
                return
            try:
                response = requests.post(
                    f"{BASE_URL}/user/register",
                    json={"username": signup_username, "email": signup_email, "password": signup_password},
                )
                if response.status_code == 200:
                    st.success("Signup successful! Please login.")
                else:
                    st.error(response.json().get("detail", "Signup failed"))
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")

#----------------------------------------------------------------------------------------------------
# check if user is authenticated
def check_authentication():
    if not st.session_state.get('auth_token'):
        return False
    return True


#----------------------------------------------------------------------------------------------------
#  chatbot page
def create_chatbot_page():
    if not check_authentication():
        st.warning("Please login first")
        return

    st.title("Create Your Custom Chatbot")

    with st.form("chatbot_creation_form"):
        name = st.text_input("Chatbot Name")
        description = st.text_area("Chatbot Description")
        personality = st.text_area("Chatbot Personality")
        file = st.file_uploader("Upload Knowledge Base (PDF or TXT)", type=["pdf", "txt"])

        submit_button = st.form_submit_button("Create Chatbot")

        if submit_button:
            if not name or not description or not personality:
                st.error("Please fill all chatbot details.")
                return

            try:
                # Step 1: Create the chatbot
                response = requests.post(
                    f"{BASE_URL}/chatbots/",
                    params={"name": name, "description": description, "personality": personality},
                    headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
                )
                st.write(f"API Response: {response.json()}")
                if response.status_code == 200:
                    chatbot_data = response.json()  # Get chatbot details including the ID
                    chatbot_id = chatbot_data.get("id")

                    # Debugging line to check the chatbot_id
                    st.write(f"Chatbot ID: {chatbot_id}")

                    if not chatbot_id:
                        st.error("Chatbot created, but ID could not be retrieved.")
                        return

                    st.success(f"Chatbot '{name}' created successfully!")
                    
                    # Step 2: Upload the knowledge base if a file was provided
                    if file :
                        try:
                            files = {"file": (file.name, file, file.type)}
                            upload_response = requests.post(
                                f"{BASE_URL}/chatbots/{chatbot_id}/upload",
                                files=files,
                                headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
                            )
                            if upload_response.status_code == 200:
                                st.success(f"Knowledge base '{file.name}' uploaded successfully!")
                            else:
                                st.error(upload_response.json().get("detail", "Failed to upload file"))
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to upload knowledge base: {e}")
                else:
                    st.error(response.json().get("detail", "Failed to create chatbot"))
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")

#----------------------------------------------------------------------------------------------------
# upload_knowledge function
def upload_knowledge_page():
    if not check_authentication():
        st.warning("Please login first")
        return
    
    st.title("Upload Knowledge Base")
    
    chatbot_id = st.text_input("Chatbot ID")
    file = st.file_uploader("Choose a file (PDF or TXT)", type=["pdf", "txt"])
    
    if st.button("Upload"):
        if not chatbot_id or not file:
            st.error("Please provide a chatbot ID and select a file.")
            return
        
        # Check file size (5 MB = 5 * 1024 * 1024 bytes)
        if file.size > 5 * 1024 * 1024:
            st.error("File size exceeds 5 MB limit. Please upload a smaller file.")
            return
        
        # Debugging line to check the file type
        st.write(f"Uploaded file type: {file.type}")  
        
        try:
            files = {"file": (file.name, file, file.type)}  # Correctly format the file upload
            response = requests.post(
                f"{BASE_URL}/chatbots/{chatbot_id}/upload",
                files=files,
                headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
            )
            if response.status_code == 200:
                st.success(f"File '{file.name}' uploaded successfully!")
            else:
                st.error(response.json().get("detail", "Failed to upload file"))
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {e}")

#----------------------------------------------------------------------------------------------------
# dashboard page
def dashboard():
    if not check_authentication():
        st.warning("Please login first")
        return
    
    st.title("View Your Chatbots")
    
    try:
        response = requests.get(
            f"{BASE_URL}/chatbots/user/{st.session_state.user_id}",
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
        )
        if response.status_code == 200:
            chatbots = response.json().get("chatbots", [])
            
            st.write("### Your Chatbots:")
            
            # Create a list of dictionaries for better formatting
            chatbot_data = [
                {"Name": chatbot["name"], "Created At": chatbot["created_at"]} for chatbot in chatbots
            ]
            
            # Display the chatbot data in a table
            st.table(chatbot_data)
        else:
            st.error("Failed to retrieve chatbots")
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}")

#----------------------------------------------------------------------------------------------------
# chatbot interaction page
def interact_with_chatbots():
    if not check_authentication():
        st.warning("Please login first")
        return
    
    st.title("View Your Chatbots")
    
    try:
        # Fetch user chatbots from the API
        response = requests.get(
            f"{BASE_URL}/chatbots/user/{st.session_state.user_id}",
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
        )
        if response.status_code == 200:
            chatbots = response.json().get("chatbots", [])
            
            if not chatbots:
                st.info("You have not created any chatbots yet.")
                return
            
            # Display chatbots in a dropdown
            chatbot_options = {chatbot['name']: chatbot['id'] for chatbot in chatbots}
            selected_chatbot_name = st.selectbox("Select a Chatbot to Interact", list(chatbot_options.keys()))
            
            # Interaction section
            st.subheader(f"Chat with {selected_chatbot_name}")
            query = st.text_area("Enter your query")
            
            if st.button(f"Submit Query to {selected_chatbot_name}"):
                chatbot_id = chatbot_options[selected_chatbot_name]
                if not query:
                    st.error("Please enter a query.")
                    return
                try:
                    response = requests.post(
                        f"{BASE_URL}/chatbots/{chatbot_id}/query",
                        params={"query": query},
                        headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
                    )
                    if response.status_code == 200:
                        
                        response_data = response.json()
                         # Debug output
                        if isinstance(response_data.get("response"), dict):
                          st.success(response_data["response"]["content"])
                        else:
                         st.success(response_data["response"])
                    else:
                        st.error(response.json().get("detail", "Failed to query chatbot"))
                except requests.exceptions.RequestException as e:
                    st.error(f"Network error: {e}")
        else:
            st.error("Failed to retrieve chatbots")
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}")




def main():
    st.set_page_config(page_title="Multi-Chatbot Platform")
    
    if 'page' not in st.experimental_get_query_params():
        login_signup_page()
    else:
        page = st.sidebar.radio("Navigate", 
            ["Create Chatbot","Interact with Chatbots", "dashboard"]
        )
        
        if st.sidebar.button("Logout"):
            st.session_state.auth_token = None
            st.session_state.user_id = None
            st.experimental_set_query_params()
            st.rerun()
        
        if page == "Create Chatbot":
            create_chatbot_page()
        elif page == "Interact_with_Chatbots":
            interact_with_chatbots()
        elif page == "dashboard":
            dashboard()

if __name__ == "__main__":
    main()

