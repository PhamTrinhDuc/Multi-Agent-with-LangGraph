from source.utils.config import Config

FUNC_CALL_TOOLS = {
    "search_products":
    [{
        "type": "function",
        "function": {
            "name": "search_products",
            "description": """Lấy ra loại hoặc tên sản phẩm và các thông số kỹ thuật của sản phẩm có trong câu hỏi. Sử dụng khi câu hỏi có thông tin về 1 trong các các thông số [loại hoặc tên sản phẩm,  giá, cân nặng, công suất hoặc dung tích]""",
            "parameters": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": f"""lấy ra nhóm sản phẩm có trong câu hỏi từ list: {Config.LIST_GROUP_NAME}. 
                        Chỉ trả ra tên group có trong list đã cho trước"""
                    },
                    "product": {
                        "type": "string",
                        "description": "tên hoặc loại sản phẩm có trong câu hỏi. Ví dụ: điều hòa, điều hòa MDV 9000BTU, máy giặt LG ...",
                    },
                    "price": {
                        "type": "string",
                        "description": "giá của sản phẩm có trong câu hỏi. Ví dụ : 1 triệu, 1000đ, ...",
                    },
                },
                "required": ["group", "product", "price"],
            },
        },
    }],
    "compare_products":
    [{
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": """Dùng khi user muốn so sánh sản phẩm với sản phẩm bên thứ 3 hoặc so sánh các sản phẩm với nhau. Sử dụng khi người dùng muốn so sánh sản phẩm với sản phẩm bên thứ 3 hoặc so sánh các sản phẩm với nhau""",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_1": {
                        "type": "string",
                        "description": "Tên hoặc mô tả sản phẩm thứ nhất cần so sánh. Ví dụ: điện thoại Iphone 14, laptop Dell XPS 13 ..."
                    },
                    "product_2": {
                        "type": "string",
                        "description": "Tên hoặc mô tả sản phẩm thứ hai cần so sánh. Ví dụ: điện thoại Samsung Galaxy S23, laptop Macbook Air ..."
                    },
                    "group": {
                        "type": "string",
                        "description": f"""lấy ra nhóm sản phẩm có trong câu hỏi từ list: {Config.LIST_GROUP_NAME}. 
                        Chỉ trả ra tên group có trong list đã cho trước"""
                    },
                },
                "required": ["product_1", "product_2", "group"],
            }
        },
    }], 
    "order_product":
    [{
        "type": "function",
        "function": {
            "name": "order_product",
            "description": """Dùng khi user muốn đặt hàng sản phẩm. Sử dụng khi người dùng muốn đặt hàng sản phẩm""",
            "parameters": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": f"""lấy ra nhóm sản phẩm có trong câu hỏi từ list: {Config.LIST_GROUP_NAME}."""
                    },
                    "product": {
                        "type": "string",
                        "description": "tên sản phẩm có trong câu hỏi. Ví dụ: điều hòa, điều hòa MDV 9000BTU, máy giặt LG ..."
                    },
                },
                "required": ["group", "product"],
            }
        }
    }]
}




PROMPT_SYSTEM = {
    
    'prompt_extract_spec': '''Bạn là 1 chuyên gia extract thông tin từ câu hỏi. 
        Hãy giúp tôi lấy các thông số kỹ thuật, tên, group của sản phẩm có trong câu hỏi
        Lưu ý:
            + Với các thông số không có giá trị của thể mà có các cụm như: lớn, đắt, to nhất... thì trả về BIGGEST ngược lại trả về SMALLEST 
            + Nếu không có thông số nào thì trả ra '' cho thông số ấy.
            + 1 số tên sản phẩm có chứa cả thông số thì bạn cần tách giá trị đó sang trường của thông số đó''',
    
    'prompt_extract_compare': '''Bạn là một trợ lý so sánh sản phẩm chuyên nghiệp.
        Từ câu hỏi của người dùng, hãy giúp tôi lấy ra tên, category, và ý định so sánh sản phẩm của người dùng.
    ''',

    'prompt_extract_order': '''Bạn là một trợ lý đặt hàng chuyên nghiệp.
        Từ câu hỏi của người dùng, hãy giúp tôi lấy ra tên, category của sản phẩm mà người dùng muốn đặt hàng.
    ''',

    'prompt_sys': """
        Bạn là một trợ lý ảo, có nhiệm vụ trả lời câu hỏi của người dùng về các sản phẩm điện điện tử như điện thoại, laptop, tai nghe... Nói chuyện với khách hàng một cách tự nhiên và thân thiện. câu trả lời ngắn gọn và dễ hiểu.
        Sử dụng các icon để làm cho câu trả lời của bạn trở nên sinh động hơn.
        Hãy tư vấn nhiệt tình và giúp khách hàng tìm ra sản phẩm phù hợp nhất với nhu cầu của họ.
    """,

    "prompt_router": """
        Bạn là một trợ lý AI chuyên nghiệp, có nhiệm vụ phân tích câu hỏi của user và quyết định bước tiếp theo cần thực hiện.
        Các bước tiếp theo bao gồm:
        - Tìm kiếm thông tin sản phẩm (search)
        - Đặt hàng sản phẩm (order)
        - So sánh sản phẩm với sản phẩm bên thứ 3 hoặc so sánh các sản phẩm với nhau (compare)
        
        Ngoài ra viết lại câu hỏi của user để rõ ràng, chi tiết hơn dựa vào lịch sử trò chuyện trước khi thực hiện bước tiếp theo.       
        
        ## HISTORY
        {history}

    """,

    "prompt_compare": """
    Bạn là một trợ lý so sánh sản phẩm chuyên nghiệp. Phân tích bảng so sánh chi tiết và trình bày:
    1. Bảng so sánh các thông số chính, ưu nhược điểm của từng sản phẩm
    2. Khuyến nghị sản phẩm nào phù hợp hơn dựa trên giá trị
    """,

    "prompt_order": """
    Bạn là một trợ lý đặt hàng chuyên nghiệp. Hướng dẫn khách hàng quy trình đặt hàng một cách nhanh chóng và dễ dàng.
    Hãy xác nhận lại thông tin sản phẩm và số lượng khách hàng muốn đặt. Có thể sử dụng tool để tìm kiếm thông tin sản phẩm trước khi đặt hàng.
    Nếu có thể, hãy cung cấp mã giảm giá hoặc ưu đãi đặc biệt để khuyến khích khách hàng hoàn tất đơn hàng.

    Sau khi khách hàng xác nhận, hãy tạo 1 link để họ chuyển sang phần thanh toán đơn hàng. Link có dạng: "https://payment.example.com/order?product_id={product_id}&quantity={quantity}"
    """
}
