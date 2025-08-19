from openai import OpenAI
from typing import Dict, List

class GenerateModel:
    def __init__(self, api_key, model= "Qwen/Qwen3-30B-A3B"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai",
        )
        self.model = model
         
    def generate(self, prompt:List[Dict]) -> str:
        response = self.client.chat.completions.create(
            model = self.model,
            messages = prompt,
            response_format={"type":"json_object"}
        )
        reply = response.choices[0].message.content
        return reply
         


    