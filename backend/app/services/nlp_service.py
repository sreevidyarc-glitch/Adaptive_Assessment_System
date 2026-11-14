import logging
from typing import List, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger("adaptive_assessment.nlp")

class NLPService:
    """
    NLP service for Sentence Transformers embeddings and cosine similarity.
    Executes Stages 1 & 2 of the adaptive assessment algorithm:
    1. Computes cosine similarity between chunk s_i and each objective o_j
    2. Assigns s_i to the most similar objective meeting the similarity threshold
    3. Identifies and reports objectives with no matching chunks as coverage gaps
    """
    def __init__(self):
        self._model = None
        self._model_failed = False

    def _get_model(self):
        if self._model is None and not self._model_failed:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded SentenceTransformer model 'all-MiniLM-L6-v2'.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Using Scikit-Learn TF-IDF vectorizer fallback.")
                self._model_failed = True
                self._model = None
        return self._model

    def compute_similarity_matrix(self, texts_chunks: List[str], texts_objectives: List[str]) -> List[List[float]]:
        """
        Computes cosine similarity between all chunks (rows) and all objectives (columns).
        Returns a 2D list of shape [len(texts_chunks), len(texts_objectives)].
        """
        if not texts_chunks or not texts_objectives:
            return []

        model = self._get_model()
        if model is not None:
            try:
                from sentence_transformers import util
                emb_chunks = model.encode(texts_chunks, convert_to_tensor=True)
                emb_objs = model.encode(texts_objectives, convert_to_tensor=True)
                sim_matrix = util.cos_sim(emb_chunks, emb_objs)
                return sim_matrix.cpu().tolist()
            except Exception as e:
                logger.warning(f"Error computing SentenceTransformer embeddings: {e}. Falling back to TF-IDF.")

        # Scikit-learn TF-IDF Cosine Similarity Fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        all_corpus = texts_chunks + texts_objectives
        tfidf_all = vectorizer.fit_transform(all_corpus)

        n_chunks = len(texts_chunks)
        tfidf_chunks = tfidf_all[:n_chunks]
        tfidf_objectives = tfidf_all[n_chunks:]

        sim = cosine_similarity(tfidf_chunks, tfidf_objectives)
        return sim.tolist()

    def map_chunks_to_objectives(
        self,
        chunks: List[Dict[str, Any]],
        objectives: List[Dict[str, Any]],
        similarity_threshold: float = 0.35
    ) -> Dict[str, Any]:
        """
        Maps content chunks S to learning objectives O using cosine similarity.
        Enforces Section 3 lines 51-59 of integrated_algorithm_auth_privacy.md.
        """
        if not chunks or not objectives:
            return {
                "mapped_chunks": [],
                "objective_summaries": [],
                "coverage_gaps": [obj["code"] for obj in objectives] if objectives else []
            }

        chunk_texts = [c["content"] for c in chunks]
        obj_texts = [f"{o['code']}: {o['description']}" for o in objectives]

        # Similarity matrix M: rows = chunks, cols = objectives
        sim_matrix = self.compute_similarity_matrix(chunk_texts, obj_texts)

        mapped_chunks = []
        obj_chunk_counts = {o["id"]: 0 for o in objectives}
        obj_max_scores = {o["id"]: 0.0 for o in objectives}

        for i, chunk in enumerate(chunks):
            scores = sim_matrix[i]
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            best_obj = objectives[best_idx]

            is_mapped = best_score >= similarity_threshold

            mapped_chunk_data = {
                **chunk,
                "similarity_score": round(best_score, 4),
                "mapped_objective_id": best_obj["id"] if is_mapped else None,
                "mapped_objective_code": best_obj["code"] if is_mapped else None,
                "is_mapped": is_mapped
            }
            mapped_chunks.append(mapped_chunk_data)

            if is_mapped:
                obj_chunk_counts[best_obj["id"]] += 1
                if best_score > obj_max_scores[best_obj["id"]]:
                    obj_max_scores[best_obj["id"]] = best_score

        # Coverage Summaries & Gap Detection
        objective_summaries = []
        coverage_gaps = []

        for obj in objectives:
            count = obj_chunk_counts[obj["id"]]
            max_sim = obj_max_scores[obj["id"]]
            is_gap = (count == 0)

            objective_summaries.append({
                "objective_id": obj["id"],
                "code": obj["code"],
                "description": obj["description"],
                "weight": obj.get("weight", 1.0),
                "mapped_chunk_count": count,
                "max_similarity": round(max_sim, 4),
                "is_gap": is_gap
            })

            if is_gap:
                coverage_gaps.append({
                    "objective_id": obj["id"],
                    "code": obj["code"],
                    "description": obj["description"]
                })

        return {
            "mapped_chunks": mapped_chunks,
            "objective_summaries": objective_summaries,
            "coverage_gaps": coverage_gaps,
            "total_chunks": len(chunks),
            "similarity_threshold": similarity_threshold
        }

nlp_service = NLPService()
