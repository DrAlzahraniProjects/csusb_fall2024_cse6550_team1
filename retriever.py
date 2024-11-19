from langchain.schema import BaseRetriever
import numpy as np
from pydantic import Field
from typing import List, Any

class ScoreThresholdRetriever(BaseRetriever):
    """
    A retriever that retrieves relevant documents based on similarity scores from a vector store.

    Attributes:
        vector_store (Any): The vector store for similarity search.
        score_threshold (float): Minimum normalized score to consider a document relevant.
        k (int): Number of documents to retrieve.

    """

    vector_store: Any = Field(..., description="Vector store for similarity search")
    score_threshold: float = Field(default=0.1, description="Minimum score threshold for a document to be considered relevant")
    k: int = Field(default=5, description="Number of documents to retrieve")

    def get_relevant_documents(self, query:str) -> List[Any]:
        """
        Get relevant documents based on the query

        Args:
            query (str): The query string

        Returns:
            List[Document]: The list of relevant documents
        """
        try:
            docs_and_scores = self.vector_store.similarity_search_with_score(query, k=self.k)
        except Exception:
            return []

        if not docs_and_scores:
        # If no documents are found, return an empty list or a default message
            return []

        # Initialize variables for tracking the most relevant document
        relevant_documents = []

        for doc, score in docs_and_scores:
            normalized_score = self._normalize_score(score)

            # Check if the document is relevant and has a higher score than the current highest score
            if normalized_score >= self.score_threshold:
                doc.metadata["score"] = normalized_score
                doc.metadata["title"] = doc.metadata.get("title", "Untitled")
                doc.metadata["source"] = doc.metadata.get("source", "Unknown")
                relevant_documents.append(doc)

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
