from firecrawl import FirecrawlApp
import json
from datetime import datetime
from typing import List, Dict
import time
import re
from bs4 import BeautifulSoup
from collections import Counter
from openai import OpenAI
import requests
import streamlit as st

class LLMEnhancedAnalyzer:
    def __init__(self, firecrawl_api_key: str, openai_api_key: str):
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.article_intent = ""
        self.secondary_keywords = []

    def set_content_parameters(self, intent: str, keywords: List[str]):
        """Set the content parameters for better LLM analysis"""
        self.article_intent = intent
        self.secondary_keywords = keywords

    def extract_serp_data(self, data: Dict) -> Dict:
        """Extract data from SERP API results"""
        return {
            'organic_results': self.extract_organic_results(data),
            'paa_questions': self.extract_paa_questions(data),
            'related_searches': self.extract_related_searches(data)
        }

    def extract_organic_results(self, data: Dict) -> List[Dict]:
        """Extract organic results from SERP data"""
        results = []
        for article in data.get('organic_results', []):
            result = {
                'title': article.get('title', ''),
                'link': article.get('link', ''),
                'date': article.get('date', ''),
                'snippet': article.get('snippet', ''),
                'position': article.get('position', ''),
                'displayed_link': article.get('displayed_link', '')
            }
            results.append(result)
        return results

    def extract_paa_questions(self, data: Dict) -> List[Dict]:
        """Extract People Also Ask questions"""
        questions = []
        for question in data.get('related_questions', []):
            questions.append({
                'question': question.get('question', ''),
                'snippet': question.get('snippet', ''),
                'title': question.get('title', '')
            })
        return questions

    def extract_related_searches(self, data: Dict) -> List[Dict]:
        """Extract related searches"""
        return [{'query': search.get('query', '')} 
                for search in data.get('related_searches', [])]

    def scrape_competitor_content(self, urls: List[str]) -> List[Dict]:
        """Scrape and analyze competitor content"""
        scraped_content = []
        
        for url in urls:
            try:
                # Basic scraping parameters
                params = {
                    'formats': ['markdown', 'html']
                }
                
                # Perform the scrape with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        result = self.firecrawl.scrape_url(url, params=params)
                        
                        # Get content with fallback
                        content = result.get('html', result.get('markdown', ''))
                        
                        # Analyze the content
                        analysis = self.analyze_content(content)
                        
                        content_data = {
                            'url': url,
                            'content': content,
                            'analysis': analysis
                        }
                        
                        scraped_content.append(content_data)
                        print(f"Successfully scraped: {url}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            print(f"Error scraping {url}: {str(e)}")
                        else:
                            print(f"Retry {attempt + 1} for {url}")
                            time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                continue
                
        return scraped_content

    def analyze_content(self, content: str) -> Dict:
        """Analyze scraped content for insights"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text() if soup.get_text() else content

            analysis = {
                'word_count': len(text_content.split()),
                'common_phrases': self.extract_common_phrases(text_content),
                'content_structure': self.analyze_content_structure(text_content),
                'key_topics': self.extract_key_topics(text_content),
                'content_elements': self.identify_content_elements(content)
            }
            return analysis
        except Exception as e:
            print(f"Error in content analysis: {str(e)}")
            return {}

    def get_llm_analysis(self, context: str, system_prompt: str) -> str:
        """Get LLM analysis using OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            return ""

    def analyze_with_llm(self, scraped_data: List[Dict], serp_data: Dict) -> Dict:
        """Analyze content using LLM"""
        
        # Prepare context for LLM
        context = self.prepare_llm_context(scraped_data, serp_data)
        
        # Define system prompts
        prompts = {
            'outline_structure': """

You're an expert content strategist and CRO specialist. Using the input fields, SERP data, and competitor analysis, create a high-converting, SEO-optimized landing page outline following the below page structure. Combine the best of SERP results for {search_query}, following EEAT, AEO, GEO, and CRO best practices.

## Input Fields:
- Primary Keyword: {search_query}
- Business Type: (infer from {search_query})
- Secondary Keywords: {secondary_keywords}
- SERP Data: {serp_data}
- Scraped Competitor Data: {scraped_data}

## Instructions:

### Step 1: SERP Analysis
- Search {search_query} in USA.
- Analyze top pages for structure, user intent, keyword focus, and common content themes.

### Step 2: Create High-Converting Landing Page Outline

#### Meta Info:
- Meta Title (≤60 characters)
- Meta Description (≤160 characters)
- Slug (URL structure)

#### Content Outline Following the $10,000,000 Landing Page Structure:

**VISUAL HIERARCHY LAYER**

1. **H1 (3-5 options)**: Strong headlines using {search_query} + unique value proposition placed above the fold
   - Offer Above the Fold: Clear, compelling main headline that instantly communicates value
   - Subheading that addresses main pain point
   - First CTA placement

2. **Short Lead with Social Proof**:
   - Brief 2-3 sentence overview targeting user intent and establishing credibility
   - Include immediate trust indicators (logos, numbers, credentials)
   
3. **Google Reviews Section**:
   - Strategic placement of star ratings and testimonial snippets
   - Highlight total review count and average rating

**PERSUASION LAYER**

4. **Reason-Why Benefit Bullets**:
   - Transform features into 5-7 compelling outcome-focused bullets
   - Each bullet should follow the "benefit → because → feature" format

5. **Dramatic Testimonial Video Section**:
   - Placement for customer success story video
   - Include video thumbnail with compelling quote overlay
   - Text backup for key video points

6. **How It Works Section**:
   - Simple 3-5 step process with icons/visuals
   - Remove uncertainty from the decision-making process
   - Include micro-CTAs within this section

**QUALIFICATION LAYER**

7. **Strategic Customer Callout**:
   - "This is for you if..." and "This is NOT for you if..." statements
   - Pre-filters ideal prospects and qualifies visitors

8. **Service Overview**:
   - Detailed explanation of the offering with location relevance
   - Pricing & Offers – Plans, discounts, or local deals
   - Service Areas – List of covered regions + Google Maps embed

9. **Qualification Panel**:
   - Specific criteria that ideal customers should meet
   - Reinforces exclusivity and quality

10. **FAQ Section**:
    - 5-7 strategic questions based on PAA or related searches
    - Address objections and remove roadblocks
    - Each FAQ should end by subtly asking for action

11. **Final CTA Block**:
    - Strong action-oriented CTA after building maximum value
    - Create urgency and scarcity elements
    - Reinforce main benefits one last time

### Step 3: EEAT & Conversion Elements

**EEAT Enhancement Elements**:
- Placement for certifications, partnerships, press features
- Expert bio section recommendations
- Trust indicators throughout the page

**Conversion Optimization Add-ons**:
- Strategic CTA button placement and copy variations
- Visual element recommendations (images, icons, graphics)
- Mobile UX optimization tips
- Form design best practices
- Trust badge placement recommendations

### Step 4: Landing Page Format Recommendation
- Suggest the best layout type (e.g., service page, SaaS page, clone app page)
- Justify based on SERP, user intent, and top competitors
- Recommend content priority based on the $10,000,000 landing page structure

## Format the response as:
- Clean, organized headings and subheadings
- Include specific content recommendations for each section
- Provide both structure and actual content suggestions
- Highlight key conversion elements with specific placement guidance
- Include notes on visual hierarchy importance
"""
        }
        
        # Get LLM analysis for each aspect
        analysis = {}
        for aspect, prompt in prompts.items():
            print(f"Getting LLM analysis for: {aspect}")
            analysis[aspect] = self.get_llm_analysis(context, prompt)
            time.sleep(1)  # Rate limiting
        
        return analysis

    def prepare_llm_context(self, scraped_data: List[Dict], serp_data: Dict) -> str:
        """Prepare context for LLM analysis"""
        serp_analysis = self.extract_serp_data(serp_data)
        
        context = f"""
Search Query: {serp_data.get('search_parameters', {}).get('q', '')}

Content Parameters:
Article Intent: {self.article_intent}
Secondary Keywords: {', '.join(self.secondary_keywords)}

Top Ranking Articles:
{self.format_top_articles(serp_analysis['organic_results'])}

People Also Ask Questions:
{self.format_paa_questions(serp_analysis['paa_questions'])}

Related Searches:
{self.format_related_searches(serp_analysis['related_searches'])}

Competitor Content Analysis:
{self.format_competitor_content(scraped_data)}
"""
        return context

    def generate_enhanced_outline(self, serp_data: Dict, scraped_data: List[Dict]) -> str:
        """Generate enhanced marketing outline using LLM insights"""
        print("Starting LLM analysis...")
        llm_insights = self.analyze_with_llm(scraped_data, serp_data)
        
        print("Formatting final outline...")
        return self.format_llm_outline(llm_insights, serp_data)

    # Helper methods with proper error handling
    def format_top_articles(self, results: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {result['title']}\n  URL: {result['link']}"
                for result in results[:5]
            ])
        except Exception as e:
            print(f"Error formatting top articles: {str(e)}")
            return ""

    def format_paa_questions(self, questions: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {q['question']}"
                for q in questions
            ])
        except Exception as e:
            print(f"Error formatting PAA questions: {str(e)}")
            return ""

    def format_related_searches(self, searches: List[Dict]) -> str:
        try:
            return "\n".join([
                f"- {search['query']}"
                for search in searches
            ])
        except Exception as e:
            print(f"Error formatting related searches: {str(e)}")
            return ""

    def format_competitor_content(self, scraped_data: List[Dict]) -> str:
        try:
            content_summary = []
            for data in scraped_data:
                analysis = data.get('analysis', {})
                summary = f"""
URL: {data.get('url', '')}
Word Count: {analysis.get('word_count', 0)}
Key Topics: {', '.join(analysis.get('key_topics', [])[:5])}
"""
                content_summary.append(summary)
            return "\n".join(content_summary)
        except Exception as e:
            print(f"Error formatting competitor content: {str(e)}")
            return ""

    def format_llm_outline(self, llm_insights: Dict, serp_data: Dict) -> str:
        """Format LLM insights into the final outline"""
        try:
            # Get the outline structure content
            outline_content = llm_insights.get('outline_structure', 'No outline structure generated')
            
            # Remove markdown formatting (** and *)
            outline_content = outline_content.replace('**', '')
            outline_content = outline_content.replace('*', '')
            
            # Format the outline with proper sections
            outline = f"""
Meta Information:
{outline_content}
END
"""
            return outline.strip()
        except Exception as e:
            print(f"Error formatting LLM outline: {str(e)}")
            raise Exception(f"Failed to generate outline: {str(e)}")

    def extract_common_phrases(self, text_content: str) -> List[str]:
        """Extract common phrases from text content"""
        try:
            # Basic phrase extraction using regex
            phrases = re.findall(r'\b[\w\s]{10,30}\b', text_content.lower())
            # Count and return most common phrases
            phrase_counter = Counter(phrases)
            return [phrase for phrase, count in phrase_counter.most_common(10)]
        except Exception as e:
            print(f"Error extracting common phrases: {str(e)}")
            return []

    def analyze_content_structure(self, text_content: str) -> Dict:
        """Analyze content structure including headings and sections"""
        try:
            # Basic structure analysis
            paragraphs = text_content.split('\n\n')
            structure = {
                'total_paragraphs': len(paragraphs),
                'avg_paragraph_length': sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            }
            return structure
        except Exception as e:
            print(f"Error analyzing content structure: {str(e)}")
            return {}

    def extract_key_topics(self, text_content: str) -> List[str]:
        """Extract key topics from content"""
        try:
            # Simple keyword extraction
            words = re.findall(r'\b\w+\b', text_content.lower())
            # Filter common words and get most frequent
            word_counter = Counter(words)
            return [word for word, count in word_counter.most_common(10)]
        except Exception as e:
            print(f"Error extracting key topics: {str(e)}")
            return []

    def identify_content_elements(self, content: str) -> Dict:
        """Identify various content elements like lists, tables, etc."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            elements = {
                'lists': len(soup.find_all(['ul', 'ol'])),
                'tables': len(soup.find_all('table')),
                'images': len(soup.find_all('img')),
                'links': len(soup.find_all('a')),
                'headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            }
            return elements
        except Exception as e:
            print(f"Error identifying content elements: {str(e)}")
            return {}

def get_search_results(query: str, api_key: str, num_results: int = 10) -> Dict:
    """Get search results from SerpAPI with retry logic"""
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": "en",  # Language
        "gl": "us"   # Country
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}, {response.text}")
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed after {max_retries} attempts: {str(e)}")
                return None
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(2)  # Wait 2 seconds before retrying
    
    return None

def main():
    try:
        # API Keys
# In your streamlit_app.py
        FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
        SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

        # Get search query from user
        search_query = input("Enter your search query: ")

        # Get SERP data directly using SerpAPI
        print("Fetching SERP data...")
        serp_data = get_search_results(search_query, SERPAPI_KEY)
        
        if not serp_data: 
            raise Exception("Failed to fetch SERP data")

        # Initialize analyzer with API keys
        analyzer = LLMEnhancedAnalyzer(
            firecrawl_api_key=FIRECRAWL_API_KEY,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Set default content parameters
        analyzer.set_content_parameters(
            intent="commercial",  # Default intent
            keywords=[]  # Empty keywords list
        )
        
        # Extract URLs to scrape
        urls_to_scrape = [
            result['link'] 
            for result in serp_data.get('organic_results', [])[:5]
        ]
        
        # Scrape competitor content
        print("Scraping competitor content...")
        scraped_data = analyzer.scrape_competitor_content(urls_to_scrape)
        
        # Generate enhanced outline with LLM insights
        print("Generating enhanced outline...")
        enhanced_outline = analyzer.generate_enhanced_outline(serp_data, scraped_data)
        
        # Save the enhanced outline
        print("Saving outline...")
        with open('landing outline5.txt', 'w', encoding='utf-8') as f:
            f.write(enhanced_outline)
        
        print("LLM-enhanced marketing outline generated successfully!")
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()


# You’re an expert content strategist. Using the input fields, SERP data, and competitor analysis, create a high-converting, SEO-optimized landing page outline. Combine the best of SERP results for {search_query}, following EEAT, AEO, GEO, and CRO best practices.
# Input Fields:
#    -Primary Keyword: {search_query}
#    -Business Type: {business_type} (optional)
#    -Secondary Keywords: {secondary_keywords}
#    -SERP Data: {serp_data}
#    -Scraped Competitor Data: {scraped_data}

# Instructions:
# Step 1: SERP Analysis
#    Search {search_query} in USA.
#    Analyze top pages for structure, user intent, keyword focus, and common content themes.
# Step 2: Create Landing Page Outline
#    Meta Info:
#       Meta Title (≤60 characters)
#       Meta Description (≤160 characters)
#       Slug (URL structure)

#    Content Outline:
#       H1 (3–5 options): Strong headlines using {search_query} + unique value
#       Intro: Brief overview targeting user intent and local relevance
#       Sections (use H2/H3 as needed):
#       Service Overview – Explain the offering and location tie-in
#       Why Choose Us – USPs, testimonials, trust elements
#       How It Works – Simple 3–5 step process
#       Pricing & Offers – Plans, discounts, or local deals
#       Service Areas – List of covered regions + Google Maps
#       CTA Block – "Get a free quote", "Book now", etc.

#    EEAT Elements:
#       Mention certifications, partnerships, press features, reviews
    
# Conversion Add-ons:
#       CTA buttons, visuals, FAQs, trust badges, mobile UX tips

#    FAQs:
#       5 local-intent questions based on PAA or related searches

#    Landing Page Format Recommendation
#       Suggest the best layout type (e.g., service page, SaaS page, clone app page)
#       Justify based on SERP, user intent, and top competitors 

# Format and structure the resonse as headings and sub headings and their content accordingly
