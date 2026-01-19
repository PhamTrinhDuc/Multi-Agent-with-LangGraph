from pydantic import BaseModel, Field
from typing import Literal, Dict, Any


class RouterDecision(BaseModel): 
  question: str = Field(description="Câu hỏi gốc từ user hoặc đã được rewrite lại dựa vào lịch sử. Viết rõ ràng, chi tiết lại tên sản phẩm")
  next_action: Literal["search", "order", "compare"] = \
      Field(description="""
            Bước tiếp theo cần được thực hiện. 
            `search`: khi câu hỏi cần hỏi, tìm kiếm thông tin sản phẩm
            `order`: Khi user muốn đặt hàng, chốt đơn
            `compare`: Khi user muốn so sánh sản phẩm với sản phẩm bên thứ 3 hoặc so sánh các sản phẩm với nhau
            """)
  reason: str = Field(description="Lí do chọn bước tiếp theo")

class ValidateContextOutput(BaseModel): 
  context_valid: str = Field(description="True nếu context phù hợp để trả lời câu hỏi cho user, False nếu không phù hợp")

class ComparisonResult(BaseModel):
  """Kết quả so sánh sản phẩm"""
  comparison_table: str = Field(description="Bảng so sánh chi tiết")
  recommendation: str = Field(description="Gợi ý nên chọn sản phẩm nào và tại sao")