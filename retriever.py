from langchain.schema import BaseRetriever
import numpy as np
from pydantic import Field
from typing import List, Any

class ScoredRetriever(BaseRetriever):

    vector_store: Any = Field(description="Vector store for similarity search")
    score_threshold: float = Field(default=0.1, description="Minimum score threshold for a document to be considered relevant")
    k: int = Field(default=3, description="Number of documents to retrieve")

    def __init__(self, vector_store: Any, score_threshold: float = 0.8, k: int = 3):
        super().__init__(
            vector_store = vector_store,
            score_threshold = score_threshold,
            k = k
        )
    
    def get_relevant_documents(self, query):
        """
        Get relevant documents based on the query

        Args:
            query (str): The query string

        Returns:
            List[Document]: The list of relevant documents
        """
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k = self.k)

        highest_score = -1
        most_relevant_document = None

        for doc, score in docs_and_scores:
            normalized_score = self.normailze_score(score)

            if normalized_score >= self.score_threshold and normalized_score > highest_score:
                highest_score = normalized_score
                most_relevant_document = doc
                most_relevant_document.metadata["score"] = normalized_score
                most_relevant_document.metadata["title"] = doc.metadata.get("title", None)
                most_relevant_document.metadata["source"] = doc.metadata.get("source", None)

        if most_relevant_document:
            print("Metadata", most_relevant_document.metadata.get("score", None), most_relevant_document.metadata.get("source", None))
        return [most_relevant_document] if most_relevant_document else []
    
    def normailze_score(self, score):
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
