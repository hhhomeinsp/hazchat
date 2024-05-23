import streamlit as st
import requests
from PIL import Image
import io
import base64
import time

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
    st.set_page_config(page_title="HazChat", page_icon="hazchaticon.png")

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

    # Camera activation switch
    camera_activated = st.sidebar.checkbox("Activate Camera", value=st.session_state["camera_activated"])
    take_snapshots = st.sidebar.checkbox("Start Periodic Snapshots", value=st.session_state["take_snapshots"])

    # Update the session state based on the checkbox values
    if camera_activated != st.session_state["camera_activated"]:
        st.session_state["camera_activated"] = camera_activated
    if take_snapshots != st.session_state["take_snapshots"]:
        st.session_state["take_snapshots"] = take_snapshots

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

    # Add custom HTML/CSS for the input container with styling
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

    st.markdown(f"""
    <div class="input-container">
        <input type="text" id="user_input" name="user_input" placeholder="Describe your hazmat incident..." style="width: 100%;">
        <button id="submit_button" type="button">
            <img src="data:image/png;base64,{img_base64}" style="width: 24px; height: 24px;">
        </button>
    </div>
    <script>
    const submitButton = document.getElementById('submit_button');
    const userInput = document.getElementById('user_input');
    submitButton.addEventListener('click', function() {{
        window.sessionStorage.setItem('user_input', userInput.value);
        window.location.reload();
    }});
    </script>
    """, unsafe_allow_html=True)

    if 'user_input' in st.session_state and st.session_state['user_input']:
        user_input = st.session_state['user_input']
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

if __name__ == "__main__":
    main()
