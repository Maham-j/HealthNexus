"""Given a user's question, find the most similar questions from our Excel knowledge bank."""

from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import time


class RAGTool:

    def __init__(self):

        excel_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "PrimeKG_manual_databank.xlsx"
        )

        start = time.time()
        print("Loading Excel...")
        self.df = pd.read_excel(excel_path)

        required_columns = [
            "User Question",
            "Cypher Query",
            "Neo4J Response",
            "LLM Finding",
        ]

        missing = [
            col for col in required_columns
            if col not in self.df.columns
        ]

        if missing:
            raise ValueError(f"Missing columns: {missing}")

        print("Excel:", time.time() - start)


        start = time.time()
        print("Loading embedding model...")
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        questions = self.df["User Question"].tolist()
        print("Model:", time.time() - start)


        start = time.time()
        print("Creating embeddings...")
        embeddings = self.model.encode(
            questions,
            convert_to_numpy=True
        ).astype("float32")

        dimension = embeddings.shape[1]
        print("Embeddings:", time.time() - start)

        start = time.time()
        print("Building FAISS index...")
        self.index = faiss.IndexFlatL2(dimension)

        self.index.add(embeddings)
        print("RAG tool initialized!")
        print("FAISS:", time.time() - start)

    
    """This function take the LLM-generated natural language query.
        Convert it into an embedding.
        Search the FAISS index.
        Return the top-k most similar examples."""
    def fetch_similar_queries(self, query: str, top_k: int = 3):

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        ).astype("float32")

        distances, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for idx in indices[0]:
            results.append({
                "question": self.df.iloc[idx]["User Question"],
                "cypher": self.df.iloc[idx]["Cypher Query"],
            })

        return results


rag_tool_groq = {
    "type": "function",
    "function": {
        "name": "fetchSimilarQueries",
        "description": (
            "Retrieve only Cypher query examples from the FAISS knowledge base. "
            "This tool does not contain medical answers or final findings. "
            "Use it only to understand previous query patterns and generate a new Neo4j Cypher query. "
            "Never use the returned examples as the final answer. "
            "Call this function with exactly one argument named 'query'. "
            "The query must be a short natural-language medical question, not Cypher. "
            "Example: 'diseases related to psoriasis'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Short natural-language question used to retrieve similar Cypher examples."
                    )
                }
            },
            "required": ["query"]
        }
    }
}
    


rag_tool = None


def get_rag_tool():
    global rag_tool

    if rag_tool is None:
        rag_tool = RAGTool()

    return rag_tool


#debuging purpose
if __name__ == "__main__":
        
        print("Testing search...")
        results = get_rag_tool().fetch_similar_queries(
            "What diseases cause red itchy eyes?"
        )

        for result in results:
            print(result)


