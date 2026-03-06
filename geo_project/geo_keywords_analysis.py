#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
地理信息科学论文关键词采集与分析
数据来源: OpenAlex (https://openalex.org/)
功能:
1. 搜索地理信息科学相关论文，获取标题、年份、关键词(concepts)
2. 保存为CSV表格
3. 统计关键词频率，生成词云（中文显示）
4. 构建关键词共现网络，保存为GraphML并绘制网络图（中文标签）
5. 绘制每年论文数量柱状图
6. 绘制热门关键词随时间变化趋势图
"""

import requests
import pandas as pd
import time
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import networkx as nx

# ==================== 配置参数 ====================
EMAIL = "3314502822@qq.com"          # 用于礼貌池，可换成你的邮箱
SEARCH_TERMS = [
    "remote sensing",
    "GIS",
    "spatial analysis",
    "geographic information science",
    "cartography",
    "geospatial",
    "land use",
    "urban planning"
]
MAX_RESULTS_PER_TERM = 50            # 每个关键词最多采集论文数
OUTPUT_CSV = "geo_papers.csv"
WORDCLOUD_IMAGE = "wordcloud.png"
NETWORK_IMAGE = "cooccurrence_network.png"
GRAPHML_FILE = "cooccurrence_network.graphml"
YEARLY_PLOT = "yearly_papers.png"
TREND_PLOT = "keyword_trends.png"

# 中文字体配置
# 词云字体路径（使用黑体 .ttf）
FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"
# matplotlib 字体设置（使用黑体名称）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 数据采集 ====================
def fetch_papers(term, max_results=50):
    """从OpenAlex搜索包含特定术语的论文，返回列表"""
    base_url = "https://api.openalex.org/works"
    params = {
        "search": term,
        "per-page": 25,
        "sort": "publication_date:desc",
        "mailto": EMAIL
    }
    papers = []
    page = 1
    while len(papers) < max_results:
        params["page"] = page
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"请求失败，状态码: {resp.status_code}")
                break
            data = resp.json()
            works = data.get("results", [])
            if not works:
                break
            for work in works:
                # 提取概念（关键词）
                concepts = work.get("concepts", [])
                keywords = [c["display_name"] for c in concepts if c["score"] > 0.3]
                papers.append({
                    "title": work.get("title", ""),
                    "year": work.get("publication_year"),
                    "keywords": "; ".join(keywords),
                    "keyword_list": keywords,      # 保留列表形式便于后续分析
                    "source": "OpenAlex",
                    "doi": work.get("doi", "")
                })
                if len(papers) >= max_results:
                    break
            print(f"  {term}: 已获取 {len(papers)} 篇")
            page += 1
            time.sleep(1)  # 礼貌性延迟
        except Exception as e:
            print(f"请求出错: {e}")
            break
    return papers

def collect_all_papers():
    """收集所有搜索词的结果，去重（基于DOI）"""
    all_papers = []
    seen_dois = set()
    for term in SEARCH_TERMS:
        print(f"\n正在搜索: {term}")
        papers = fetch_papers(term, MAX_RESULTS_PER_TERM)
        for p in papers:
            doi = p["doi"]
            if doi and doi not in seen_dois:
                seen_dois.add(doi)
                all_papers.append(p)
            elif not doi:  # 如果没有DOI，直接添加（可能有重复标题，这里简化）
                all_papers.append(p)
        time.sleep(2)
    return all_papers

# ==================== 关键词频率分析 ====================
def extract_all_keywords(papers):
    """从论文列表中提取所有关键词（平铺）"""
    all_kw = []
    for p in papers:
        all_kw.extend(p["keyword_list"])
    return all_kw

def plot_wordcloud(keywords, output_file):
    """生成词云（使用指定中文字体）"""
    counter = Counter(keywords)
    wordcloud = WordCloud(
        width=1200,
        height=800,
        background_color="white",
        max_words=100,
        font_path=FONT_PATH,          # 关键：使用你提供的字体路径
        colormap="viridis"
    ).generate_from_frequencies(counter)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("地理信息科学研究关键词词云", fontsize=16)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"词云已保存至 {output_file}")

# ==================== 构建关键词共现网络 ====================
def build_cooccurrence_network(papers, min_occur=2):
    """
    构建关键词共现网络：
    - 节点：关键词（出现次数 >= min_occur）
    - 边：两个关键词在同一篇论文中出现
    返回networkx图对象
    """
    all_kw = extract_all_keywords(papers)
    kw_count = Counter(all_kw)
    valid_kws = {kw for kw, cnt in kw_count.items() if cnt >= min_occur}
    
    cooccur = defaultdict(lambda: defaultdict(int))
    for p in papers:
        kws = p["keyword_list"]
        kws = [kw for kw in kws if kw in valid_kws]
        for i in range(len(kws)):
            for j in range(i+1, len(kws)):
                a, b = sorted([kws[i], kws[j]])
                cooccur[a][b] += 1
    
    G = nx.Graph()
    for kw in valid_kws:
        G.add_node(kw, count=kw_count[kw])
    for a, neighbors in cooccur.items():
        for b, weight in neighbors.items():
            if weight >= 1:
                G.add_edge(a, b, weight=weight)
    return G

def plot_network(G, output_file):
    """绘制网络图（中文标签）"""
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=2, iterations=50)
    node_sizes = [G.nodes[node]["count"] * 50 for node in G.nodes]
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="lightblue", alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=1, alpha=0.5, edge_color="gray")
    nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif")
    plt.title("地理信息科学关键词共现网络", fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"网络图已保存至 {output_file}")

def save_graphml(G, filename):
    """保存为GraphML格式，可用Gephi打开"""
    nx.write_graphml(G, filename)
    print(f"网络数据已保存至 {filename}")

# ==================== 年份相关可视化 ====================
def plot_yearly_papers(papers, output_file):
    """统计每年论文数量并绘制柱状图"""
    years = [p["year"] for p in papers if p["year"] is not None]
    if not years:
        print("没有年份数据，跳过年份分析")
        return
    year_counts = Counter(years)
    sorted_years = sorted(year_counts.items())
    x = [str(y) for y, _ in sorted_years]
    y = [cnt for _, cnt in sorted_years]
    
    plt.figure(figsize=(12, 6))
    plt.bar(x, y, color="steelblue")
    plt.xlabel("年份")
    plt.ylabel("论文数量")
    plt.title("地理信息科学领域论文年发表量趋势", fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"年份柱状图已保存至 {output_file}")

def plot_keyword_trends(papers, top_n=10, output_file="keyword_trends.png"):
    """绘制热门关键词随时间的变化趋势（折线图）"""
    # 收集每个关键词出现的年份
    kw_year = defaultdict(list)
    for p in papers:
        year = p["year"]
        if year is None:
            continue
        for kw in p["keyword_list"]:
            kw_year[kw].append(year)
    
    # 获取所有年份范围
    all_years = sorted(set(y for yrs in kw_year.values() for y in yrs))
    # 计算每个关键词每年的出现次数
    trends = {}
    for kw, years in kw_year.items():
        if len(years) < 3:   # 忽略出现次数太少的关键词
            continue
        year_counts = Counter(years)
        series = [year_counts.get(y, 0) for y in all_years]
        trends[kw] = series
    
    # 按总出现次数排序，取前top_n
    sorted_kws = sorted(trends.items(), key=lambda x: sum(x[1]), reverse=True)[:top_n]
    
    plt.figure(figsize=(14, 8))
    for kw, series in sorted_kws:
        plt.plot(all_years, series, marker='o', label=kw)
    
    plt.xlabel("年份")
    plt.ylabel("出现次数")
    plt.title("热门关键词随时间变化趋势", fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"关键词趋势图已保存至 {output_file}")

# ==================== 主程序 ====================
def main():
    print("=" * 60)
    print("地理信息科学论文关键词采集与分析")
    print("数据来源: OpenAlex")
    print("=" * 60)
    
    # 1. 采集数据
    print("\n开始采集论文数据...")
    papers = collect_all_papers()
    print(f"\n共采集到 {len(papers)} 篇唯一论文")
    
    # 2. 保存原始表格（去掉keyword_list列）
    df = pd.DataFrame(papers)
    df_display = df.drop(columns=["keyword_list"])
    df_display.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"表格已保存至 {OUTPUT_CSV}")
    
    # 3. 提取所有关键词
    all_keywords = extract_all_keywords(papers)
    print(f"共提取到 {len(all_keywords)} 个关键词（含重复）")
    
    # 4. 生成词云
    if all_keywords:
        plot_wordcloud(all_keywords, WORDCLOUD_IMAGE)
    
    # 5. 构建共现网络
    G = build_cooccurrence_network(papers, min_occur=2)
    print(f"网络包含 {G.number_of_nodes()} 个节点，{G.number_of_edges()} 条边")
    save_graphml(G, GRAPHML_FILE)
    plot_network(G, NETWORK_IMAGE)
    
    # 6. 年份柱状图
    plot_yearly_papers(papers, YEARLY_PLOT)
    
    # 7. 关键词趋势图
    plot_keyword_trends(papers, top_n=8, output_file=TREND_PLOT)
    
    print("\n所有分析完成！")

if __name__ == "__main__":
    main()