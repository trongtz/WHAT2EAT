# File: services/ai_service.py
from sqlalchemy.orm import Session
import crud.restaurant as crud_restaurant

def generate_recommendation(query: str, db: Session) -> dict:
    """
    ===================================================================
    KHU VỰC DÀNH CHO AI ENGINEER 
    Nhiệm vụ: Phân tích 'query', gọi OpenAI/LangChain, truy vấn Database.
    ===================================================================
    
    Input:
    - query: Câu hỏi của người dùng (VD: "Tìm quán lẩu cay Quận 1")
    - db: Session kết nối CSDL (để query lấy nhà hàng)
    
    Output (BẮT BUỘC trả về dict chứa 2 key này):
    - message (str): Câu trả lời giao tiếp tự nhiên của AI
    - restaurants (List[Restaurant]): Danh sách object nhà hàng phù hợp
    """
    
    # -------------------------------------------------------------
    # TODO: VIẾT LOGIC LANGCHAIN / OPENAI TẠI ĐÂY
    # 1. Gắn OPENAI_API_KEY
    # 2. Phân tích intent (ý định) của user từ biến `query`
    # 3. Dùng db.query(Restaurant) để tìm quán phù hợp
    # -------------------------------------------------------------
    
    # DƯỚI ĐÂY LÀ DỮ LIỆU MẪU ĐỂ BACKEND TEST (Xóa đi khi tích hợp code thật)
    print(f"[AI Service] Đang phân tích câu hỏi: {query}")
    
    # Tạm thời lấy 3 nhà hàng đầu tiên làm kết quả
    mock_restaurants = crud_restaurant.get_restaurants(db, skip=0, limit=3)
    mock_message = f"Dạ, hệ thống AI đang được hoàn thiện. Tạm thời em gợi ý cho anh/chị các quán sau dựa trên từ khóa '{query}' nhé!"
    
    return {
        "message": mock_message,
        "restaurants": mock_restaurants
    }