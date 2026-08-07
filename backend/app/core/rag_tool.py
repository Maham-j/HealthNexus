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


FAISS_TOOL_DESCRIPTION = """
<tool>

    <purpose>
        Retrieve similar Cypher query examples from the FAISS knowledge base.
    </purpose>

    <usage>

        <input>
            A short natural-language biomedical question, rephrased or generalized by you — do not copy the user's exact wording verbatim.
        </input>

        <behavior>
            Retrieve similar questions and their corresponding Cypher queries.
            Use the returned examples only to understand query patterns.
        </behavior>

    </usage>

    <limitations>

        <rule>
            Never use the returned examples as medical evidence.
        </rule>

        <rule>
            Never use the returned examples as the final answer.
        </rule>

        <rule>
            Use them only to help generate a new Cypher query.
        </rule>

    </limitations>

    <output>
        Return similar questions together with their Cypher queries.
    </output>

</tool>
"""

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


