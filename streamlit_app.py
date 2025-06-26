import streamlit as st
import pandas as pd
import scraper

st.title("Projects-Scrapping Web App")

st.write("Click the button below to scrape the latest 6 ongoing projects from the Odisha RERA portal.")

if st.button("Run Scraper"):
    with st.spinner("Scraping in progress... This may take up to a minute."):
        data = scraper.scrape_ongoing_projects()
    if data:
        st.success(f"Scraping complete! {len(data)} projects found.")
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.download_button("Download as CSV", df.to_csv(index=False), "projects.csv", "text/csv")
    else:
        st.error("Scraping failed or no data found. Please try again.")
