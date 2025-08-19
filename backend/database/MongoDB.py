from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from services.get_data import get_comments, get_info
from typing import List, Dict


class MongoService:
    def __init__(self, uri):
        self.client = MongoClient(uri,server_api=ServerApi('1'))
        self.db = self.client['products']
        self.info = self.db['info'] 
        self.comments = self.db['comments']
        
    def exists_product(self, productId, spId, sellerId) -> bool:
        return self.info.find_one(
            {"productId": productId, "spId": spId, "sellerId": sellerId},
            {"_id": 1}
        ) is not None
    def insert_info(self,info_data):
        self.info.insert_one(info_data)
    
    def insert_comments(self, comments_data):
        self.comments.insert_many(comments_data)
        
    def get_info(self, productId, spId, sellerId) -> List[Dict]:
        """Get info by product ID, spId, sellerId"""
        info = list(self.info.find({"productId":productId,
                                    'spId':spId,
                                    'sellerId':sellerId
                                    },
                                   {"_id": 0}))
        return info
        
    def get_comments(self,productId, spId, sellerId) -> List[Dict]:
        """Get comments by product ID"""
        comments = list(self.comments.find({"productId":productId,
                                        'spId':spId,
                                        'sellerId':sellerId
                                        },
                                       {"_id": 0}))
        return comments
        


