import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_page_content(self, url: str) -> Dict[str, str]:
        """Extract text content from a single page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Extract main content
            content = soup.get_text()
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
            
            return {
                'url': url,
                'title': title_text,
                'content': content[:5000],  # Limit content length
                'word_count': len(content.split())
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def get_site_links(self, base_url: str, max_pages: int = 50) -> List[str]:
        """Get relevant links from the website"""
        try:
            response = self.session.get(base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = set()
            for link in soup.find_all('a', href=True):
                full_url = urljoin(base_url, link['href'])
                if self.is_valid_url(full_url, base_url):
                    links.add(full_url)
                    if len(links) >= max_pages:
                        break
            
            return list(links)
        except Exception as e:
            logger.error(f"Error getting links from {base_url}: {str(e)}")
            return [base_url]
    
    def is_valid_url(self, url: str, base_url: str) -> bool:
        """Check if URL is valid for scraping"""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        
        # Same domain
        if parsed_url.netloc != parsed_base.netloc:
            return False
            
        # Skip certain file types
        skip_extensions = ['.pdf', '.jpg', '.png', '.gif', '.zip', '.doc']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
            
        return True
    
    def scrape_websites(self, websites: List[str]) -> List[Dict]:
        """Scrape multiple websites"""
        all_content = []
        
        for website in websites:
            logger.info(f"Scraping {website}")
            links = self.get_site_links(website)
            
            for link in links[:20]:  # Limit to 20 pages per site
                content = self.get_page_content(link)
                if content and len(content['content']) > 100:
                    all_content.append(content)
                time.sleep(1)  # Be respectful
        
        logger.info(f"Scraped {len(all_content)} pages total")
        return all_content
