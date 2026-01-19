import threading

from langchain.tools import BaseTool
from retriever.els import ElasticQueryEngine


class DSM5RetrievalTool(BaseTool):
    """
    Tool for retrieving DSM-5 diagnostic criteria and clinical information.

    Uses HealthcareRetriever to perform hybrid search (keyword + semantic)
    on DSM-5 chunks indexed in Elasticsearch.

    Supports:
    - Finding diagnostic criteria for psychiatric disorders
    - Querying clinical information and diagnostic features
    - Searching related information using hierarchical structure
    - Differential diagnosis information
    """

    name: str = "DSM5"

    description: str = """Tool for querying DSM-5 diagnostic criteria and clinical information.
    Use cases:
    - Find diagnostic criteria for a disorder (e.g., "Diagnostic criteria for autism spectrum disorder")
    - Query clinical features and severity levels (e.g., "Diagnostic features of depression")
    - Search differential diagnosis (e.g., "Differentiate anxiety disorder from panic disorder")
    - Find related psychiatric disorder information
    Input: Query about DSM-5 (e.g., "Severe autism spectrum disorder criteria")
    Output: List of relevant sections with detailed diagnostic information
    """

    class Config:
        extra = "allow"  # Allow adding new attributes after init

    def __init__(
        self,
        embedding_model: str = "openai",  # "google" or "openai"
        top_k: int = 5,
        include_context: bool = True,
        callbacks=None,
    ):
        """
        Initialize DSM5RetrievalTool.

        Args:
            embedding_model: Embedding model to use ("google" or "openai")
            top_k: Number of top results to return (default: 5)
            include_context: Whether to include related sections
        """
        super().__init__()

        self._retriever = None
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.include_context = include_context
        self.callbacks = callbacks

    @property
    def retriever(self):
        if not self._retriever:
            with threading.Lock():
                self._retriever = ElasticQueryEngine()
        return self._retriever

    def _format_output(self, results: dict) -> list[dict]:
        """
        Format the retrieval results into a structured output.

        Args:
            results: Raw results from the retriever

        Returns:
            Formatted results
        """
        formatted_results = []
        for item in results:
            formatted_item = {
                "title": item.get("title"),
                "content": item.get("content"),
            }
            formatted_results.append(formatted_item)
        return formatted_results

    def _run(self, query: str) -> str:
        """
        Synchronous execution of DSM-5 retrieval.

        Args:
          query: User's question about DSM-5
            (e.g., "What are the diagnostic criteria for autism spectrum disorder?")

        Returns:
            Formatted text with relevant DSM-5 diagnostic information
        """
        try:
            # Perform hybrid search
            results = self.retriever.invoke(
                query=query,
                config={
                    "top_k": self.top_k,
                    "include_context": self.include_context,
                    "callbacks": self.callbacks,
                },
            )
            return self._format_output(results)

        except Exception as e:
            error_msg = f"Error retrieving DSM-5 information: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _arun(self, query: str) -> str:
        """
        Asynchronous execution of DSM-5 retrieval.

        Args:
            query: User's question about DSM-5

        Returns:
            Formatted text with relevant DSM-5 diagnostic information
        """
        try:
            # Perform async hybrid search
            results = await self.retriever.ainvoke(
                query=query,
                config={
                    "top_k": self.top_k,
                    "include_context": self.include_context,
                    "callbacks": self.callbacks,
                },
            )
            return self._format_output(results)

        except Exception as e:
            error_msg = f"Async error retrieving DSM-5 information: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)


if __name__ == "__main__":
    # python -m tools.health_tool

    tool = DSM5RetrievalTool(embedding_model="google", top_k=3, include_context=True)
    query = "Rối loạn tic là gì và được phân loại như thế nào trong DSM-5?"
    response = tool.invoke(input=query)
    print(f"Query: {query}\n")
    print("Response:")
    for idx, item in enumerate(response):
        print(f"\nResult {idx + 1}:")
        print(f"Title: {item['title']}")
        print(f"Content: {item['content']}")