import os
from dotenv import load_dotenv
from serpapi import SerpApiClient

load_dotenv()

def search(query: str) -> str:
    """
    一个基于SerpApi的网页搜索引擎工具
    它会智能的解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise ValueError("错误：SERPAPI_API_KEY 未在 .env 文件中定义。")
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",
            "hl": "zh-CN"
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析：优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
        return f"抱歉，没有找到'{query}'相关的搜索结果。"
    
    except Exception as e:
        return f"错误：执行SerpApi搜索时出现问题 - {e}"
