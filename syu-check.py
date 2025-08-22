#!/usr/bin/env python3
"""
Arch Linux Update Checker
Checks archlinux.org/news for recent posts containing warnings about system updates.
"""

import requests
from bs4 import BeautifulSoup
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import subprocess

# Configuration
NEWS_URLS = [
    "https://archlinux.org/news/",  # Primary
    "https://mirror.rackspace.com/archlinux/news/",  # Mirror 1
    "https://mirror.lty.me/archlinux/news/",  # Mirror 2
    "https://mirrors.kernel.org/archlinux/news/",  # Mirror 3
]
# Keywords that might indicate a problematic update
WARNING_KEYWORDS = [
    'manual intervention', 'reboot required', 'hold back', 'warning',
    'break', 'action required', 'incompatible', 'problem', 'issue', 'outages', 'backdoor', 'critical', 'corrupting', 'backdoored'
]

import subprocess

def fetch_news():
    """Try multiple mirrors to fetch the news page."""
    for i, url in enumerate(NEWS_URLS):
        # Try curl first (since it works better)
        result = try_curl(url)
        if result:
            return result

        # If curl fails, try Python requests
        result = try_python_requests(url)
        if result:
            return result

    print("Error: All mirrors and methods failed.")
    sys.exit(1)

def try_curl(url):
    """Try to fetch using curl"""
    try:
        result = subprocess.run([
            'curl',
            '-s',           # Silent mode
            '-L',           # Follow redirects
            '-4',           # Force IPv4 only (skip IPv6)
            '--max-time', '10',  # Timeout after 10 seconds
            url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            return result.stdout
        return None
    except:
        return None

def try_python_requests(url):
    """Try to fetch using Python requests with stealth headers"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        print(f"✅ Success with Python requests: {url}")
        return response.text
    except Exception as e:
        print(f"Python requests failed for {url}: {e}")
        return None
def try_curl(url):
    """Try to fetch using curl"""
    try:
        result = subprocess.run([
            'curl',
            '-s',           # Silent mode
            '-L',           # Follow redirects
            '-4',           # Force IPv4 only (skip IPv6)
            '--max-time', '10',  # Timeout after 10 seconds
            url
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print(f"✅ Success with curl: {url}")
            return result.stdout
        else:
            print(f"curl failed for {url} with return code: {result.returncode}")
            return None
    except Exception as e:
        print(f"curl exception for {url}: {e}")
        return None

def debug_save_html(html_content, filename="debug_output.html"):
    """Saves the HTML content to a file for debugging."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Debug: HTML content saved to {filename}. Please inspect this file.")

def parse_news(html_content):
    """Parses the HTML to extract news titles and dates."""
    soup = BeautifulSoup(html_content, 'html.parser')
    news_items = []

    # Method 1: Look for article elements (common modern pattern)
    for article in soup.find_all('article'):
        title_tag = article.find('h2') or article.find('a')
        date_tag = article.find('time')

        if title_tag and date_tag:
            title = title_tag.get_text().strip()
            date_str = date_tag.get_text().strip()
            link = title_tag.get('href') if title_tag.name == 'a' else None

            if link and not link.startswith('http'):
                link = f"https://archlinux.org{link}"

            news_items.append({'title': title.lower(), 'date': date_str, 'link': link})

    # If we found news with method 1, return them
    if news_items:
        return news_items

    # Method 2: Look for elements with "news" in class name
    for news_item in soup.select('[class*="news"]'):
        title_tag = news_item.find('a')
        if title_tag:
            title = title_tag.get_text().strip()
            # Try to find a date nearby
            date_span = news_item.find('span') or news_item.find('time')
            date_str = date_span.get_text().strip() if date_span else "Recent"

            link = title_tag.get('href')
            if link and not link.startswith('http'):
                link = f"https://archlinux.org{link}"

            news_items.append({'title': title.lower(), 'date': date_str, 'link': link})

    if news_items:
        return news_items

    # Method 3: Look for the news table (old structure)
    news_table = soup.find('table', class_='news')
    if news_table:
        for row in news_table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all('td')
            if len(cells) >= 2:
                date_cell = cells[0]
                title_cell = cells[1]
                title_tag = title_cell.find('a')
                if title_tag:
                    title = title_tag.get_text().strip()
                    date_str = date_cell.get_text().strip()
                    link = title_tag.get('href')
                    if link and not link.startswith('http'):
                        link = f"https://archlinux.org{link}"
                    news_items.append({'title': title.lower(), 'date': date_str, 'link': link})

    if news_items:
        return news_items

    # Method 4: Look for news-item divs (another old structure)
    for item in soup.find_all('div', class_='news-item'):
        title_tag = item.find('a')
        date_span = item.find('span', class_='news-item-date')
        if title_tag and date_span:
            title = title_tag.get_text().strip().lower()
            date = date_span.get_text().strip()
            link = title_tag.get('href')
            if link and not link.startswith('http'):
                link = f"https://archlinux.org{link}"
            news_items.append({'title': title, 'date': date, 'link': link})

    if news_items:
        return news_items

    # Method 5: Generic link analysis as last resort
    print("Debug: Trying generic link analysis...")
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/news/' in href and link.get_text().strip():
            title = link.get_text().strip()
            news_items.append({
                'title': title.lower(),
                'date': "Date not found",
                'link': f"https://archlinux.org{href}" if not href.startswith('http') else href
            })

    return news_items

def check_for_warnings(news_items, num_to_check=5):
    """Checks the most recent news items for warning keywords."""
    recent_news = news_items[:num_to_check] # Check the top 'n' most recent posts
    warnings_found = []

    for news in recent_news:
        if any(keyword in news['title'] for keyword in WARNING_KEYWORDS):
            warnings_found.append(news)

    return warnings_found

def main():
    print("🔍 Checking Arch Linux News for update warnings...\n")

    html = fetch_news()
    if not html:
        print("Error: Could not fetch news from any source.")
        sys.exit(1)

    all_news = parse_news(html)

    if not all_news:
        print("No news posts found. The website structure may have changed.")
        return

    warnings = check_for_warnings(all_news)

    if warnings:
        print("❌ \033[91mWARNING: Potential update issues found!\033[0m")
        # ... warning display code ...
        sys.exit(1)
    else:
        print("✅ \033[92mNo recent warnings found.\033[0m")
        print("It is likely safe to proceed with 'sudo pacman -Syu'.")
        print("(Always remember to read the pacman output carefully before confirming!)")
        sys.exit(0)

if __name__ == "__main__":
    main()
