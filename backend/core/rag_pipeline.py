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
        
