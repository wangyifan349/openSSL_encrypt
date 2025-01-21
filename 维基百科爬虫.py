import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json
import os

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
    title_tag = soup.find('h1', {'id': 'firstHeading'})
    title = title_tag.text if title_tag else "No Title"

    content_div = soup.find('div', {'class': 'mw-parser-output'})
    paragraphs = content_div.find_all('p') if content_div else []
    
    text_content = ""
    for para in paragraphs:
        text_content += para.text + "\n"

    links = set()
    if content_div:
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

def save_state(visited, queue, output_file, state_file='crawler_state.json'):
    """保存爬虫的状态，包括已访问的URL和待访问的队列。"""
    state = {
        'visited': list(visited),
        'queue': queue,
        'output_file': output_file  # 保存文件路径
    }
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f)

def load_state(state_file='crawler_state.json'):
    """加载爬虫的状态，如果存在的话。"""
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            visited = set(state['visited'])
            queue = state['queue']
            output_file = state['output_file']
            return visited, queue, output_file
    return set(), [], 'wikipedia_content.txt'

def check_files(output_file):
    """检查保存文件是否存在，如果不存在则创建。"""
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            pass  # 创建文件

def crawl_wikipedia(start_url, max_depth=2, max_workers=5, state_file='crawler_state.json'):
    """主爬虫函数，负责管理爬虫的执行和状态保存。"""
    visited, queue, output_file = load_state(state_file)
    check_files(output_file)

    if not queue:
        queue.append((start_url, 0))

    with create_session() as session:
        with open(output_file, 'a', encoding='utf-8') as file:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for url, depth in queue:
                    future = executor.submit(fetch_page, session, url)
                    futures[future] = (url, depth)

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
                                        new_future = executor.submit(fetch_page, session, link)
                                        futures[new_future] = (link, depth + 1)

                    # 定期保存状态
                    queue = []
                    for future in futures:
                        url, depth = futures[future]
                        queue.append((url, depth))
                    save_state(visited, queue, output_file, state_file)

# 示例用法
start_url = "https://en.wikipedia.org/wiki/Web_scraping"
crawl_wikipedia(start_url)
