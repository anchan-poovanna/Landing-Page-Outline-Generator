import streamlit as st
from landing_generator import LLMEnhancedAnalyzer, get_search_results
from datetime import datetime
import time
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# Get API keys from environment variables or use defaults
# In your streamlit_app.py
FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

# Configure page
st.set_page_config(page_title="Landing Page Outline Generator", layout="wide")

# Add custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .medium-font {
        font-size:16px !important;
        line-height: 1.6;
    }
    .medium-font p {
        margin-bottom: 20px;
    }
    .medium-font strong {
        color: #1f77b4;
    }
    .log-font {
        font-family: 'Courier New', Courier, monospace;
        font-size:14px;
        color: #00ff00;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: rgba(0, 0, 0, 0.2);
        border-left: 3px solid #00ff00;
        box-shadow: 0 2px 4px rgba(0, 255, 0, 0.1);
        transition: all 0.3s ease;
    }
    .log-font:hover {
        transform: translateX(5px);
        box-shadow: 2px 2px 8px rgba(0, 255, 0, 0.2);
    }
    .section-h2 {
        font-size: 20px !important;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 20px;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #1f77b4;
    }
    
    .section-h3 {
        font-size: 16px !important;
        font-weight: 500;
        color: #34495e;
        margin-top: 12px;
        margin-bottom: 8px;
        padding-left: 15px;
    }
    
    .section-content {
        padding-left: 20px;
        margin-bottom: 10px;
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)

def display_enhanced_outline(enhanced_outline: str):
    """Display enhanced outline with improved error handling and content parsing"""
    try:
        if not enhanced_outline or not isinstance(enhanced_outline, str):
            st.error("No valid outline content available")
            return

        # Define sections and their delimiters based on the prompt's expected output format
        sections = {
            "Meta Title": ("Meta title:", "Meta description:"),
            "Meta Description": ("Meta description:", "Slug:"),
            "Slug": ("Slug:", "Outline:"),
            "H1": ("H1:", "Introduction:"),
            "Introduction": ("Introduction:", "Section Breakdown:"),
            "Section Breakdown": ("Section Breakdown:", "FAQ:"),
            "FAQ": ("FAQ:", "Writing Guidelines:"),
            "Writing Guidelines": ("Writing Guidelines:", "Landing Page Format Prediction:"),
            "Landing Page Format": ("Landing Page Format Prediction:", "Justification:"),
            "Justification": ("Justification:", None)
        }

        st.markdown("<p class='big-font'>Enhanced Content Outline:</p>", unsafe_allow_html=True)
        
        for section_name, (start_delimiter, end_delimiter) in sections.items():
            try:
                content = safe_split(enhanced_outline, start_delimiter, end_delimiter)
                
                if not content:
                    continue  # Skip empty sections
                
                # Special formatting for sections with bullet points or numbered lists
                if section_name in ["H1 Options", "Writing Guidelines", "FAQ"]:
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>{section_name}:</strong></p>", unsafe_allow_html=True)
                    options = [opt.strip() for opt in content.split('\n') if opt.strip()]
                    
                    # Handle numbered lists (for FAQ) and bullet points
                    for i, opt in enumerate(options, 1):
                        # Remove existing numbers or bullet points
                        opt = re.sub(r'^\d+\.\s*', '', opt)  # Remove numbers
                        opt = re.sub(r'^[-•]\s*', '', opt)   # Remove bullet points
                        
                        if section_name == "FAQ":
                            st.markdown(f"{i}. {opt}", unsafe_allow_html=True)
                        else:
                            st.markdown(f"• {opt}", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Special formatting for Section Breakdown
                elif section_name == "Section Breakdown":
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>{section_name}:</strong></p>", unsafe_allow_html=True)
                    # Split content by H2 and H3 headers
                    sections = content.split('\n')
                    current_h2 = None
                    
                    for section in sections:
                        if section.strip():
                            if section.startswith('H2:'):
                                current_h2 = section[3:].strip()
                                st.markdown(f"<div class='section-h2'>{current_h2}</div>", unsafe_allow_html=True)
                            elif section.startswith('H3:'):
                                h3_content = section[3:].strip()
                                st.markdown(f"<div class='section-h3'>• {h3_content}</div>", unsafe_allow_html=True)
                            else:
                                # Regular content
                                st.markdown(f"<div class='section-content'>{section}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Special formatting for H1 section
                elif section_name == "H1":
                    st.markdown("<div class='medium-font'>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>{section_name}:</strong></p>", unsafe_allow_html=True)
                    
                    # Clean and format H1 options
                    content = content.replace("Options:", "").strip()  # Remove "Options:" text
                    
                    # Split by numbers and clean up
                    options = re.findall(r'\d+\.\s*([^0-9]+?)(?=\d+\.|$)', content)
                    
                    # If no numbered options found, try splitting by line
                    if not options:
                        options = [opt.strip() for opt in content.split('\n') if opt.strip()]
                    
                    # Display each option in a clean format
                    for i, opt in enumerate(options, 1):
                        opt = opt.strip()
                        if opt:
                            st.markdown(
                                f"""<div style='margin-bottom: 10px; padding: 10px; border-left: 3px solid #1f77b4;'>
                                    {i}. {opt}
                                </div>""", 
                                unsafe_allow_html=True
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                else:
                    st.markdown(
                        f"""<div class='medium-font'>
                            <p><strong>{section_name}:</strong><br>{content}</p>
                        </div>""",
                        unsafe_allow_html=True
                    )
            
            except Exception as e:
                st.warning(f"Error displaying section {section_name}: {str(e)}")
                continue

    except Exception as e:
        st.error(f"Error displaying outline: {str(e)}")

def safe_split(text, delimiter1, delimiter2=None):
    """Extract content from text between two delimiters with flexible matching"""
    try:
        delim1_pattern = re.compile(re.escape(delimiter1).replace(r'\:', r'\s*:?[\s]*'), re.IGNORECASE)
        match1 = delim1_pattern.search(text)
        if not match1:
            alt_delim1 = delimiter1.replace(":", "").strip()
            delim1_pattern = re.compile(re.escape(alt_delim1), re.IGNORECASE)
            match1 = delim1_pattern.search(text)
            if not match1:
                return ""
        start = match1.end()

        if delimiter2:
            delim2_pattern = re.compile(re.escape(delimiter2).replace(r'\:', r'\s*:?[\s]*'), re.IGNORECASE)
            match2 = delim2_pattern.search(text, start)
            if not match2:
                alt_delim2 = delimiter2.replace(":", "").strip()
                delim2_pattern = re.compile(re.escape(alt_delim2), re.IGNORECASE)
                match2 = delim2_pattern.search(text, start)
                if not match2:
                    return text[start:].strip()
            end = match2.start()
            return text[start:end].strip()
        else:
            return text[start:].strip()
    except Exception as e:
        st.error(f"Error processing content: {str(e)}")
        return ""

def main():
    st.markdown("<h1 style='text-align: center;'>Landing Page Outline  Generator</h1>", unsafe_allow_html=True)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    # Left column - Input fields
    with col1:
        st.markdown("<p class='big-font'>Input Parameters</p>", unsafe_allow_html=True)
        search_query = st.text_input("Enter your search query:", key="search_query")
        analyze_button = st.button("Generate Landing Page")

        # Add log section
        st.markdown("<p class='big-font'>Analysis Logs</p>", unsafe_allow_html=True)
        log_placeholder = st.empty()

    # Right column - Results
    with col2:
        if analyze_button and search_query:
            try:
                # Initialize progress bar
                progress_bar = st.progress(0)
                
                def update_log(message, progress_value):
                    current_time = datetime.now().strftime("%H:%M:%S")
                    log_placeholder.markdown(
                        f"""<div class='log-font'>
                            [⏱️ {current_time}] {message}
                            <div style='height: 2px; background: linear-gradient(to right, #00ff00 {progress_value * 100}%, transparent {progress_value * 100}%); margin-top: 5px;'></div>
                        </div>""",
                        unsafe_allow_html=True
                    )
                    progress_bar.progress(progress_value)

                update_log("🚀 Initializing analysis process...", 0.1)
                
                # Get SERP data
                update_log("🔍 Fetching SERP data...", 0.2)
                serp_data = get_search_results(search_query, SERPAPI_KEY)
                
                if not serp_data:
                    st.error("Failed to fetch SERP data")
                    return

                # Initialize analyzer
                update_log("⚙️ Setting up content analyzer...", 0.3)
                analyzer = LLMEnhancedAnalyzer(
                    firecrawl_api_key=FIRECRAWL_API_KEY,
                    openai_api_key=OPENAI_API_KEY
                )
                
                # Set default content parameters
                analyzer.set_content_parameters(
                    intent="commercial",  # Default to commercial intent
                    keywords=[]  # Empty keywords list
                )
                
                # Get URLs to scrape
                urls_to_scrape = [
                    result['link'] 
                    for result in serp_data.get('organic_results', [])[:5]
                    if not any(domain in result['link'].lower() 
                             for domain in ['youtube.com', 'reddit.com', 'twitter.com', 'facebook.com'])
                ]

                update_log("🌐 Analyzing competitor content...", 0.5)
                scraped_data = analyzer.scrape_competitor_content(urls_to_scrape)
                
                update_log("✍️ Generating enhanced outline...", 0.8)
                enhanced_outline = analyzer.generate_enhanced_outline(serp_data, scraped_data)
                
                update_log("🎉 Analysis completed! Displaying results...", 1.0)
                time.sleep(0.5)

                # Display the enhanced outline
                if enhanced_outline:
                    display_enhanced_outline(enhanced_outline)
                else:
                    st.error("Failed to generate enhanced outline.")

            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
        
        elif analyze_button:
            st.warning("Please enter a search query to begin analysis.")

if __name__ == "__main__":
    main() 