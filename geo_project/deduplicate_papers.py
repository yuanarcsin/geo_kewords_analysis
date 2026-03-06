#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对 geo_papers.csv 进行去重，基于 DOI 和标题
生成去重后的文件 geo_papers_deduplicated.csv
"""

import pandas as pd

# 读取原始数据
df = pd.read_csv("geo_papers.csv", encoding='utf-8-sig')
print(f"原始数据行数: {len(df)}")

# 统计重复情况
duplicate_dois = df[df.duplicated('doi', keep=False)]
print(f"基于DOI的重复行数: {len(duplicate_dois)}")

# 去重：优先保留第一个出现的记录（keep='first'）
# 如果 DOI 为空，则基于标题去重（避免丢失无 DOI 的论文）
# 先处理有 DOI 的，再处理无 DOI 的

# 1. 基于 DOI 去重（保留第一个）
df_dedup = df.drop_duplicates(subset='doi', keep='first')

# 2. 对于 DOI 为空的记录，再基于标题去重
mask_no_doi = df_dedup['doi'].isna() | (df_dedup['doi'] == '')
if mask_no_doi.any():
    # 将无 DOI 的部分单独取出，基于标题去重
    no_doi_part = df_dedup[mask_no_doi].drop_duplicates(subset='title', keep='first')
    # 将有 DOI 的部分与去重后的无 DOI 部分合并
    with_doi_part = df_dedup[~mask_no_doi]
    df_final = pd.concat([with_doi_part, no_doi_part], ignore_index=True)
else:
    df_final = df_dedup

print(f"去重后数据行数: {len(df_final)}")

# 保存去重后的文件
df_final.to_csv("geo_papers_deduplicated.csv", index=False, encoding='utf-8-sig')
print("去重后的文件已保存为 geo_papers_deduplicated.csv")
