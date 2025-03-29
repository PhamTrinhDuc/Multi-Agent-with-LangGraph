from source.config import AragProduct

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
            + 1 số tên sản phẩm có chứa cả thông số thì bạn cần tách giá trị đó sang trường của thông số đó''',

    'prompt_sys': """
        Bạn là một trợ lý ảo, có nhiệm vụ trả lời câu hỏi của người dùng về các sản phẩm điện máy gia dụng. Nói chuyện với khách hàng một cách tự nhiên và thân thiện.
        Sử dụng các icon để làm cho câu trả lời của bạn trở nên sinh động hơn.
        Hãy tư vấn nhiệt tình và giúp khách hàng tìm ra sản phẩm phù hợp nhất với nhu cầu của họ.

        Câu hỏi của khách hàng: {question}
        Phần nội dung có thể liên quan đến câu hỏi: {context}

        Lịch sử cuộc trò chuyện trước đó: {history}
    """,

    "rewite_query": """
    Nhiệm vụ của bạn là viết rõ lại câu hỏi của người dùng từ lịch sử của họ với chatbot.
    Lưu ý: luôn viết lại tên sản phẩm vào câu hỏi mới. Nếu không có lịch sử thì giữ nguyên câu hỏi, không cần viết lại.
    ###############
    Lịch sử cuộc trò chuyện trước đó: {history}
    ################
    Câu hỏi của người dùng: {question}
    ################
    Ví dụ: 
        user: Tôi muốn xem điện thoại .
        bot: 2 sản phẩm liên quan kèm tên hãng và giá:
                1. Điện thoại Iphone 14 giá 6,000,000 đồng.
                2. Điện thoại Samsung Galaxy giá 9,000,000 đồng.
        user: Tôi muốn xem sản phẩm số 2.
        => rewrite user Tôi muốn xem sản phẩm Samsung Galaxy.
    Chỉ cần trả ra câu được viết lại mà không cần thêm bất kỳ thông tin nào khác.
    """
}
