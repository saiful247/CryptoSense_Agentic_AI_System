# # app/services/history_store.py
# import os, time
# from typing import List, Dict, Any, Optional, Tuple
# import chromadb
# from chromadb.config import Settings
# from sentence_transformers import SentenceTransformer

# CHROMA_DIR = os.getenv("HISTORY_DB_DIR", ".chroma")
# EMBED_MODEL = os.getenv("HISTORY_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# class HistoryStore:
#     def __init__(self, collection_name: str = "risk_history"):
#         self.client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))
#         self.col = self.client.get_or_create_collection(collection_name)
#         self.model = SentenceTransformer(EMBED_MODEL)

#     def _embed(self, text: str) -> List[float]:
#         return self.model.encode(text, normalize_embeddings=True).tolist()

#     def add_record(self, item: Dict[str, Any]) -> str:
#         """
#         item: {
#           "kind": "url|token|contract",
#           "input": "https://.. | PEPE | 0x..",
#           "risk": "low|medium|high",
#           "score": int,
#           "reasons": [..],
#           "ts": int (optional epoch seconds)
#         }
#         """
#         rid = f"{int(time.time()*1000)}-{os.getpid()}"
#         ts = item.get("ts") or int(time.time())
#         text = f"{item.get('kind')} | {item.get('input')} | {item.get('risk')} | {item.get('score')} | {' ; '.join(item.get('reasons') or [])}"
#         emb = self._embed(text)
#         self.col.add(ids=[rid], embeddings=[emb], metadatas=[{
#             "kind": item.get("kind"),
#             "input": item.get("input"),
#             "risk": item.get("risk"),
#             "score": int(item.get("score", 0)),
#             "ts": ts,
#         }], documents=[text])
#         self.client.persist()
#         return rid

#     def similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
#         emb = self._embed(query_text)
#         res = self.col.query(query_embeddings=[emb], n_results=top_k)
#         out = []
#         for i in range(len(res.get("ids", [[]])[0])):
#             out.append({
#                 "id": res["ids"][0][i],
#                 "distance": res["distances"][0][i] if "distances" in res else None,
#                 "document": res["documents"][0][i],
#                 "meta": res["metadatas"][0][i],
#             })
#         return out


# app/services/history_store.py
import os, time
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

# NOTE: sentence-transformers is required. Install:
#   pip install sentence-transformers chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = os.getenv("HISTORY_DB_DIR", ".chroma")
EMBED_MODEL = os.getenv("HISTORY_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

class HistoryStore:
    def __init__(self, collection_name: str = "risk_history"):
        # Persist Chroma to disk + turn off telemetry
        self.client = chromadb.Client(
            Settings(persist_directory=CHROMA_DIR, anonymized_telemetry=False)
        )
        # Force cosine distance (works well with normalized SBERT)
        self.col = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        # Lazy-load the embedder once
        self.model = SentenceTransformer(EMBED_MODEL)

    def _embed(self, text: str) -> List[float]:
        # Normalized embeddings so cosine distance is meaningful (0 = identical)
        emb = self.model.encode(text, normalize_embeddings=True)
        # Ensure plain list[float]
        return emb.tolist() if hasattr(emb, "tolist") else list(emb)

    def add_record(self, item: Dict[str, Any]) -> str:
        """
        item: {
          "kind": "url|token|contract",
          "input": "https://.. | PEPE | 0x..",
          "risk": "low|medium|high",
          "score": int,
          "reasons": [..],
          "ts": int (optional epoch seconds)
        }
        """
        rid = f"{int(time.time()*1000)}-{os.getpid()}"
        ts = int(item.get("ts") or time.time())

        text = f"{item.get('kind')} | {item.get('input')} | {item.get('risk')} | {int(item.get('score', 0))} | {' ; '.join(item.get('reasons') or [])}"
        emb = self._embed(text)

        self.col.add(
            ids=[rid],
            embeddings=[emb],
            metadatas=[{
                "kind": item.get("kind"),
                "input": item.get("input"),
                "risk": item.get("risk"),
                "score": int(item.get("score", 0)),
                "ts": ts,
            }],
            documents=[text],
        )
        self.client.persist()
        return rid

    def similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        emb = self._embed(query_text)
        # IMPORTANT: Ask Chroma to include distances & metadata
        res = self.col.query(
            query_embeddings=[emb],
            n_results=top_k,
            include=["distances", "metadatas", "documents"],
        )
        out: List[Dict[str, Any]] = []

        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0] if "distances" in res else []
        documents = res.get("documents", [[]])[0] if "documents" in res else []
        metadatas = res.get("metadatas", [[]])[0] if "metadatas" in res else []

        for i in range(len(ids)):
            out.append({
                "id": ids[i],
                "distance": distances[i] if i < len(distances) else None,
                "document": documents[i] if i < len(documents) else None,
                "meta": metadatas[i] if i < len(metadatas) else {},
            })
        return out
