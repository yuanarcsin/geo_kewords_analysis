"""
第二步：获取地理信息相关论文及关键词
目标：搜索指定关键词的论文，提取标题、年份、关键词（concepts）
"""
import requests
import pandas as pd
import time
from typing import List, Dict

class OpenAlexGeoFetcher:
    """OpenAlex地理信息论文获取器"""
    
    def __init__(self, email: str = None):
        """
        初始化
        :param email: 3314502822@qq.com
        """
        self.base_url = "https://api.openalex.org"
        self.headers = {
            'User-Agent': f'GeoResearcher/1.0 ({email if email else "anonymous"})'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def search_works(self, 
                     keyword: str, 
                     max_results: int = 100,
                     year_from: int = None,
                     year_to: int = None) -> List[Dict]:
        """
        搜索论文作品
        :param keyword: 搜索关键词（如 "remote sensing"）
        :param max_results: 最大结果数
        :param year_from: 起始年份（可选）
        :param year_to: 结束年份（可选）
        :return: 论文列表
        """
        all_works = []
        page = 1
        per_page = 25  # OpenAlex每页默认25条
        
        print(f"正在搜索关键词 '{keyword}' 的地理信息论文...")
        
        while len(all_works) < max_results:
            # 构建查询参数
            params = {
                'search': keyword,
                'page': page,
                'per-page': per_page,
                'sort': 'publication_date:desc',  # 按出版日期倒序
            }
            
            # 添加年份过滤
            if year_from or year_to:
                date_filter = []
                if year_from:
                    date_filter.append(f"from_publication_date:{year_from}-01-01")
                if year_to:
                    date_filter.append(f"to_publication_date:{year_to}-12-31")
                params['filter'] = ','.join(date_filter)
            
            try:
                # 发送请求
                response = self.session.get(
                    f"{self.base_url}/works", 
                    params=params,
                    timeout=15
                )
                
                if response.status_code != 200:
                    print(f"请求失败，状态码: {response.status_code}")
                    break
                
                data = response.json()
                works = data.get('results', [])
                
                if not works:
                    print("没有更多结果")
                    break
                
                # 提取关键信息
                for work in works:
                    # 提取关键词（OpenAlex中的concepts）
                    concepts = work.get('concepts', [])
                    keywords = [c['display_name'] for c in concepts if c['score'] > 0.3]  # 只保留置信度>0.3的概念
                    
                    paper = {
                        'title': work.get('title', 'N/A'),
                        'publication_year': work.get('publication_year'),
                        'doi': work.get('doi', ''),
                        'keywords': '; '.join(keywords[:10]),  # 取前10个关键词
                        'keyword_count': len(keywords),
                        'url': work.get('id', ''),
                        'cited_by_count': work.get('cited_by_count', 0)
                    }
                    all_works.append(paper)
                    
                    if len(all_works) >= max_results:
                        break
                
                print(f"已获取第 {page} 页，共 {len(all_works)} 篇论文")
                
                # 礼貌性延迟，避免请求过快
                time.sleep(1)
                
                # 检查是否还有下一页
                if len(works) < per_page:
                    break
                    
                page += 1
                
            except Exception as e:
                print(f"请求出错: {e}")
                break
        
        return all_works
    
    def get_concepts_list(self, keyword: str = None, max_concepts: int = 50) -> List[Dict]:
        """
        获取OpenAlex的概念列表（即研究主题/关键词库）
        可用于了解地理信息领域有哪些官方定义的概念
        
        :param keyword: 过滤关键词（如 "geography"）
        :param max_concepts: 最大返回数
        :return: 概念列表
        """
        params = {
            'per-page': min(max_concepts, 50),
            'sort': 'works_count:desc'  # 按相关论文数量排序
        }
        
        if keyword:
            params['search'] = keyword
        
        try:
            response = self.session.get(
                f"{self.base_url}/concepts",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                concepts = []
                for concept in data.get('results', []):
                    concepts.append({
                        'name': concept['display_name'],
                        'works_count': concept.get('works_count', 0),
                        'description': concept.get('description', ''),
                        'level': concept.get('level', 0)  # level越低越通用
                    })
                return concepts
            else:
                print(f"获取概念列表失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"获取概念列表出错: {e}")
            return []


def main():
    """主函数"""
    print("=" * 60)
    print("地理信息学术论文关键词采集")
    print("=" * 60)
    
    # 初始化爬虫（建议填写你的邮箱，获得更好待遇）
    fetcher = OpenAlexGeoFetcher(email="your.name@example.com")
    
    # 第一步：查看地理信息相关的概念（可选）
    print("\n【可选】查看地理信息领域的热门研究概念...")
    geo_concepts = fetcher.get_concepts_list(keyword="geography", max_concepts=10)
    
    if geo_concepts:
        print("\n热门地理信息概念：")
        for i, c in enumerate(geo_concepts[:5], 1):
            print(f"  {i}. {c['name']} (相关论文数: {c['works_count']})")
    
    # 第二步：搜索具体关键词的论文
    print("\n" + "-" * 60)
    
    # 你可以修改这里的关键词
    search_keywords = [
        "remote sensing",
        "GIS",
        "spatial analysis",
        "urban planning",
        "climate change"
    ]
    
    all_papers = []
    
    for keyword in search_keywords:
        print(f"\n正在搜索: {keyword}")
        papers = fetcher.search_works(
            keyword=keyword,
            max_results=50,  # 每个关键词取50篇
            year_from=2020,  # 只取2020年以后的论文
            year_to=2025
        )
        
        print(f"  找到 {len(papers)} 篇论文")
        all_papers.extend(papers)
        
        # 每个关键词后稍作休息
        time.sleep(2)
    
    # 保存结果
    if all_papers:
        df = pd.DataFrame(all_papers)
        
        # 去除可能的重复（基于DOI）
        df = df.drop_duplicates(subset=['doi'], keep='first')
        
        # 保存为CSV
        output_file = "geo_papers_keywords.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 数据保存成功！")
        print(f"  总论文数: {len(df)}")
        print(f"  文件: {output_file}")
        
        # 显示关键词统计（简单版）
        print("\n关键词频率统计（前20）：")
        all_keywords = []
        for kw_str in df['keywords']:
            if pd.notna(kw_str):
                all_keywords.extend([k.strip() for k in kw_str.split(';') if k.strip()])
        
        from collections import Counter
        counter = Counter(all_keywords)
        for kw, count in counter.most_common(20):
            print(f"  {kw}: {count}")
    else:
        print("❌ 没有获取到任何论文")

if __name__ == "__main__":
    main()