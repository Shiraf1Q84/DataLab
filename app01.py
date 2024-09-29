import streamlit as st
import requests
import time
import base64
import zipfile
import io

# Datalab API endpoint
DATALAB_API_URL = "https://www.datalab.to/api/v1/marker"

# Function to convert PDF to Markdown using Datalab API
def convert_pdf_to_markdown(file, api_key, langs=None, force_ocr=False, paginate=False):
    form_data = {
        'file': ('uploaded_file.pdf', file, 'application/pdf'),
        'langs': (None, langs),
        "force_ocr": (None, force_ocr),
        "paginate": (None, paginate)
    }
    headers = {"X-Api-Key": api_key}
    response = requests.post(DATALAB_API_URL, files=form_data, headers=headers)

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError as e:
        st.error(f"Error decoding JSON response: {e}")
        st.error(f"Raw response: {response.text}") 
        return None

    return data

# Streamlit UI
st.title("PDF to Markdown Converter")

# Initialize session state
if 'conversion_successful' not in st.session_state:
    st.session_state.conversion_successful = False
if 'converted_data' not in st.session_state:
    st.session_state.converted_data = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# Form
with st.form("converter_form"):
    # API Key input
    api_key = st.text_input("Enter your Datalab API Key", type="password")

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    # Options
    langs = st.text_input("Languages (comma-separated, optional)", "")
    force_ocr = st.checkbox("Force OCR")
    paginate = st.checkbox("Paginate Output")

    # Convert button
    submitted = st.form_submit_button("Convert")

    # Conversion process
    if submitted and uploaded_file is not None and api_key:
        with st.spinner("Converting..."):
            # Convert the PDF
            data = convert_pdf_to_markdown(uploaded_file, api_key, langs, force_ocr, paginate)

            if data:  # Check if the conversion was successful
                # Poll for results
                max_polls = 300
                check_url = data.get("request_check_url")

                if check_url:
                    for i in range(max_polls):
                        time.sleep(2)
                        response = requests.get(check_url, headers={"X-Api-Key": api_key})
                        data = response.json()

                        if data["status"] == "complete":
                            break

                    # Store results in session state
                    if data["success"]:
                        st.session_state.conversion_successful = True
                        st.session_state.converted_data = data
                        st.session_state.uploaded_file = uploaded_file
                        st.success("Conversion successful!")
                    else:
                        st.error(f"Conversion failed: {data.get('error', 'Unknown error')}")
                else:
                    st.error("Conversion failed: Invalid response from API.")
            else:
                st.error("Conversion failed: Invalid response from API.")

    elif submitted:
        st.warning("Please upload a PDF file and enter your API Key.")

# Download button (outside the form)
if st.session_state.conversion_successful:
    data = st.session_state.converted_data
    uploaded_file = st.session_state.uploaded_file

    # Create zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Add Markdown file
        zip_file.writestr(uploaded_file.name.replace(".pdf", ".md"), data["markdown"])

        # Add images
        if data["images"]:
            for filename, image_data in data["images"].items():
                image = base64.b64decode(image_data)
                zip_file.writestr(filename, image)

    # Download button for zip file
    st.download_button(
        label="Download Zip",
        data=zip_buffer.getvalue(),
        file_name=uploaded_file.name.replace(".pdf", ".zip"),
        mime="application/zip"
    )