from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance
import numpy as np
from qdrant_client.models import PointStruct
from qdrant_client.models import Filter, FieldCondition, Range, PayloadSchemaType
from httpx import WriteTimeout
import numpy as np
import uuid
from typing import List, Dict
import time

class QdrantService:
   def __init__(self, url,api_key):
      self.client = QdrantClient(url=url, api_key = api_key,timeout=120)
      
   def insert(self, collection: str, data: List[Dict], emb_data: np.ndarray, batch_size: int = 100, retries: int = 3):

      if not self.client.collection_exists(collection):
         self.client.create_collection(
               collection_name=collection,
               vectors_config=VectorParams(size=emb_data.shape[1], distance=Distance.COSINE)
         )

      for i in range(0, len(data), batch_size):
         batch_data = data[i:i+batch_size]
         batch_emb = emb_data[i:i+batch_size]

         points = [
               PointStruct(
                  id=str(uuid.uuid4()),
                  vector=batch_emb[idx].tolist(),
                  payload=batch_data[idx]
               )
               for idx in range(len(batch_data))
         ]

         for attempt in range(retries):
               try:
                  self.client.upsert(
                     collection_name=collection,
                     points=points
                  )
                  break
               except WriteTimeout:
                  if attempt < retries - 1:
                     print(f"Timeout, thử lại batch {i//batch_size+1} (attempt {attempt+1})...")
                     time.sleep(2)
                  else:
                     raise

   
   def search(self, collection:str, Ids:List[Dict],query_vector: np.ndarray, limit:int) -> List[Dict]:
      productIds = [Id.get('productId') for Id in Ids]
      spIds = [Id.get('spId') for Id in Ids]
      sellerIds = [Id.get('sellerId') for Id in Ids]
      
      sim_vector = self.client.query_points(
         collection_name = collection,
         query = query_vector,
         query_filter=models.Filter(
            must = [
               models.FieldCondition(
                  key = "productId",
                  match = models.MatchAny(any = productIds)
               ),
               models.FieldCondition(
                  key = "spId",
                  match = models.MatchAny(any = spIds)
               ),
               models.FieldCondition(
                  key = "sellerId",
                  match = models.MatchAny(any = sellerIds)
               )
            ]
            ),
         limit = limit,
      ).points
      response_vector = [vector.payload for vector in sim_vector]
      return response_vector
   

