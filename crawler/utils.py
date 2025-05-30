import httpx
import nltk
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter
import re
import ssl

# Download NLTK resources (uncomment on first run)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

def scrape_webpage(url):
    """
    Scrape a webpage using httpx and BeautifulSoup4
    
    Args:
        url (str): URL to scrape
        
    Returns:
        dict: Dictionary with title, content, and tags
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "Untitled Page"
            
            # Extract main content by targeting specific container elements
            # First try to find common main content container IDs
            main_content = None
            
            # Try common content container IDs and classes
            content_selectors = [
                'div#main-content', 'div.main-content', 
                'div#content', 'div.content', 
                'main', 'article', 
                'div.post-content', 'div.entry-content'
            ]
            
            # Try each selector until we find content
            for selector in content_selectors:
                content_container = soup.select_one(selector)
                if content_container and content_container.get_text().strip():
                    main_content = content_container
                    break
            
            # If we found a main content container, extract text from it
            if main_content:
                content_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li'])
            else:
                # Otherwise, extract content from after the header if exists
                header = soup.find('header')
                if header:
                    content_elements = []
                    for elem in header.find_next_siblings():
                        if elem.name == 'footer':
                            break
                        content_elements.extend(elem.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']))
                else:
                    # Fallback to extracting from the body but skip headers and footers
                    body = soup.find('body')
                    if body:
                        # Skip headers and footers
                        content_elements = []
                        for elem in body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
                            # Check if element is inside a header or footer
                            parent_tags = [p.name for p in elem.parents]
                            if 'header' not in parent_tags and 'footer' not in parent_tags and 'nav' not in parent_tags:
                                content_elements.append(elem)
                    else:
                        # Last resort - get all content elements from page
                        content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li'])
            
            # Join the text content of elements
            content = ' '.join([element.get_text().strip() for element in content_elements])
            
            # Generate tags using NLP
            tags = extract_keywords(title + " " + content, max_keywords=10)
            
            return {
                'title': title,
                'content': content,
                'tags': tags,
                'source_url': url
            }
    
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def extract_keywords(text, max_keywords=10):
    """
    Extract keywords from text using simple NLP techniques
    
    Args:
        text (str): Text to extract keywords from
        max_keywords (int): Maximum number of keywords to extract
        
    Returns:
        list: List of keywords
    """
    # Clean text
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words and len(token) > 3]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Count word frequencies
    word_freq = Counter(tokens)
    
    # Get most common keywords
    keywords = [word for word, count in word_freq.most_common(max_keywords)]
    
    return keywords

def crawl_and_store(url, model_class):
    """
    Crawl a webpage and store it in the KnowledgeBase model
    
    Args:
        url (str): URL to crawl
        model_class: The model class to store the data in
        
    Returns:
        object: Created model instance or None if failed
    """
    scraped_data = scrape_webpage(url)
    
    if not scraped_data:
        return None
    
    # Check if we already have this URL in the database
    existing = model_class.objects.filter(source_url=url).first()
    
    if existing:
        # Update existing entry
        existing.title = scraped_data['title']
        existing.content = scraped_data['content']
        existing.tags = scraped_data['tags']
        existing.save()
        return existing
    else:
        # Create new entry
        return model_class.objects.create(
            title=scraped_data['title'],
            content=scraped_data['content'],
            tags=scraped_data['tags'],
            source_url=url,
            is_verified=False
        )
