import streamlit as st
import requests
import time
import base64

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
    data = response.json()
    return data

# Streamlit UI
st.title("PDF to Markdown Converter")

# API Key input
api_key = st.text_input("Enter your Datalab API Key", type="password")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Options
langs = st.text_input("Languages (comma-separated, optional)", "")
force_ocr = st.checkbox("Force OCR")
paginate = st.checkbox("Paginate Output")

# Convert button
if st.button("Convert"):
    if uploaded_file is not None and api_key:
        with st.spinner("Converting..."):
            # Convert the PDF
            data = convert_pdf_to_markdown(uploaded_file, api_key, langs, force_ocr, paginate)

            # Poll for results
            max_polls = 300
            check_url = data["request_check_url"]

            for i in range(max_polls):
                time.sleep(2)
                response = requests.get(check_url, headers={"X-Api-Key": api_key})
                data = response.json()

                if data["status"] == "complete":
                    break

            # Display results
            if data["success"]:
                st.success("Conversion successful!")

                # Display Markdown
                st.markdown(data["markdown"])

                # Download Markdown button
                st.download_button(
                    label="Download Markdown",
                    data=data["markdown"],
                    file_name=uploaded_file.name.replace(".pdf", ".md")
                )

                # Display and download images if available
                if data["images"]:
                    st.subheader("Images")
                    for filename, image_data in data["images"].items():
                        # Decode base64 image data
                        image = base64.b64decode(image_data)

                        # Display image
                        st.image(image, caption=filename)

                        # Download image button
                        st.download_button(
                            label=f"Download {filename}",
                            data=image,
                            file_name=filename
                        )

            else:
                st.error(f"Conversion failed: {data['error']}")
    else:
        st.warning("Please upload a PDF file and enter your API Key.")