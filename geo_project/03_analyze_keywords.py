"""
第三步：关键词分析与可视化
目标：统计高频关键词，生成词云，发现研究趋势
"""
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import jieba  # 用于中文分词，如果关键词是英文可以不用

def analyze_keywords(csv_file):
    """
    分析关键词频率
    """
    # 读取数据
    df = pd.read_csv(csv_file)
    print(f"共加载 {len(df)} 篇论文")
    
    # 提取所有关键词
    all_keywords = []
    keywords_by_year = {}
    
    for _, row in df.iterrows():
        if pd.notna(row['keywords']):
            # 分割关键词
            keywords = [k.strip() for k in str(row['keywords']).split(';') if k.strip()]
            all_keywords.extend(keywords)
            
            # 按年份分组
            year = row['publication_year']
            if pd.notna(year):
                year = int(year)
                if year not in keywords_by_year:
                    keywords_by_year[year] = []
                keywords_by_year[year].extend(keywords)
    
    # 统计总频率
    counter = Counter(all_keywords)
    print("\n📊 关键词总频率 TOP 30：")
    for kw, count in counter.most_common(30):
        print(f"  {kw}: {count}")
    
    # 生成词云
    if all_keywords:
        # 将关键词列表转为字符串（空格分隔）
        text = ' '.join(all_keywords)
        
        wordcloud = WordCloud(
            width=1200,
            height=800,
            background_color='white',
            max_words=100,
            collocations=False,  # 避免重复词组
            font_path=None  # 如果有中文字体需要指定
        ).generate(text)
        
        # 显示词云
        plt.figure(figsize=(15, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('地理信息研究关键词词云', fontsize=16)
        plt.tight_layout()
        plt.savefig('keyword_wordcloud.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ 词云已保存为 keyword_wordcloud.png")
    
    # 按年份分析趋势
    if keywords_by_year:
        # 取近5年数据
        recent_years = sorted([y for y in keywords_by_year.keys() if y >= 2020])
        
        # 找出上升最快的10个关键词
        if len(recent_years) >= 2:
            # 这里简化处理，你可以做更复杂的趋势分析
            print("\n📈 2020-2025 年新兴关键词（示例）：")
            # 简单统计：在最近两年出现频率显著增加的词
            # 实际应用需要更严谨的计算
            pass
    
    return counter

def save_keywords_report(counter, output_file='keywords_report.txt'):
    """
    保存关键词统计报告
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("地理信息研究关键词统计报告\n")
        f.write("=" * 50 + "\n\n")
        f.write("关键词频率排名：\n")
        for kw, count in counter.most_common(100):
            f.write(f"{kw}: {count}\n")
    
    print(f"✅ 报告已保存为 {output_file}")

if __name__ == "__main__":
    # 分析上一步生成的文件
    counter = analyze_keywords("geo_papers_keywords.csv")
    
    # 保存报告
    save_keywords_report(counter)