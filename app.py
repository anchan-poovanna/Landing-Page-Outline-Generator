import streamlit as st
from firecrawl import FirecrawlApp
from openai import OpenAI
import requests
import json
from datetime import datetime
# Assuming your LLMEnhancedAnalyzer class is in a separate file called analyzer.py
from lg import LLMEnhancedAnalyzer, get_search_results

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Landing Page Outline Generator",
        page_icon="📝",
        layout="wide"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main {
            background-color: #1a1a2e;
            color: #ffffff;
        }
        .main-title {
            font-size: 2.5rem;
            color: #00d4ff;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stButton>button {
            background-color: #00d4ff;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 2rem;
            margin-right: 1rem;
        }
        .stButton>button:hover {
            background-color: #00aaff;
        }
        .stTextInput div input {
            background-color: #2e2e4d;
            color: #ffffff;
            border: 1px solid #444;
        }
        .stTextArea textarea {
            background-color: #2e2e4d !important;
            color: #ffffff !important;
            border: 1px solid #444 !important;
            border-radius: 8px !important;
            padding: 1rem !important;
            height: 500px !important;
        }
        .stTextArea textarea:disabled {
            background-color: #2e2e4d !important;
            color: #ffffff !important;
            opacity: 1 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-title">Landing Page Outline Generator</h1>', unsafe_allow_html=True)

    # Create two columns for the layout
    col1, col2 = st.columns([1, 2], gap="large")

    # Initialize session state for outline
    if 'outline' not in st.session_state:
        st.session_state.outline = ""

    # Left column: Input and buttons
    with col1:
        # Input field for topic
        search_query = st.text_input(
            label="Enter the topic:",
            placeholder="e.g., uber clone/ enter your primary keyword",
            help="Enter the topic or search query for which you want to generate a landing page outline"
        )

        # Create two columns for buttons
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            get_outline_btn = st.button("Get Outline")

        with btn_col2:
            # Download button (disabled until outline is generated)
            download_btn = st.download_button(
                label="Download",
                data=st.session_state.outline,
                file_name=f"landing_page_outline_{search_query.replace(' ', '_')}.txt" if search_query else "landing_page_outline.txt",
                mime="text/plain",
                disabled=not st.session_state.outline
            )

        # Handle button click
        if get_outline_btn:
            if not search_query:
                st.error("Please enter a topic before generating an outline!")
            else:
                try:
                    # Create a spinner to show progress
                    with st.spinner("Generating outline... This may take a moment"):
                        # Get API keys from secrets
                        FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
                        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
                        SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

                        # Fetch SERP data
                        serp_data = get_search_results(search_query, SERPAPI_KEY)
                        if not serp_data:
                            st.error("Failed to fetch SERP data. Please try again.")
                            return

                        # Initialize analyzer
                        analyzer = LLMEnhancedAnalyzer(
                            firecrawl_api_key=FIRECRAWL_API_KEY,
                            openai_api_key=OPENAI_API_KEY
                        )

                        # Set content parameters
                        analyzer.set_content_parameters(
                            intent="commercial",
                            keywords=[]
                        )

                        # Extract URLs to scrape
                        urls_to_scrape = [
                            result['link']
                            for result in serp_data.get('organic_results', [])[:5]
                        ]

                        # Scrape competitor content
                        scraped_data = analyzer.scrape_competitor_content(urls_to_scrape)

                        # Generate enhanced outline
                        enhanced_outline = analyzer.generate_enhanced_outline(serp_data, scraped_data)
                        st.session_state.outline = enhanced_outline

                    # Show success message after spinner completes
                    st.success("Outline generated successfully!")
                    
                    # Re-run the app to update the UI with the outline
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.write("Please check your API keys and try again.")

    # Right column: Output text box
    with col2:
        st.subheader("Output")
        st.text_area(
            "Generated Outline",
            value=st.session_state.outline,
            height=500,
            disabled=True,
            placeholder="Your generated outline will appear here..."
        )

    # Footer
    st.markdown("""
        <hr>
        <p style='text-align: center; color: #666;'>
        Powered by Appscrip
        </p>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
