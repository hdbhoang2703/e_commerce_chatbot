from model.embedding_model import EmbeddingModel
from model.generate_model import GenerateModel
from model.rerank_model import RerankModel

from database.MongoDB import MongoService
from database.Qdrant import QdrantService

from services.get_data import get_info, get_comments
from services.convert_data import dict_to_str

from core.conversation_manager import ConversationManager

from typing import List,Dict,Tuple
import asyncio


class RAG:
    def __init__(self, embedding_model, rerank_model, generate_model, mongo_service, qdrant_service,conversation_manager):
        self.embedding_model = embedding_model
        self.rerank_model = rerank_model
        self.generate_model = generate_model
        self.mongo_service = mongo_service
        self.qdrant_service = qdrant_service
        self.conversation_manager = conversation_manager

    async def pre_data(self, link_product):
        
        raw_info = get_info(link_product=link_product)

        productId = raw_info.get('productId',"")
        spId = raw_info.get('spId',"")
        sellerId = raw_info.get('sellerId',"")
        
        if self.mongo_service.exists_product(productId = productId, spId=spId,sellerId=sellerId) == False:
            raw_comments= await get_comments(link_product=link_product)
            self.mongo_service.insert_info(info_data=raw_info)
            self.mongo_service.insert_comments(comments_data=raw_comments)
            
            comments = self.mongo_service.get_comments(productId = productId,
                                                    spId = spId,
                                                    sellerId = sellerId)
            
            comments_str = dict_to_str(comments)
            emb_comments = self.embedding_model.encode(comments_str)
            
            self.qdrant_service.insert(collection = "comments",data = comments, emb_data = emb_comments)
    
    def retrieve(self,collection:str,query:str, Ids:List[Dict],top_k_search:int=30, top_k_rerank:int=10)->List[Tuple[str,float]]:
        emb_query = self.embedding_model.encode([query])
        response_search = self.qdrant_service.search(collection = collection,
                                          Ids = Ids,
                                          query_vector = emb_query[0],
                                          limit = top_k_search
                                          )
        Id = Ids[0]
        info_product = self.mongo_service.get_info(productId = Id['productId'],
                                                    spId = Id['spId'],
                                                    sellerId = Id['sellerId']) 
        
        response_search_str = dict_to_str(response_search)
        info_product_str = dict_to_str(info_product)
        response_search_str.extend(info_product_str)
        
        response_rerank = self.rerank_model.rerank(query = query,
                                                   contexts = response_search_str,
                                                   top_k = top_k_rerank
                                                   )
        print(response_rerank)
        
        return response_rerank
    
    def build_context(self,hits:List[Tuple[str,float]])->str:
        return "\n".join(f"score:{hit[1]},{hit[0]}" for hit in hits)
        
    def generate_answer(self, session_id:str, query:str, context:str)->str:
        prompt = f"""Thông tin cung cấp:
                    {context}"""

        self.conversation_manager.add_message(session_id = session_id, role="system",content = prompt)
        self.conversation_manager.add_message(session_id = session_id, role="user",content = query)
        messages= self.conversation_manager.get_messages(session_id = session_id)
        print(messages)
        answer = self.generate_model.generate(prompt = messages)
        
        self.conversation_manager.add_message(session_id = session_id, role="assistant",content=answer)
        return answer
    
    def answer(self, session_id:str, query:str, Ids:List[Dict], collection:str)->str:
        hits = self.retrieve(collection=collection,
                query=query,
                Ids = Ids,
                )
        print(hits)
        context = self.build_context(hits = hits)
        response = self.generate_answer(session_id=session_id, query=query, context=context)
        
        return response
        
def main():
    api_key="s1OcFjuIJzI7DfJKiixyL3nCYsq04Z4W"
    uri = "mongodb+srv://baohoang2734:Cm72HgFgT5iI7IRR@data-tiki.d8njkdk.mongodb.net/?retryWrites=true&w=majority&appName=data-tiki"
    
    embedding_model = EmbeddingModel(api_key=api_key)
    rerank_model = RerankModel(api_key=api_key)
    generate_model = GenerateModel(api_key=api_key,model="Qwen/Qwen2.5-7B-Instruct")
    
    mongo_service = MongoService(uri = uri)
    qdrant_service = QdrantService(
        url = "https://0acf1ecd-b3ba-499a-8aae-04235fea580f.eu-central-1-0.aws.cloud.qdrant.io:6333",
        api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.R8_oydWeF41emvkY2aUR1kUhT3MqMf_0rd_HOZlV7No"
        )
    
    system_prompt="""
        Bạn là nhân viên hỗ trợ khách hàng tìm hiểu thông tin về sản phẩm dựa trên các đánh giá từ khách hàng trước đây.
        Bạn không bán hàng, không sản xuất và không liên quan đến nhà bán hàng.
        Chỉ sử dụng thông tin được cung cấp để trả lời.
        Nếu không đủ dữ liệu để trả lời hoặc câu hỏi không liên quan đến sản phẩm, hãy trả lời không biết.
        Không đề xuất hành động, không hỏi ngược lại, không đưa thông tin ngoài dữ liệu đã cho.
        Không suy đoán, không đưa lời khuyên hay đề xuất ngoài dữ liệu.
        Luôn trả lời rõ ràng, mạch lạc như đang trò chuyện trực tiếp với khách hàng.
        """

    conversation_manager = ConversationManager(system_prompt=system_prompt)
    
    rag = RAG(embedding_model=embedding_model,
              rerank_model=rerank_model,
              generate_model=generate_model,
              mongo_service=mongo_service,
              qdrant_service=qdrant_service,
              conversation_manager=conversation_manager)
    
    Ids = [{
        'productId':119706880,
        'spId':"119706881",
        'sellerId':215908
    }]
    
    query = "sản phẩm có xuất xứ từ đâu"

    session_id = "1111"

    answer = rag.answer(session_id =session_id ,query=query,Ids=Ids,collection="comments")
    
    print(answer)
    
    
    # link_product = "https://tiki.vn/chuot-game-co-day-logitech-g203-lightsync-tuy-chinh-rgb-6-nut-lap-trinh-nhe-8000-dpi-pc-mac-hang-chinh-hang-p174599595.html?spid=187960118"

    # asyncio.run(rag.pre_data(link_product=link_product))

if __name__ =="__main__":
    main()  