class OpenAIClientWrapper:
    def __init__(self, timeout: int = config.TIMEOUT, model: str = config.MODEL):
        self.client = OpenAI(timeout=timeout)
        self.model = model

    def call_chat_api(self, messages: list, tools: list, tool_choice: str = "auto"):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )