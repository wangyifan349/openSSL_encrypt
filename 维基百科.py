import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# 配置代理
proxies = {
    "http": "http://127.0.0.1:10809",
    "https": "http://127.0.0.1:10809"
}

def create_session():
    """创建并返回一个带有自定义User-Agent的requests.Session对象。"""
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({'User-Agent': ua.google})
    return session

def fetch_page(session, url):
    """使用给定的session获取页面内容。"""
    try:
        response = session.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            return response.content
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
    return None

def parse_content(html_content):
    """解析HTML内容并提取标题、文本和链接。"""
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.find('h1', {'id': 'firstHeading'}).text

    content_div = soup.find('div', {'class': 'mw-parser-output'})
    paragraphs = content_div.find_all('p')
    text_content = '\n'.join([para.text for para in paragraphs])

    links = set()
    for a_tag in content_div.find_all('a', href=True):
        href = a_tag['href']
        if re.match(r'^/wiki/[^:]*$', href):
            full_url = 'https://en.wikipedia.org' + href
            links.add(full_url)

    return title, text_content, links

def write_to_file(file, url, title, content):
    """将抓取到的内容写入文件。"""
    file.write(f"URL: {url}\n")
    file.write(f"Title: {title}\n")
    file.write(f"Content: {content}\n")
    file.write("="*80 + "\n")

def crawl_wikipedia(start_url, max_depth=2, max_workers=5, output_file='wikipedia_content.txt'):
    visited = set()
    queue = [(start_url, 0)]

    with create_session() as session:
        with open(output_file, 'w', encoding='utf-8') as file:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_page, session, url): (url, depth) for url, depth in queue}

                while futures:
                    for future in as_completed(futures):
                        url, depth = futures[future]
                        del futures[future]

                        if url not in visited and depth <= max_depth:
                            visited.add(url)
                            html_content = future.result()
                            if html_content:
                                title, content, links = parse_content(html_content)
                                write_to_file(file, url, title, content)

                                for link in links:
                                    if link not in visited:
                                        futures[executor.submit(fetch_page, session, link)] = (link, depth + 1)

# 示例用法
start_url = "https://en.wikipedia.org/wiki/Web_scraping"
crawl_wikipedia(start_url)
