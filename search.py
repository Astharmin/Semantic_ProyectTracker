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
        print("Inicializando SemanticSearcher...")

        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        print("✓ Configuración cargada")

        # Cargar modelos e índices con verificación
        try:
            self.model = SentenceTransformer(self.config['model']['embedding_model'])
            print(f"✓ Modelo de embeddings cargado: {self.config['model']['embedding_model']}")
        except Exception as e:
            print(f"✗ Error cargando modelo: {e}")
            raise

        try:
            self.faiss_index = faiss.read_index('faiss_index.bin')
            print(f"✓ Índice FAISS cargado: {self.faiss_index.ntotal} vectores")
        except Exception as e:
            print(f"✗ Error cargando índice FAISS: {e}")
            raise

        try:
            self.product_ids = pd.read_csv('product_ids.csv')
            print(f"✓ IDs de productos cargados: {len(self.product_ids)} registros")
        except Exception as e:
            print(f"✗ Error cargando product_ids.csv: {e}")
            raise

        try:
            self.product_data = pd.read_pickle('product_data.pkl')
            print(f"✓ Datos de productos cargados: {len(self.product_data)} registros")
            print(f"  Columnas disponibles: {list(self.product_data.columns)}")
        except Exception as e:
            print(f"✗ Error cargando product_data.pkl: {e}")
            raise

        try:
            self.conn = sqlite3.connect('product_index.db')
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products_fts")
            fts_count = cursor.fetchone()[0]
            print(f"✓ Base de datos FTS5 cargada: {fts_count} documentos indexados")

            # Debug: mostrar algunos registros
            cursor.execute("SELECT * FROM products_fts LIMIT 2")
            sample_records = cursor.fetchall()
            print(f"  Muestra de registros: {len(sample_records)}")
            for i, record in enumerate(sample_records):
                print(f"    Registro {i + 1}: {record[:2]}...")  # Primeros 2 campos

        except Exception as e:
            print(f"✗ Error conectando a la base de datos: {e}")
            raise

        print("✅ SemanticSearcher inicializado exitosamente!")
        print("=" * 50)

    def preprocess_query(self, text):
        """Preprocesa la consulta igual que los documentos"""
        if pd.isna(text) or text == "":
            return ""
        text = str(text)
        text = unidecode(text).lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def bm25_search(self, query, top_k=100):
        """Búsqueda inicial con BM25"""
        query_processed = self.preprocess_query(query)

        if not query_processed:
            return []

        # Formato correcto para FTS5 - usar comillas para frases
        fts_query = f'"{query_processed}"'

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            SELECT rowid, reference, title, description, features, 
                   bm25(products_fts) as score
            FROM products_fts 
            WHERE products_fts MATCH ?
            ORDER BY score
            LIMIT ?
            ''', (fts_query, top_k))

            results = cursor.fetchall()
            print(f"BM25 encontró {len(results)} resultados para: '{query_processed}'")
            return results
        except sqlite3.Error as e:
            print(f"Error en búsqueda BM25: {e}")
            print(f"Consulta FTS: {fts_query}")
            return []

    def semantic_search(self, query, top_k=10):
        """Búsqueda semántica con re-ranking"""
        print(f"\n🔍 Buscando: '{query}'")

        # Primera fase: BM25
        bm25_results = self.bm25_search(
            query,
            top_k=self.config['index']['top_k_initial']
        )

        if not bm25_results:
            print("❌ No se encontraron resultados en BM25")
            return []

        # Obtener references de los resultados de BM25
        references = [r[1] for r in bm25_results]  # reference está en índice 1
        print(f"References encontrados: {references}")

        # Buscar los índices en product_ids
        product_indices = []
        for ref in references:
            matches = self.product_ids[self.product_ids[self.config['data']['id_column']] == ref]
            if not matches.empty:
                product_indices.append(matches.index[0])

        print(f"Índices de productos encontrados: {product_indices}")

        if not product_indices:
            print("❌ No se pudieron mapear los references a índices")
            return []

        # Embedding de la consulta
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)

        # Búsqueda en FAISS - usar solo los embeddings de los resultados BM25
        subset_embeddings = self.faiss_index.reconstruct_batch(product_indices)
        distances, indices = self.faiss_index.search(
            query_embedding,
            min(top_k, len(product_indices))
        )

        # Formatear resultados
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(product_indices) and idx >= 0:
                actual_idx = product_indices[idx]
                product = self.product_data.iloc[actual_idx]

                # Calcular score 0-100 (cosine similarity convertida a porcentaje)
                score = max(0, min(100, (distance + 1) * 50))

                results.append({
                    'reference': product[self.config['data']['id_column']],
                    'title': product.get('title', 'Sin título'),
                    'price': product.get('price', 'N/A'),
                    'score': round(score, 2),
                    'description': str(product.get('description', ''))[:200] + '...' if pd.notna(
                        product.get('description')) else '',
                    'match_reason': self.get_match_reason(query, product)
                })

        # Ordenar por score y limitar resultados
        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"✅ Búsqueda completada: {len(results)} resultados")
        return results[:top_k]

    def get_match_reason(self, query, product):
        """Identifica por qué coincidió el producto"""
        query_terms = set(self.preprocess_query(query).split())
        reasons = []

        # Verificar coincidencias en diferentes campos
        for field in ['reference', 'title', 'description', 'features', 'category', 'price']:
            if field in product and pd.notna(product[field]):
                field_text = self.preprocess_query(str(product[field]))
                field_terms = set(field_text.split())
                matching_terms = query_terms.intersection(field_terms)

                if matching_terms:
                    reasons.append(f"{field}: {', '.join(matching_terms)}")

        return "; ".join(reasons) if reasons else "Coincidencia semántica"

    def close(self):
        self.conn.close()


# Singleton para la aplicación
searcher = SemanticSearcher()

if __name__ == "__main__":
    print("\n🔍 Realizando pruebas de búsqueda...")

    # Pruebas con diferentes consultas
    test_queries = [
        "producto",
        "categoria",
        "precio",
        "reference",
        "features"
    ]

    for test_query in test_queries:
        print(f"\n{'=' * 50}")
        print(f"TEST: '{test_query}'")
        print(f"{'=' * 50}")

        results = searcher.semantic_search(test_query, top_k=3)

        if results:
            print(f"\n✅ Encontrados: {len(results)} productos")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['title']}")
                print(f"   Reference: {result['reference']}")
                print(f"   Price: {result['price']}")
                print(f"   Score: {result['score']}")
                print(f"   Match: {result['match_reason']}")
        else:
            print("❌ No se encontraron resultados")

    searcher.close()