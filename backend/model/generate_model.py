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
         
def main():
    context = [
        {
            "Đánh giá": "Rất không hài lòng",
            "Tình trạng khách hàng": "Đã mua hàng",
            "Nội dung": "Sách sao bẩn quá shop ơi, bẩn lắm luôn ạ. Sách brand new hay secondhand vậy ạ? Buồn quá shop ạ"
        },
        {
            "Đánh giá": "Bình thường",
            "Tình trạng khách hàng": "Đã mua hàng",
            "Nội dung": "Sách đẹp, mới đọc vài trang đầu đã thấy câu văn lủng củng, sai chính tả 😡, kiểm duyệt sách quá tệ cho 1 tác phẩm xuất sắc"
        }
    ]
    query = "Sách in ấn có tốt không?"
    
    system_prompt = "Bạn là chatbot tiếng việt hỗ trợ khách hàng biết thêm thông tin về sản phẩm, bạn không hề liên quan gì đến sản phẩm(không bán, không sản xuất,.. bạn chỉ phân tích)"
    user_prompt = f"""
    Trả lời câu hỏi của khách hàng dựa trên các thông tin sau:
    {context}
    Hãy trả lời trực tiếp với khách hàng, trả lời như một cuộc trò chuyện. Đây là câu hỏi của khách hàng:
    {query}
    """
    
    prompt = [
        {"role":"system", "content":system_prompt},
        {"role":"user", "content":user_prompt},
    ]
    
    generate_model = GenerateModel(api_key="s1OcFjuIJzI7DfJKiixyL3nCYsq04Z4W")
    reply = generate_model.generate(prompt = prompt)
    print(reply)
    
if __name__=="__main__":
    main()
    