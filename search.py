import pandas as pd
import numpy as np
import sqlite3
import faiss
from sentence_transformers import SentenceTransformer
import yaml
from unidecode import unidecode
import re


class SemanticSearcher:
    def __init__(self):
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)

        # Cargar modelos e índices
        self.model = SentenceTransformer(self.config['model']['embedding_model'])
        self.faiss_index = faiss.read_index('faiss_index.bin')
        self.product_ids = pd.read_csv('product_ids.csv')
        self.product_data = pd.read_pickle('product_data.pkl')
        self.conn = sqlite3.connect('product_index.db')

    def preprocess_query(self, text):
        """Preprocesa la consulta igual que los documentos"""
        text = unidecode(text).lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def bm25_search(self, query, top_k=100):
        """Búsqueda inicial con BM25"""
        query_processed = self.preprocess_query(query)

        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT reference, title, description, features, 
               bm25(products_fts) as score
        FROM products_fts 
        WHERE products_fts MATCH ?
        ORDER BY score
        LIMIT ?
        ''', (query_processed, top_k))

        results = cursor.fetchall()
        return results

    def semantic_search(self, query, top_k=10):
        """Búsqueda semántica con re-ranking"""
        # Primera fase: BM25
        bm25_results = self.bm25_search(
            query,
            top_k=self.config['index']['top_k_initial']
        )

        if not bm25_results:
            return []

        # Obtener embeddings de los resultados de BM25
        references = [r[0] for r in bm25_results]
        product_indices = self.product_ids[
            self.product_ids[self.config['data']['id_column']].isin(references)
        ].index.tolist()

        # Embedding de la consulta
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)

        # Búsqueda en FAISS
        distances, indices = self.faiss_index.search(
            query_embedding,
            len(product_indices)
        )

        # Formatear resultados
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(product_indices):
                product_idx = product_indices[idx]
                product = self.product_data.iloc[product_idx]

                # Calcular score 0-100
                score = max(0, min(100, (distance + 1) * 50))

                results.append({
                    'reference': product[self.config['data']['id_column']],
                    'title': product.get('titulo', ''),
                    'price': product.get('precio', ''),
                    'score': round(score, 2),
                    'description': product.get('descripcion', '')[:200] + '...' if pd.notna(
                        product.get('descripcion')) else '',
                    'match_reason': self.get_match_reason(query, product)
                })

        # Ordenar por score y limitar resultados
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def get_match_reason(self, query, product):
        """Identifica por qué coincidió el producto"""
        query_terms = set(self.preprocess_query(query).split())
        reasons = []

        # Verificar coincidencias en diferentes campos
        for field in ['titulo', 'descripcion', 'caracteristicas']:
            if field in product and pd.notna(product[field]):
                field_text = self.preprocess_query(product[field])
                field_terms = set(field_text.split())
                matching_terms = query_terms.intersection(field_terms)

                if matching_terms:
                    reasons.append(f"{field}: {', '.join(matching_terms)}")

        return "; ".join(reasons) if reasons else "Coincidencia semántica"

    def close(self):
        self.conn.close()


# Singleton para la aplicación
searcher = SemanticSearcher()