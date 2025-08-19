from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.get_data import get_info, get_comments
from services.convert_data import dict_to_str

from model.embedding_model import EmbeddingModel
from model.generate_model import GenerateModel
from model.rerank_model import RerankModel

from database.MongoDB import MongoService
from database.Qdrant import QdrantService

from core.rag_pipeline import RAG
from core.conversation_manager import ConversationManager
 
from services.check_link import is_tiki_url, is_product_tiki_url

from typing import List,Dict
import uuid

from config import Config

import time

# set up config models, database   

embedding_model = EmbeddingModel(api_key=Config.MODEL_API_KEY,model="Qwen/Qwen3-Embedding-0.6B")
rerank_model = RerankModel(api_key=Config.MODEL_API_KEY,model_url="https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B")
generate_model = GenerateModel(api_key=Config.MODEL_API_KEY,model="Qwen/Qwen3-32B")

mongo_service = MongoService(uri = Config.MONGODB_URI)

qdrant_service = QdrantService(url = Config.QDRANT_URL,api_key = Config.QDRANT_API_KEY)

system_prompt="""
        Bạn là nhân viên hỗ trợ khách hàng tìm hiểu thông tin về sản phẩm dựa trên các đánh giá từ khách hàng trước đây.

        ## Vai trò và giới hạn:
        - Bạn KHÔNG bán hàng, KHÔNG sản xuất và KHÔNG liên quan đến nhà bán hàng
        - CHỈ sử dụng thông tin được cung cấp trong dữ liệu được cung cấp để trả lời
        - KHÔNG suy đoán, KHÔNG đưa lời khuyên hay đề xuất ngoài dữ liệu có sẵn
        - KHÔNG đề xuất hành động mua bán hay so sánh với sản phẩm khác

        ## Khi nào trả lời không biết:
        - Không đủ dữ liệu để trả lời chính xác
        - Câu hỏi không liên quan đến sản phẩm trong dữ liệu
        - Yêu cầu thông tin không có trong dữ liệu được cung cấp

        ## Cách trả lời:
        - Trò chuyện tự nhiên, thân thiện như đang nói chuyện trực tiếp
        - Trả lời rõ ràng, mạch lạc dựa trên đánh giá thực tế
        - Trích dẫn thông tin từ đánh giá khi có thể
        - Không hỏi ngược lại, không yêu cầu thêm thông tin

        ## Format bắt buộc:
        - Luôn trả lời đúng chuẩn JSON, không thêm bất kỳ ký tự, chú thích, văn bản nào ngoài JSON.
        - JSON phải có đúng 2 trường: "content" (string), "images" (array of string).
        - Trong trường "content" không được có link ảnh
        - Nếu không có hình ảnh thì "images": [].
        - Chỉ đưa ảnh khi khách hàng có yêu cầu ảnh.
    """

conversation_manager = ConversationManager(system_prompt=system_prompt)

rag = RAG(embedding_model=embedding_model,
            rerank_model=rerank_model,
            generate_model=generate_model,
            mongo_service=mongo_service,
            qdrant_service=qdrant_service,
            conversation_manager=conversation_manager)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    product_id:Dict
    message: str

class LinkInput(BaseModel):
    link : str


@app.post("/create_chat")
async def create_chat(req: LinkInput):
    try:
        link_input = req.link
        if is_tiki_url(link=link_input)==False:
            raise HTTPException(status_code=400,detail=f"Không phải link tiki")
        if is_product_tiki_url(link=link_input)==False:
            raise HTTPException(status_code=400,detail="Link tiki không chứa sản phẩm")
        
        info = get_info(link_product=link_input)
        
        await rag.pre_data(link_product=link_input)

        Id = {
            "productId": info.get('productId'),
            "spId": info.get('spId'),
            "sellerId": info.get('sellerId')
        }
        name_product = info.get('name')
        img_product = info.get('images') or []
        session_id = str(uuid.uuid4())

        len_image = min((len(img_product)//2)*2, 4)
        img_product = img_product[:len_image]

        return {
            "Id": Id,
            "session_id": session_id,
            "name_product": name_product,
            "img_product": img_product
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        user_message = req.message
        session_id = req.session_id
        Id_product = req.product_id
        
        bot_response = rag.answer(session_id=session_id,
                                query=user_message,   
                                Ids = [Id_product],
                                collection="comments")
        return {"response":bot_response}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@app.post("/end_chat/{session_id}")
async def end_chat(session_id: str):
    try:
        conversation_manager.clear_session(session_id)
        return {"status": "session_cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa session: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}





