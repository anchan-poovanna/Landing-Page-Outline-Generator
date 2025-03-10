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
            'outline_structure': """You are an expert content strategist. Using the provided input fields, SERP data, and competitor analysis, create a comprehensive, SEO-optimized landing page outline. The output should integrate localized details, conversion best practices, and EEAT signals.

Input Fields:
- Primary Keyword: {search_query} (e.g., "Hire carpenters in Texas")
- Location: {location} (e.g., specific city, state, or region)
- Business Type: {business_type} (Optional; if not provided, infer from the primary keyword)
- Secondary Keywords: {secondary_keywords} (Additional related search terms)
- Article Intent: {intent} (E.g., informational, transactional, commercial)
- SERP Data: {serp_data} (Organic results, PAA questions, related searches)
- Scraped Competitor Data: {scraped_data} (Insights from top-ranking competitor content)

Instructions for AI:
Step 1: Conduct a Localized Web Search
  - Analyze the top-ranking pages for "{search_query}" in "{location}".
  - Identify common themes, user intent, competitor strategies, and frequently used subtopics.

Step 2: Generate the Landing Page Outline with SEO-Optimized Structure
1. Meta Information:
   - Title (H1): Craft a compelling headline that incorporates "{search_query}" and a unique value proposition.
   - Meta Title: Create an SEO-friendly title including "{search_query}".
   - Meta Description: Write a click-worthy summary that enhances CTR.
   - URL Structure: Propose an optimized URL format (e.g., "https://www.example.com/{location}/{service}").

2. Section Breakdown:
   - Provide a structured content outline with hierarchical headings (H2s and H3s).
   - Include sections such as:
     • Service Overview: Describe the service and its local relevance.
     • Differentiators: Explain why to choose this service (include unique selling points, testimonials, and trust signals).
     • Process Overview: Detail the steps (e.g., consultation, execution, delivery).
     • Pricing & Availability: Outline pricing options, special offers, or discounts (if applicable).
     • Service Area: Highlight local expertise and nearby regions.
     • Call-to-Action: Insert a strong CTA to prompt immediate engagement.

3. Localized EEAT Elements:
   - Authority: Mention certifications, partnerships, or media mentions.
   - Trust: Include local testimonials, case studies, and Google My Business reviews.
   - Expertise: Provide location-specific insights and solutions.

4. Conversion-Optimized CTAs:
   - Integrate clear, action-driven calls-to-action (e.g., "Get a Free Quote in {location} Today", "Call Now for Immediate Assistance", "Schedule a Consultation in {location}").

5. Additional Optimizations:
   - Suggest embedding Google Maps, internal linking to related services, mobile optimization, and inclusion of high-quality images.

Expected Output Format:
Meta title: [60 chars max]
Meta description: [160 chars max]
Slug: [URL-friendly]
Outline:
H1: [Provide 3-5 headline options]
Introduction: [Brief overview of approach and key points]
[Detailed section breakdown with H2s and H3s as needed]
Conclusion: [Summarize key selling points and reinforce CTA]
FAQ:
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]

Writing Guidelines:
- Word count target: [Based on competitor analysis]
- Content tone: Professional and engaging
- Placement for statistics/data, expert quotes, visuals, and content upgrades
- Key takeaways and internal/external linking strategy

Landing Page Format Prediction:
Based on SERP analysis, competitor data, and "{search_query}", predict the optimal landing page format (e.g., "Lead Generation Page", "Informational Service Page") and provide a justification:
Justification:
- [Explain why this format is ideal based on user search behavior, content structures of top-ranking pages, and competitor insights]  
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


