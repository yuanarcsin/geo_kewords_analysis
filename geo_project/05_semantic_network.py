#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于已采集数据生成学术语义网络图
输入：geo_papers.csv
输出：专业关键词共现网络图（静态PNG + 交互式HTML）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter, defaultdict
import community.community_louvain as community_louvain  # 社区检测
import warnings
warnings.filterwarnings("ignore")

# ==================== 配置 ====================
INPUT_CSV = "geo_papers.csv"           # 你已生成的文件
MIN_KEYWORD_FREQ = 3                    # 关键词最少出现次数（过滤低频词）
MIN_COOCCUR = 2                         # 共现最少次数（过滤弱连接）
TOP_LABELS = 30                         # 最多显示多少个关键词标签
FIGURE_SIZE = (20, 16)                  # 图像尺寸
OUTPUT_PNG = "semantic_network.png"
OUTPUT_HTML = "semantic_network.html"   # 交互式版本（需要pyvis）

# 中文字体设置（根据你的系统调整）
plt.rcParams['font.sans-serif'] = ['SimHei']  # 或 'Microsoft YaHei'
plt.rcParams['axes.unicode_minus'] = False

# ==================== 读取数据 ====================
print("正在读取数据...")
df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
print(f"共 {len(df)} 篇论文")

# 将关键词字符串转换为列表
df['keyword_list'] = df['keywords'].apply(lambda x: [k.strip() for k in str(x).split(';') if k.strip()])

# 提取所有关键词并统计频率
all_keywords = []
for klist in df['keyword_list']:
    all_keywords.extend(klist)
keyword_freq = Counter(all_keywords)
print(f"原始关键词总数: {len(keyword_freq)}")

# 过滤低频关键词
valid_keywords = {k for k, v in keyword_freq.items() if v >= MIN_KEYWORD_FREQ}
print(f"保留出现 ≥{MIN_KEYWORD_FREQ} 次的关键词: {len(valid_keywords)} 个")

# ==================== 构建共现矩阵 ====================
cooccur = defaultdict(lambda: defaultdict(int))
paper_count = 0
for klist in df['keyword_list']:
    # 仅保留有效关键词
    klist = [k for k in klist if k in valid_keywords]
    if len(klist) < 2:
        continue
    paper_count += 1
    for i in range(len(klist)):
        for j in range(i+1, len(klist)):
            a, b = sorted([klist[i], klist[j]])
            cooccur[a][b] += 1

print(f"有效论文数量（含至少2个有效关键词）: {paper_count}")

# ==================== 构建网络图 ====================
G = nx.Graph()

# 添加节点（关键词）
for kw in valid_keywords:
    G.add_node(kw, weight=keyword_freq[kw])

# 添加边（共现）
for a, neighbors in cooccur.items():
    for b, w in neighbors.items():
        if w >= MIN_COOCCUR:
            G.add_edge(a, b, weight=w)

print(f"网络包含 {G.number_of_nodes()} 个节点，{G.number_of_edges()} 条边")

if G.number_of_nodes() == 0:
    print("网络为空，请降低 MIN_KEYWORD_FREQ 或 MIN_COOCCUR 再试。")
    exit()

# ==================== 社区检测（聚类） ====================
# 使用 Louvain 算法划分社区
partition = community_louvain.best_partition(G, weight='weight')
# 为每个节点添加社区属性
nx.set_node_attributes(G, partition, 'community')

# ==================== 计算布局 ====================
# 使用 Kamada-Kawai 布局（通常比 spring 更美观，尤其适合中规模网络）
pos = nx.kamada_kawai_layout(G, weight='weight')

# ==================== 绘制静态图 ====================
plt.figure(figsize=FIGURE_SIZE)

# 节点大小：与出现次数成正比（可调整缩放因子）
node_sizes = [G.nodes[node]['weight'] * 20 for node in G.nodes]

# 节点颜色：根据社区分配
communities = set(partition.values())
colors = plt.cm.tab20(range(len(communities)))  # 使用tab20色系
node_colors = [colors[partition[node] % len(colors)] for node in G.nodes]

# 绘制节点
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)

# 绘制边：宽度与共现次数成正比
edge_weights = [G[u][v]['weight'] for u, v in G.edges]
nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.3, edge_color='gray')

# 绘制标签：只显示出现次数最多的前 TOP_LABELS 个节点
top_keywords = [kw for kw, _ in keyword_freq.most_common(TOP_LABELS) if kw in G.nodes]
labels = {kw: kw for kw in top_keywords}
nx.draw_networkx_labels(G, pos, labels, font_size=10, font_family='sans-serif')

plt.title(f"地理信息科学关键词共现网络（数据来源：OpenAlex）\n"
          f"节点大小=关键词频次，颜色=研究主题聚类，边粗=共现强度",
          fontsize=16)
plt.axis('off')
plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
plt.show()
print(f"静态网络图已保存至 {OUTPUT_PNG}")

# ==================== 可选：生成交互式HTML ====================
try:
    from pyvis.network import Network
    net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")
    # 添加节点和边
    for node, data in G.nodes(data=True):
        net.add_node(node, label=node, size=data['weight'], title=f"出现次数: {data['weight']}")
    for u, v, data in G.edges(data=True):
        net.add_edge(u, v, value=data['weight'], title=f"共现次数: {data['weight']}")
    # 设置物理布局
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 95,
          "springConstant": 0.04
        }
      }
    }
    """)
    net.save_graph(OUTPUT_HTML)
    print(f"交互式网络图已保存至 {OUTPUT_HTML}，可用浏览器打开。")
except ImportError:
    print("未安装pyvis，跳过交互式HTML生成。")