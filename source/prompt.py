from source.config import AragProduct

PROMPT_TOOLS = {
    "order": """Hữu ích khi khách hàng thảo luận về việc mua bán, giá cả, chốt đơn... sản phẩm, 
                hoăc có thể có các cụm sau: [đặt hàng, chốt đơn, thanh toán, giao hàng, vận chuyển, 
                địa chỉ nhận hàng, thông tin đơn hàng]""", 

    "search_product": """Hữu ích khi cần tìm kiếm các thông tin như: 
                tên, số lượng, giá cả, đắt nhất, rẻ nhất, lớn nhất, nhỏ nhất, 
                công suất, dung tích, khối lượng, kích thước, trọng lượng, top sản phẩm bán chạy.""", 

    "general_info": """Hữu ích khi khách hàng muốn hỏi các thông tin như:
                + Câu hỏi về thông tin chung, giải thích, hướng dẫn sử dụng
                + Thắc mắc về chính sách bảo hành, đổi trả
                + Câu hỏi về tình trạng còn hàng hoặc hết hàng""",

    "search_web": """Hữu ích khi các câu hỏi của khách hàng vượt ngoài khả năng hiểu biết của LLM, 
                hoặc những câu hỏi mang tính real-time"""
}

FUNC_CALL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_specifications",
            "description": """Lấy ra loại hoặc tên sản phẩm và các thông số kỹ thuật của sản phẩm có trong câu hỏi. Sử dụng khi câu hỏi có thông tin về 1 trong các các thông số [loại hoặc tên sản phẩm,  giá, cân nặng, công suất hoặc dung tích]""",
            "parameters": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": f"""lấy ra nhóm sản phẩm có trong câu hỏi từ list: {AragProduct.LIST_GROUP_NAME}. 
                        Chỉ trả ra tên group có trong list đã cho trước"""
                    },
                    "object": {
                        "type": "string",
                        "description": "tên hoặc loại sản phẩm có trong câu hỏi. Ví dụ: điều hòa, điều hòa MDV 9000BTU, máy giặt LG ...",
                    },
                    "price": {
                        "type": "string",
                        "description": "giá của sản phẩm có trong câu hỏi. Ví dụ : 1 triệu, 1000đ, ...",
                    },
                    "power": {
                        "type": "string", 
                        "description": "công suất của sản phẩm có trong câu hỏi. Ví dụ : 5W, 9000BTU, ...",
                    },  
                    "weight": {
                        "type": "string", 
                        "description": "cân nặng của sản phẩm có trong câu hỏi. Ví dụ : 1 cân, 10kg, 20 gam, ..."
                    },
                    "volume": {
                        "type": "string", 
                        "description": "dung tích của sản phẩm có trong câu hỏi. Ví dụ : 1 lít, 3 mét khối ..."
                    },
                    "intent": {
                        "type": "string",
                        "description": "ý định của người dùng khi hỏi câu hỏi. Ví dụ: mua, tìm hiểu, so sánh, ..."
                    }
                },
                "required": ["group", "object", "price", "power", "weight", "volume", "intent"],
            },
        },
    }
]

PROMPT_SYSTEM = {
    "extract_query": '''Bạn là 1 chuyên gia extract thông tin từ câu hỏi. 
        Hãy giúp tôi lấy các thông số kỹ thuật, tên, group của sản phẩm có trong câu hỏi
        Lưu ý:
            + Với các thông số không có giá trị của thể mà có các cụm như: lớn, đắt, to nhất... thì trả về BIGGEST ngược lại trả về SMALLEST 
            + Nếu không có thông số nào thì trả ra '' cho thông số ấy.
            + 1 số tên sản phẩm có chứa cả thông số thì bạn cần tách giá trị đó sang trường của thông số đó'''
}