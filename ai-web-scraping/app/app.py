import streamlit as st

scrape = st.Page("scrape.py", title="Web Scraper", icon=":material/home:")
results = st.Page("results.py", title="Upload", icon=":material/upload_file:")
howto = st.Page("howto.py", title="How To", icon=":material/question_mark:")

pg = st.navigation([scrape, results, howto])
st.set_page_config(page_title="AI Web Scraper", page_icon=":material/table_rows:")
pg.run()
