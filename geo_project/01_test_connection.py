import requests

print("测试连接 OpenAlex API...")
url = "https://api.openalex.org/concepts"
params = {"search": "geography", "per-page": 1}
headers = {"User-Agent": "GeoResearcher/1.0 (3314502822@qq.com)"}

try:
    r = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"状态码: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"找到概念总数: {data['meta']['count']}")
        concept = data['results'][0]
        print(f"示例概念: {concept['display_name']}")
        print("连接成功！")   # 这里用中文代替 ✅
    else:
        print("请求失败，请检查网络或API地址")
        
except Exception as e:
    print(f"错误: {e}")