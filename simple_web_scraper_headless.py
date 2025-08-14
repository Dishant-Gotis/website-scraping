#!/usr/bin/env python3
"""
Simple Web Scraper (Headless) - One tool to scrape any website (headless mode)
"""
import os
import sys
import time
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class SimpleWebScraper:
    def __init__(self):
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver in headless mode."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--headless=new")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            raise
    
    def scrape_website(self, url):
        try:
            self.driver.get(url)
            time.sleep(5)
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            data = {
                'url': url,
                'title': self.get_title(soup),
                'headings': self.get_headings(soup),
                'paragraphs': self.get_paragraphs(soup),
                'links': self.get_links(soup),
                'images': self.get_images(soup),
                'meta_tags': self.get_meta_tags(soup),
                'abstract': self.get_abstract(soup),
                'full_text': self.get_full_text(soup)
            }
            if not os.path.exists('data'):
                os.makedirs('data')
            domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
            json_filename = f"data/{domain}_scraped_data.json"
            txt_filename = f"data/{domain}_scraped_data.txt"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"WEBSITE SCRAPED DATA\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(f"URL: {url}\n")
                f.write(f"Title: {data['title']}\n\n")
                if data['abstract']:
                    f.write(f"ABSTRACT:\n{data['abstract']}\n\n")
                if data['headings']:
                    f.write(f"HEADINGS:\n")
                    for heading in data['headings']:
                        f.write(f"{heading['level'].upper()}: {heading['text']}\n")
                    f.write("\n")
                if data['paragraphs']:
                    f.write(f"PARAGRAPHS:\n")
                    for i, para in enumerate(data['paragraphs'][:20], 1):
                        f.write(f"{i}. {para}\n\n")
                if data['links']:
                    f.write(f"LINKS (first 20):\n")
                    for i, link in enumerate(data['links'][:20], 1):
                        f.write(f"{i}. {link['text']} -> {link['href']}\n")
                    f.write("\n")
                if data['meta_tags']:
                    f.write(f"META TAGS:\n")
                    for name, content in data['meta_tags'].items():
                        f.write(f"{name}: {content}\n")
                    f.write("\n")
                f.write(f"FULL TEXT LENGTH: {len(data['full_text'])} characters\n")
                f.write(f"TOTAL HEADINGS: {len(data['headings'])}\n")
                f.write(f"TOTAL PARAGRAPHS: {len(data['paragraphs'])}\n")
                f.write(f"TOTAL LINKS: {len(data['links'])}\n")
                f.write(f"TOTAL IMAGES: {len(data['images'])}\n")
            return data
        except Exception as e:
            return None
    
    def scrape_multiple_websites(self, urls):
        results = []
        successful = 0
        failed = 0
        for i, url in enumerate(urls, 1):
            result = self.scrape_website(url)
            if result:
                results.append(result)
                successful += 1
            else:
                failed += 1
            if i < len(urls):
                time.sleep(2)
        return results
    
    def get_title(self, soup):
        title = soup.find('title')
        return title.get_text().strip() if title else "No title found"
    
    def get_headings(self, soup):
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append({
                'level': tag.name,
                'text': tag.get_text().strip()
            })
        return headings
    
    def get_paragraphs(self, soup):
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)
        return paragraphs
    
    def get_links(self, soup):
        links = []
        for a in soup.find_all('a', href=True):
            links.append({
                'text': a.get_text().strip(),
                'href': a['href']
            })
        return links
    
    def get_images(self, soup):
        images = []
        for img in soup.find_all('img'):
            images.append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        return images
    
    def get_meta_tags(self, soup):
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                meta_tags[name] = content
        return meta_tags
    
    def get_abstract(self, soup):
        abstract_selectors = [
            '.abstract', '.summary', '.excerpt', '.description',
            '[class*="abstract"]', '[class*="summary"]',
            '.article-abstract', '.paper-abstract', '.content-abstract'
        ]
        for selector in abstract_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text().strip()
            except:
                continue
        return None
    
    def get_full_text(self, soup):
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def close(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

def load_urls_from_file(filename):
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        return urls
    except FileNotFoundError:
        return []

def main():
    scraper = SimpleWebScraper()
    try:
        if len(sys.argv) > 1:
            if sys.argv[1].endswith('.txt'):
                urls = load_urls_from_file(sys.argv[1])
                if urls:
                    scraper.scrape_multiple_websites(urls)
            else:
                urls = sys.argv[1:]
                if len(urls) == 1:
                    scraper.scrape_website(urls[0])
                else:
                    scraper.scrape_multiple_websites(urls)
        else:
            while True:
                print("\nOptions:")
                print("1. Enter single URL")
                print("2. Enter multiple URLs (separated by space)")
                print("3. Load URLs from file")
                print("4. Quit")
                choice = input("\nEnter your choice (1-4): ").strip()
                if choice == '1':
                    url = input("Enter website URL: ").strip()
                    if url:
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        scraper.scrape_website(url)
                elif choice == '2':
                    urls_input = input("Enter URLs (separated by space): ").strip()
                    urls = [url.strip() for url in urls_input.split() if url.strip()]
                    for i, url in enumerate(urls):
                        if not url.startswith(('http://', 'https://')):
                            urls[i] = 'https://' + url
                    if urls:
                        scraper.scrape_multiple_websites(urls)
                elif choice == '3':
                    filename = input("Enter filename (e.g., urls.txt): ").strip()
                    urls = load_urls_from_file(filename)
                    if urls:
                        scraper.scrape_multiple_websites(urls)
                elif choice == '4':
                    break
                else:
                    pass
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
 