import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import requests
from PIL import Image
import io
import base64
import time

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

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Streamlit app
def main():
    name, authentication_status, username = authenticator.login(location='main')
    if authentication_status:
        authenticator.logout('Logout', 'sidebar')

        # Display the logo
        st.image("hazchat.png", width=200)  # Display the logo at 200 pixels width

        st.write("Helping emergency responders with hazardous material incidents.")

        # Sidebar for additional functionalities
        st.sidebar.header("Additional Options")

        # File uploader for photo in the sidebar
        uploaded_file = st.sidebar.file_uploader("Upload a photo of your hazmat incident (optional):", type=["jpg", "jpeg", "png"])

        # Initialize session states if not already set
        if "camera_activated" not in st.session_state:
            st.session_state["camera_activated"] = False
        if "take_snapshots" not in st.session_state:
            st.session_state["take_snapshots"] = False

        # Camera activation using toggle buttons
        camera_activated = st.sidebar.radio("Activate Camera", ["Off", "On"], index=1 if st.session_state["camera_activated"] else 0)
        st.session_state["camera_activated"] = camera_activated == "On"

        take_snapshots = st.sidebar.radio("Start Periodic Snapshots", ["Off", "On"], index=1 if st.session_state["take_snapshots"] else 0)
        st.session_state["take_snapshots"] = take_snapshots == "On"

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
                    payload["image"] = img_str.hex()

                    # Display the snapshot
                    st.image(camera_image, caption="Snapshot taken at: " + time.strftime("%Y-%m-%d %H:%M:%S"), use_column_width=True)
                
                    # Periodic snapshots every 5 seconds
                    time.sleep(5)

        # Convert the image to a base64 string
        img_base64 = get_base64_image("image.png")  # Ensure the image is in the same directory as this script

        # Chat input section
        st.markdown("""
        <style>
        .input-container {
            display: flex;
            align-items: center;
            background-color: #f0f0f5;
            border-radius: 30px;
            padding: 10px;
        }
        .input-container input {
            flex: 1;
            border: none;
            background-color: #f0f0f5;
            border-radius: 10px;
            padding: 10px;
            margin-right: 10px;
        }
        .input-container input:focus {
            outline: none;
        }

        .input-container button {
            background-color: transparent;
            border: none;
            cursor: pointer;
        }
        @media only screen and (max-width: 600px) {
            .input-container {
                flex-direction: column;
            }
            .input-container input {
                margin-bottom: 10px;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        user_input = st.text_input("Describe your hazmat incident...", key="user_input")

        if st.button("Submit"):
            if user_input:
                # Prepare the payload
                payload = {"question": user_input}

                # If a file is uploaded, include the image in the payload
                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    img_str = buffered.getvalue()
                    payload["image"] = img_str.hex()

                # If a camera image is captured, include it in the payload
                if st.session_state["camera_activated"] and camera_input:
                    camera_image = Image.open(camera_input)
                    buffered = io.BytesIO()
                    camera_image.save(buffered, format="PNG")
                    img_str = buffered.getvalue()
                    payload["image"] = img_str.hex()

                # Query the API with user's input
                output = query(payload)

                # Display the response
                if output:
                    st.write("Chatbot Response:")
                    response_text = output.get("text", "No response received.")
                    st.markdown(response_text.replace("\\n", "\n"))
                else:
                    st.write("No response received from the server.")
    
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')

if __name__ == "__main__":
    main()
