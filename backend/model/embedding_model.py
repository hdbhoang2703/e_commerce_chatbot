from openai import OpenAI
from typing import List, Dict
import numpy as np

class EmbeddingModel:
    def __init__(self, api_key, model = "Qwen/Qwen3-Embedding-0.6B"):
        self.client = OpenAI(
            api_key = api_key,
            base_url = "https://api.deepinfra.com/v1/openai",
        )
        self.model = model
        self.texts = []
    
    def encode(self, texts: List[str], batch_size = 512) -> np.ndarray:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_text = tuple(texts[i:i + batch_size])
            text_embeddings = self.client.embeddings.create(
                model=self.model,
                input=batch_text,
                encoding_format="float"
                )
            embeddings = [item.embedding for item in text_embeddings.data]
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)
    
def main():
    
    api_key = "s1OcFjuIJzI7DfJKiixyL3nCYsq04Z4W"

    embedding_model = EmbeddingModel(api_key=api_key)
    
    texts = ['san pham:ca phe khong duong','san pham:ca phe co duong']

    emb_texts = embedding_model.encode(texts = texts)
    print(emb_texts)
    
if __name__ == "__main__":
    main()