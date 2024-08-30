import json

import streamlit as st
import pandas as pd

from aiwebscraper.extract import get_from_xpaths

st.title("Upload")
st.write(
    "Upload the scraper to extract data from the website again. "
    "This feature doesn't use OpenAI's API"
)


def upload_and_parse_json():
    uploaded_file = st.file_uploader("Choose a JSON file", type="json")
    if uploaded_file is not None:
        try:
            # Read the file
            file_contents = uploaded_file.read()
            # Parse JSON
            parsed_data = json.loads(file_contents)
            return parsed_data
        except json.JSONDecodeError:
            st.error("Error: Invalid JSON file. Please upload a valid JSON file.")
            return None
    return None


# Call the function and store the result
parsed_json = upload_and_parse_json()

# Display the parsed JSON if available
if parsed_json:
    table = get_from_xpaths(
        parsed_json["url"], parsed_json["element_xpath"], parsed_json["xpaths"]
    )

    try:
        df = pd.DataFrame.from_records(table)
    except Exception as e:
        st.write(table)
    else:
        st.write(df)
