#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
地理信息科学论文关键词综合可视化
基于翻译后的中文关键词数据
输入文件：geo_papers_with_chinese.csv（由翻译脚本生成）
输出文件：
  - keyword_stats.csv / 表格图片
  - wordcloud_cn.png
  - cooccurrence_network_cn.png / .graphml
  - yearly_papers.png
  - keyword_trends_cn.png（可选）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter, defaultdict
import community.community_louvain as community_louvain
from wordcloud import WordCloud
import warnings
warnings.filterwarnings("ignore")

# ==================== 配置区域（请根据实际情况修改）====================
# 输入文件（翻译脚本生成的带中文关键词的文件）
INPUT_FILE = "geo_papers_with_chinese.csv"   # 如果文件名不同，请修改

# 中文字体设置（请确保字体文件存在）
# 使用系统黑体（最稳定）
plt.rcParams['font.sans-serif'] = ['SimHei']      # Windows 黑体
plt.rcParams['axes.unicode_minus'] = False
FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"        # 词云字体路径（如无 simhei.ttf，请更换）

# 输出文件
KEYWORD_STATS_CSV = "keyword_stats.csv"
KEYWORD_TABLE_IMG = "keyword_table.png"
WORDCLOUD_IMG = "wordcloud_cn.png"
GRAPHML_FILE = "cooccurrence_network_cn.graphml"
NETWORK_IMG = "cooccurrence_network_cn.png"
YEARLY_PLOT = "yearly_papers.png"
TREND_PLOT = "keyword_trends_cn.png"              # 可选

# 分析参数
MIN_KEYWORD_FREQ = 3          # 关键词最少出现次数（过滤低频词）
MIN_COOCCUR = 2                # 共现最少次数（过滤弱连接）
TOP_LABELS = 30                 # 网络图中显示标签的最大数量
TOP_TREND = 8                   # 趋势图中显示的热门关键词数量
# ====================================================================

# 1. 读取数据
print("正在读取数据...")
df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
print(f"共 {len(df)} 篇论文")

# 将中文关键词字符串转换为列表
df['keyword_list'] = df['keywords_cn'].apply(
    lambda x: [k.strip() for k in str(x).split(';') if k.strip()]
)

# 2. 关键词频率统计
all_keywords = []
for klist in df['keyword_list']:
    all_keywords.extend(klist)
keyword_freq = Counter(all_keywords)
print(f"原始关键词总数: {len(keyword_freq)}")

# 保存完整统计表
stats_df = pd.DataFrame(keyword_freq.items(), columns=['关键词', '出现次数'])
stats_df = stats_df.sort_values('出现次数', ascending=False).reset_index(drop=True)
total = stats_df['出现次数'].sum()
stats_df['占比(%)'] = (stats_df['出现次数'] / total * 100).round(2)
stats_df['累计占比(%)'] = stats_df['占比(%)'].cumsum().round(2)
stats_df.insert(0, '序号', range(1, len(stats_df)+1))
stats_df.to_csv(KEYWORD_STATS_CSV, index=False, encoding='utf-8-sig')
print(f"关键词统计表已保存至 {KEYWORD_STATS_CSV}")

# 3. 生成关键词表格图片（前30个）
def draw_keyword_table(df, top_n=30, output_file=KEYWORD_TABLE_IMG):
    table_data = df.head(top_n).values
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('off')
    tb = plt.table(cellText=table_data, colLabels=df.columns, 
                   cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    tb.auto_set_font_size(False)
    tb.set_fontsize(10)
    for (i, j), cell in tb.get_celld().items():
        if i == 0:
            cell.set_facecolor('lightgray')
    plt.title("地理信息科学关键词频率统计（前30）", fontsize=16, y=1.05)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"关键词表格图片已保存至 {output_file}")

draw_keyword_table(stats_df)

# 4. 生成词云
def plot_wordcloud(keywords, output_file):
    counter = Counter(keywords)
    wordcloud = WordCloud(
        width=1200, height=800,
        background_color='white',
        max_words=100,
        font_path=FONT_PATH,          # 关键：使用中文字体
        colormap='viridis'
    ).generate_from_frequencies(counter)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title("地理信息科学研究关键词词云（中文）", fontsize=16)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"词云已保存至 {output_file}")

plot_wordcloud(all_keywords, WORDCLOUD_IMG)

# 5. 构建共现网络
print("构建共现网络...")
# 过滤低频关键词
valid_keywords = {k for k, v in keyword_freq.items() if v >= MIN_KEYWORD_FREQ}
print(f"保留出现 ≥{MIN_KEYWORD_FREQ} 次的关键词: {len(valid_keywords)} 个")

# 构建共现矩阵
cooccur = defaultdict(lambda: defaultdict(int))
paper_count = 0
for klist in df['keyword_list']:
    klist = [k for k in klist if k in valid_keywords]
    if len(klist) < 2:
        continue
    paper_count += 1
    for i in range(len(klist)):
        for j in range(i+1, len(klist)):
            a, b = sorted([klist[i], klist[j]])
            cooccur[a][b] += 1
print(f"有效论文数量（含至少2个有效关键词）: {paper_count}")

# 创建图
G = nx.Graph()
for kw in valid_keywords:
    G.add_node(kw, weight=keyword_freq[kw])
for a, neighbors in cooccur.items():
    for b, w in neighbors.items():
        if w >= MIN_COOCCUR:
            G.add_edge(a, b, weight=w)
print(f"网络包含 {G.number_of_nodes()} 个节点，{G.number_of_edges()} 条边")

if G.number_of_nodes() == 0:
    print("网络为空，请降低 MIN_KEYWORD_FREQ 或 MIN_COOCCUR 再试。")
else:
    # 社区检测
    partition = community_louvain.best_partition(G, weight='weight')
    nx.set_node_attributes(G, partition, 'community')

    # 布局
    pos = nx.kamada_kawai_layout(G, weight='weight')

    # 绘制网络图
    plt.figure(figsize=(20, 16))
    node_sizes = [G.nodes[node]['weight'] * 15 for node in G.nodes]
    communities = set(partition.values())
    colors = plt.cm.tab20(range(len(communities)))
    node_colors = [colors[partition[node] % len(colors)] for node in G.nodes]
    
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)
    edge_weights = [G[u][v]['weight'] for u, v in G.edges]
    nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.3, edge_color='gray')
    
    # 只显示前 TOP_LABELS 个高频词的标签
    top_keywords = [kw for kw, _ in keyword_freq.most_common(TOP_LABELS) if kw in G.nodes]
    labels = {kw: kw for kw in top_keywords}
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_family='sans-serif')
    
    plt.title("地理信息科学关键词共现网络（中文）", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(NETWORK_IMG, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"网络图已保存至 {NETWORK_IMG}")

    # 保存GraphML（用于Gephi）
    nx.write_graphml(G, GRAPHML_FILE)
    print(f"网络数据已保存至 {GRAPHML_FILE}")

# 6. 年份分析
def plot_yearly_papers(papers_df, output_file):
    years = papers_df['year'].dropna().astype(int)
    if years.empty:
        print("无年份数据，跳过")
        return
    year_counts = years.value_counts().sort_index()
    plt.figure(figsize=(12, 6))
    plt.bar(year_counts.index.astype(str), year_counts.values, color='steelblue')
    plt.xlabel("年份")
    plt.ylabel("论文数量")
    plt.title("地理信息科学领域论文年发表量趋势", fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"年份柱状图已保存至 {output_file}")

plot_yearly_papers(df, YEARLY_PLOT)

# 7. 关键词趋势图（可选）
def plot_keyword_trends(papers_df, top_n=TOP_TREND, output_file=TREND_PLOT):
    # 收集每个关键词出现的年份
    kw_year = defaultdict(list)
    for _, row in papers_df.iterrows():
        year = row['year']
        if pd.isna(year):
            continue
        for kw in row['keyword_list']:
            kw_year[kw].append(int(year))
    
    if not kw_year:
        print("无足够数据绘制趋势图")
        return
    
    # 获取所有年份范围
    all_years = sorted(set(y for yrs in kw_year.values() for y in yrs))
    # 计算每个关键词每年的出现次数
    trends = {}
    for kw, years in kw_year.items():
        if len(years) < 3:
            continue
        year_counts = Counter(years)
        series = [year_counts.get(y, 0) for y in all_years]
        trends[kw] = series
    
    # 取总出现次数最多的 top_n
    sorted_kws = sorted(trends.items(), key=lambda x: sum(x[1]), reverse=True)[:top_n]
    
    if not sorted_kws:
        print("没有足够的关键词数据绘制趋势图")
        return
    
    plt.figure(figsize=(14, 8))
    for kw, series in sorted_kws:
        plt.plot(all_years, series, marker='o', label=kw)
    
    plt.xlabel("年份")
    plt.ylabel("出现次数")
    plt.title("热门关键词随时间变化趋势（中文）", fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"关键词趋势图已保存至 {output_file}")

plot_keyword_trends(df)

print("\n所有可视化已完成！")