import requests
from typing import List, Tuple

class RerankModel:
    def __init__(self, api_key, model_url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B"):
        self.api_key = api_key
        self.model_url = model_url
        self.headers = {
            "Authorization": f"bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def rerank(self, query: str, contexts: List[str], top_k: int = None) -> List[Tuple[str,float]]:
        """Rerank lại các contexts theo mức độ phù hợp"""
        payload = {
            "queries":[query]*len(contexts),
            "documents":contexts
        }
        response = requests.post(self.model_url, headers=self.headers, json=payload)
        score = response.json()["scores"]
        ranked = sorted(zip(contexts,score),key = lambda x:x[1],reverse=True)
        
        if top_k is not None:
            return ranked[:top_k]
        return ranked

def main():
    reranker = RerankModel(api_key="s1OcFjuIJzI7DfJKiixyL3nCYsq04Z4W")

    query = "Tôi có thể đổi trả sản phẩm điện tử như thế nào?"
    contexts = [
        "Sản phẩm điện tử đã kích hoạt bảo hành không được đổi trả.",
        "Bạn có thể đổi trả sản phẩm trong vòng 7 ngày nếu còn nguyên tem.",
        "Chúng tôi hỗ trợ giao hàng toàn quốc.",
        "Chính sách đổi trả không áp dụng cho hàng đã sử dụng."
    ]

    # Rerank và in kết quả
    results = reranker.rerank(query, contexts, top_k=2)
    print(results)

if __name__ == "__main__":
    main()