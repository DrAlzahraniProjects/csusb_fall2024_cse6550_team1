from langchain.schema import BaseRetriever, Document
import numpy as np
from pydantic import Field
from pymilvus import Collection
from typing import List, Any

class ScoreThresholdRetriever(BaseRetriever):
    """
    A retriever that retrieves relevant documents based on similarity scores from a vector store.

    Attributes:
        vector_store (Any): The vector store for similarity search.
        score_threshold (float): Minimum normalized score to consider a document relevant.
        k (int): Number of documents to retrieve.

    """

    score_threshold: float = Field(default=0.1, description="Minimum score threshold for a document to be considered relevant")
    k: int = Field(default=5, description="Number of documents to retrieve")

    def _get_relevant_documents(self) -> List[Any]:
        # This method is not implemented in the base class
        pass

    def get_related_documents(self, query_embedding, collection: Collection) -> List[Any]:
        """
        Get relevant documents based on the query

        Args:
            query (str): The query string

        Returns:
            List[Document]: The list of relevant documents
        """
        try:
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            result = collection.search(
                data = [query_embedding],
                anns_field = "embedding",
                param = search_params,
                limit = self.k,
                output_fields = ["title", "text" ,"source"]
            )
            docs_and_scores = result[0]
            # docs_and_scores = self.vector_store.similarity_search_with_score(query, k=self.k)
        except Exception:
            return []

        if not docs_and_scores:
        # If no documents are found, return an empty list or a default message
            return []

        # Initialize variables for tracking the most relevant document
        relevant_documents = []

        for doc in docs_and_scores:
            score = doc.distance
            normalized_score = self._normalize_score(score)
            print("Doc: ", doc)
            print("Normalized score: ", normalized_score)
            page_content = doc.entity.get("text")
            title = doc.entity.get("title")
            source = doc.entity.get("source")
            if page_content is None:
                page_content = ""
            if title is None:
                title = "Untitled"
            if source is None:
                source = "Unknown"
            # Check if the document is relevant and has a higher score than the current highest score
            if normalized_score >= self.score_threshold:
                res = Document(
                    page_content = page_content,
                    metadata = {
                        'score': normalized_score,
                        'title': title,
                        'source': source
                    }
                )
                relevant_documents.append(res)

        # Sort the relevant documents by score in descending order
        relevant_documents.sort(key=lambda x: x.metadata["score"], reverse=True)

        return relevant_documents
    
    @staticmethod
    def _normalize_score(score):
        """
        Normalize the score to a value between 0 and 1

        Args:
            score (float): The score to be normalized

        Returns:
            float: The normalized score
        """
        # Assuming Milvus L2 distance, adjust based on your distance metric
        max_distance = np.sqrt(2)
        normalized = 1 - (score / max_distance)
        return max(0, min(1, normalized))
