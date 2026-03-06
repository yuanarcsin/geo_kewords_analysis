#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用百度翻译 API 进行翻译（稳定、免费）
"""

import pandas as pd
import time
import requests
import hashlib
import random
from tqdm import tqdm

# ====== 请填写你的百度翻译 API 信息 ======
appid = "20260306002567098"
secretKey = "Xl0YALG2kTc5QMEZEN29"
# ======================================

def baidu_translate(text, from_lang='en', to_lang='zh'):
    """调用百度翻译 API"""
    endpoint = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = random.randint(32768, 65536)
    sign = appid + text + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': appid,
        'salt': salt,
        'sign': sign
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=5)
        result = r.json()
        if 'trans_result' in result:
            return result['trans_result'][0]['dst']
        else:
            print(f"百度翻译错误: {result}")
            return f"[失败]{text}"
    except Exception as e:
        print(f"请求异常: {e}")
        return f"[失败]{text}"

# 读取数据
df = pd.read_csv("geo_papers.csv", encoding='utf-8-sig')
print(f"原始数据共 {len(df)} 行")

# 提取所有唯一关键词
all_keywords = set()
for kw_str in df['keywords'].dropna():
    for kw in kw_str.split(';'):
        kw = kw.strip()
        if kw:
            all_keywords.add(kw)
print(f"共发现 {len(all_keywords)} 个唯一英文关键词")

# 翻译（带重试和进度保存）
translations = {}
kw_list = list(all_keywords)
failed_list = []

print("开始翻译...")
for i, kw in enumerate(tqdm(kw_list, desc="翻译进度")):
    # 尝试翻译，最多重试3次
    for attempt in range(3):
        result = baidu_translate(kw)
        if not result.startswith("[失败]"):
            translations[kw] = result
            break
        time.sleep(2)  # 等待后重试
    else:
        # 三次都失败，记录
        translations[kw] = kw  # 保留原文
        failed_list.append(kw)
    
    # 每翻译5个暂停1秒，避免触发限流
    if (i+1) % 5 == 0:
        time.sleep(1)

# 保存结果
trans_df = pd.DataFrame(list(translations.items()), columns=['英文关键词', '中文关键词'])
trans_df.to_csv("keyword_translation.csv", index=False, encoding='utf-8-sig')
print("中英文对照表已保存至 keyword_translation.csv")

if failed_list:
    print(f"翻译失败的关键词（已保留原文）: {failed_list}")

# 在原数据中添加中文关键词列
def get_chinese_keywords(kw_str):
    if pd.isna(kw_str):
        return ""
    eng_kws = [k.strip() for k in kw_str.split(';') if k.strip()]
    chn_kws = [translations.get(k, k) for k in eng_kws]
    return "; ".join(chn_kws)

df['keywords_cn'] = df['keywords'].apply(get_chinese_keywords)
df.to_csv("geo_papers_with_chinese.csv", index=False, encoding='utf-8-sig')
print("带中文关键词的数据已保存至 geo_papers_with_chinese.csv")