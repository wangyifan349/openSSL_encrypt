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
    ua = UserAgent()  # 使用fake_useragent生成随机User-Agent，以模拟不同浏览器的请求
    session.headers.update({'User-Agent': ua.google})  # 设置User-Agent头部以避免被目标网站封锁
    return session

def fetch_page(session, url):
    """使用给定的session获取页面内容。"""
    try:
        response = session.get(url, proxies=proxies, timeout=10)  # 使用代理和超时机制来获取页面
        if response.status_code == 200:  # 检查请求是否成功（状态码200表示成功）
            return response.content
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")  # 捕获并打印请求异常
    return None

def parse_content(html_content):
    """解析HTML内容并提取标题、文本和链接。"""
    soup = BeautifulSoup(html_content, 'html.parser')  # 使用BeautifulSoup解析HTML
    title = soup.find('h1', {'id': 'firstHeading'}).text  # 提取页面标题

    content_div = soup.find('div', {'class': 'mw-parser-output'})  # 找到主要内容的div
    paragraphs = content_div.find_all('p')  # 提取所有段落
    text_content = '\n'.join([para.text for para in paragraphs])  # 合并段落文本

    links = set()
    for a_tag in content_div.find_all('a', href=True):  # 查找所有链接
        href = a_tag['href']
        if re.match(r'^/wiki/[^:]*$', href):  # 过滤掉非维基百科的内部链接（如文件、分类等）
            full_url = 'https://en.wikipedia.org' + href  # 构造完整的URL
            links.add(full_url)

    return title, text_content, links

def write_to_file(file, url, title, content):
    """将抓取到的内容写入文件。"""
    file.write(f"URL: {url}\n")
    file.write(f"Title: {title}\n")
    file.write(f"Content: {content}\n")
    file.write("="*80 + "\n")  # 分隔符用于区分不同页面的内容

def save_state(visited, queue, state_file='crawler_state.json'):
    """保存爬虫的状态，包括已访问的URL和待访问的队列。"""
    state = {
        'visited': list(visited),  # 将集合转换为列表以便序列化
        'queue': queue
    }
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f)  # 使用JSON格式保存状态

def load_state(state_file='crawler_state.json'):
    """加载爬虫的状态，如果存在的话。"""
    if os.path.exists(state_file):  # 检查状态文件是否存在
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)  # 从JSON文件中加载状态
            return set(state['visited']), state['queue']
    return set(), []

def crawl_wikipedia(start_url, max_depth=2, max_workers=5, output_file='wikipedia_content.txt', state_file='crawler_state.json'):
    """主爬虫函数，负责管理爬虫的执行和状态保存。"""
    visited, queue = load_state(state_file)  # 加载之前的爬虫状态
    if not queue:
        queue.append((start_url, 0))  # 如果队列为空，添加起始URL

    with create_session() as session:
        with open(output_file, 'a', encoding='utf-8') as file:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交初始任务到线程池
                futures = {executor.submit(fetch_page, session, url): (url, depth) for url, depth in queue}

                while futures:
                    for future in as_completed(futures):  # 处理已完成的任务
                        url, depth = futures[future]
                        del futures[future]

                        if url not in visited and depth <= max_depth:  # 检查深度限制和访问状态
                            visited.add(url)  # 将URL标记为已访问
                            html_content = future.result()
                            if html_content:
                                title, content, links = parse_content(html_content)
                                write_to_file(file, url, title, content)

                                for link in links:
                                    if link not in visited:  # 避免重复访问
                                        futures[executor.submit(fetch_page, session, link)] = (link, depth + 1)

                    # 定期保存状态
                    queue = [(url, depth) for future in futures for url, depth in [futures[future]]]
                    save_state(visited, queue, state_file)

# 示例用法
start_url = "https://en.wikipedia.org/wiki/Web_scraping"
crawl_wikipedia(start_url)
