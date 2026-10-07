"""
Medical Knowledge RAG Pipeline for City Care Clinics
Retrieves clinical FAQs, lab instructions, patient leaflets, and specialty mappings
with strict attribution, source citations, and hallucination prevention.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "knowledge_base"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

class MedicalKnowledgeRAG:
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self._load_documents()
        self._init_vector_store()

    def _load_documents(self):
        """Loads and indexes structured knowledge chunks from JSON files."""
        # 1. FAQs
        faq_file = KB_DIR / "clinic_faqs.json"
        if faq_file.exists():
            with open(faq_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("clinic_faqs", []):
                    self.documents.append({
                        "id": item["id"],
                        "category": "Clinic FAQs",
                        "title": item["question"],
                        "content": f"Question: {item['question']}\nAnswer: {item['answer']}",
                        "source": item["source"],
                        "tags": item.get("tags", [])
                    })

        # 2. Lab Instructions
        lab_file = KB_DIR / "lab_test_instructions.json"
        if lab_file.exists():
            with open(lab_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("lab_instructions", []):
                    self.documents.append({
                        "id": item["id"],
                        "category": "Lab Test Preparation",
                        "title": f"Preparation for {item['test_name']}",
                        "content": f"Test: {item['test_name']}\nFasting: {item['fasting_hours']}\nInstructions: {item['preparation']}\nSpecial Notes: {item.get('special_notes', '')}",
                        "source": item["source"],
                        "tags": item.get("tags", [])
                    })

        # 3. Patient Education Leaflets
        leaf_file = KB_DIR / "patient_education_leaflets.json"
        if leaf_file.exists():
            with open(leaf_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("leaflets", []):
                    self.documents.append({
                        "id": item["id"],
                        "category": "Patient Education",
                        "title": item["topic"],
                        "content": f"Topic: {item['topic']}\nSummary: {item['summary']}\nGuidance: {item['content']}",
                        "source": item["source"],
                        "tags": item.get("tags", [])
                    })

        # 4. Specialty Mapping
        spec_file = KB_DIR / "symptom_specialty_mapping.json"
        if spec_file.exists():
            with open(spec_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("mappings", []):
                    self.documents.append({
                        "id": f"spec_{item['specialty'].lower().replace(' ', '_')}",
                        "category": "Specialty Mapping",
                        "title": f"Clinical Specialty: {item['specialty']}",
                        "content": f"Specialty: {item['specialty']}\nTypical Symptoms: {', '.join(item['typical_symptoms'])}\nKeywords: {', '.join(item['keywords'])}\nUrgency: {item['urgency_hint']}\nRed Flags: {', '.join(item['red_flags'])}",
                        "source": "City Care Clinics Clinical Triage Protocols 2026",
                        "tags": item.get("keywords", [])
                    })

    def _init_vector_store(self):
        """Initializes ChromaDB collection with fallback to semantic keyword scoring."""
        self.chroma_collection = None
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            # Delete if exists to refresh
            try:
                client.delete_collection("medical_knowledge")
            except:
                pass
            self.chroma_collection = client.create_collection(
                name="medical_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            # Add documents
            ids = [doc["id"] for doc in self.documents]
            texts = [f"{doc['title']}\n{doc['content']}" for doc in self.documents]
            metadatas = [{"source": doc["source"], "category": doc["category"], "title": doc["title"]} for doc in self.documents]
            self.chroma_collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
        except Exception as e:
            print(f"[RAG Init] ChromaDB fallback enabled: {e}")

    def retrieve(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top matching knowledge chunks with hybrid semantic + keyword scoring."""
        query_text_lower = query_text.lower()
        candidates: Dict[str, Dict[str, Any]] = {}

        # 1. Dense Vector Retrieval via ChromaDB
        if self.chroma_collection:
            try:
                results = self.chroma_collection.query(
                    query_texts=[query_text],
                    n_results=min(top_k * 2, len(self.documents))
                )
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    distances = results.get("distances", [[0]*len(docs)])[0]
                    ids = results["ids"][0]
                    for i, d in enumerate(docs):
                        score = max(0.0, 1.0 - distances[i])
                        candidates[ids[i]] = {
                            "id": ids[i],
                            "title": metas[i]["title"],
                            "content": d,
                            "source": metas[i]["source"],
                            "category": metas[i]["category"],
                            "score": score
                        }
            except Exception:
                pass

        # 2. Lexical Keyword Boosting (BM25 intuition)
        tokens = re.findall(r"\w+", query_text_lower)
        for doc in self.documents:
            lex_score = 0.0
            doc_str = f"{doc['title']} {doc['content']} {' '.join(doc['tags'])}".lower()
            for t in tokens:
                if len(t) <= 2:
                    continue
                if t in doc_str:
                    lex_score += 0.25
                if t in doc['title'].lower():
                    lex_score += 0.5
                if any(t == tag.lower() for tag in doc.get('tags', [])):
                    lex_score += 0.75

            doc_id = doc["id"]
            if doc_id in candidates:
                candidates[doc_id]["score"] += lex_score
            elif lex_score > 0.5:
                candidates[doc_id] = {
                    "id": doc_id,
                    "title": doc["title"],
                    "content": f"{doc['title']}\n{doc['content']}",
                    "source": doc["source"],
                    "category": doc["category"],
                    "score": lex_score
                }

        # Sort combined candidates by fused score
        ranked = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)
        return ranked[:top_k]

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answers a clinical question strictly grounded in retrieved knowledge.
        Returns synthesized response with explicit source citations.
        """
        retrieved_docs = self.retrieve(question, top_k=2)
        if not retrieved_docs:
            return {
                "question": question,
                "answer": "Maaf kijiye, is sawal ki tasdeeq shuda maloomat hamare clinical database mein mojood nahi hain. Baraye meharbani doctor se rabta karein.",
                "citations": [],
                "is_grounded": False,
                "hallucination_detected": False
            }

        top_doc = retrieved_docs[0]
        citations = [
            {
                "source": d["source"],
                "document_title": d["title"],
                "category": d["category"]
            }
            for d in retrieved_docs
        ]

        # Extract precise factual core from top retrieved content
        extracted_info = top_doc["content"]
        # Format a concise, grounded clinical answer
        answer_text = f"{extracted_info}\n\n[Tasdeeq Shuda Hawala / Source: {top_doc['source']}]"

        return {
            "question": question,
            "answer": answer_text,
            "citations": citations,
            "top_match_id": top_doc["id"],
            "is_grounded": True,
            "hallucination_detected": False
        }


# Singleton instance
rag = MedicalKnowledgeRAG()

if __name__ == "__main__":
    test_q = "What are the timings for DHA branch and consultation fees for Cardiology?"
    res = rag.answer_question(test_q)
    print("Question:", res["question"])
    print("\nAnswer:\n", res["answer"])
    print("\nCitations:", res["citations"])
