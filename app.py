import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import requests
from PIL import Image
import io
import base64
import time
from streamlit_modal import Modal

# Set the page configuration
st.set_page_config(page_title="HazChat", page_icon="hazchaticon.png")

# Load configuration from the YAML file
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initialize the authenticator
authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)

# API endpoint without authorization headers
API_URL = "https://flowiseai-lisa.onrender.com/api/v1/prediction/156d7471-57f9-49fa-a39e-25ef6e3e173f"

# Function to query the API
def query(payload):
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        st.error(f"Other error occurred: {err}")
        return None

def load_reference_materials():
    return ["dot_placards.jpg"]

# Streamlit app
def main():
    name, authentication_status, username = authenticator.login(location='main')
    if authentication_status:
        authenticator.logout('Logout', 'sidebar')

        # Initialize session states if not already set
        if "camera_activated" not in st.session_state:
            st.session_state["camera_activated"] = False
        if "take_snapshots" not in st.session_state:
            st.session_state["take_snapshots"] = False
        if "ref_button" not in st.session_state:
            st.session_state["ref_button"] = False
        if "image_paths" not in st.session_state:
            st.session_state["image_paths"] = []
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # Display the logo
        st.image("hazchat.png", width=200)  # Display the logo at 200 pixels width
        st.write("Helping emergency responders with hazardous material incidents.")

        # Sidebar for additional functionalities
        st.sidebar.header("Additional Options")

        # Add a dropdown to select reference materials
        image_options = load_reference_materials()
        selected_image = st.sidebar.selectbox("Select Reference", image_options)
        
        modal = Modal("Reference Material", key="reference-modal")
        
        open_modal = st.sidebar.button("Display Reference")
        if open_modal:
            modal.open()

        if modal.is_open():
            with modal.container():
                st.image(selected_image, use_column_width=True)

        # Camera activation using toggle switch
        st.session_state["camera_activated"] = st.sidebar.checkbox("Activate Camera", value=st.session_state["camera_activated"])

        # Start Periodic Snapshots using toggle switch
        st.session_state["take_snapshots"] = st.sidebar.checkbox("Start Periodic Snapshots", value=st.session_state["take_snapshots"])

        if st.session_state["camera_activated"]:
            # Camera input for periodic snapshots
            st.sidebar.write("Take a photo using your camera for real-time context:")
            camera_input = st.sidebar.camera_input("Take a photo")

            if camera_input:
                st.image(camera_input, caption="Snapshot", use_column_width=True)

                if st.session_state["take_snapshots"]:
                    camera_image = Image.open(camera_input)
                    buffered = io.BytesIO()
                    camera_image.save(buffered, format="PNG")
                    img_str = buffered.getvalue()
                    payload = {"image": img_str.hex()}

                    # Display the snapshot
                    st.image(camera_image, caption="Snapshot taken at: " + time.strftime("%Y-%m-%d %H:%M:%S"), use_column_width=True)

                    # Periodic snapshots every 5 seconds
                    time.sleep(5)

        # Display chat history
        for chat in st.session_state["chat_history"]:
            st.write(chat)

        prompt = st.chat_input("Describe your hazmat incident...")
        if prompt:
            st.session_state["chat_history"].append(f"User: {prompt}")
            st.write(f"User has sent the following prompt: {prompt}")

            # Prepare the payload
            payload = {"question": prompt}

            # If a file is uploaded, include the image in the payload
            if 'uploaded_file' in locals() and uploaded_file is not None:
                image = Image.open(uploaded_file)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = buffered.getvalue()
                payload["image"] = img_str.hex()

            # Query the API with user's input
            output = query(payload)

            # Display the response
            if output:
                response_text = output.get("text", "No response received.")
                st.session_state["chat_history"].append(f"Chatbot: {response_text}")
                st.write("Chatbot Response:")
                st.markdown(response_text.replace("\\n", "\n"))
            else:
                st.write("No response received from the server.")

    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')

if __name__ == "__main__":
    main()
