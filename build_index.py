from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import sqlite3
import yaml
import re
from unidecode import unidecode
import os


def preprocess_text(text):

    if pd.isna(text):
        return ""
    text = str(text)
    text = unidecode(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def build_indices():
    print("Iniciando build_indices...")

    # Verificar que el archivo existe
    current_dir = Path(__file__).parent
    file_path = current_dir / 'data' / 'catalogo_productos.xlsx'

    if not file_path.exists():
        print(f"✗ Error: El archivo {file_path} no existe")
        return

    print(f"✓ Archivo encontrado: {file_path}")

    # Cargar configuración
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Cargar datos
    df = pd.read_excel(
        'data/catalogo_productos.xlsx',
        engine='openpyxl',
        dtype=str,
        na_values=['', 'NULL', 'NaN', 'N/A']
    )

    # Preprocesar texto
    text_columns = config['data']['text_columns']
    df['search_text'] = df[text_columns].apply(
        lambda row: ' '.join([preprocess_text(row[col]) for col in text_columns]),
        axis=1
    )

    # Crear índice BM25 (SQLite FTS5)
    conn = sqlite3.connect('product_index.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
    USING fts5(reference, title, description, features, search_text)
    ''')

    # Insertar datos en FTS5
    for _, row in df.iterrows():
        cursor.execute('''
        INSERT INTO products_fts 
        (reference, title, description, features, search_text) 
        VALUES (?, ?, ?, ?, ?)
        ''', (
            str(row[config['data']['id_column']]),
            preprocess_text(row.get('titulo', '')),
            preprocess_text(row.get('descripcion', '')),
            preprocess_text(row.get('caracteristicas', '')),
            row['search_text']
        ))

    conn.commit()

    # Crear embeddings y índice FAISS
    model = SentenceTransformer(config['model']['embedding_model'])
    embeddings = model.encode(df['search_text'].tolist(), show_progress_bar=True)

    # Normalizar embeddings para cosine similarity
    faiss.normalize_L2(embeddings)

    # Crear índice FAISS
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    # Guardar índice FAISS y mapeo de IDs
    faiss.write_index(index, 'faiss_index.bin')
    df[[config['data']['id_column']]].to_csv('product_ids.csv', index=False)
    df.to_pickle('product_data.pkl')

    print("Índices construidos exitosamente!")
    print(f"Productos indexados: {len(df)}")
    print(f"Dimensión de embeddings: {embeddings.shape[1]}")

    conn.close()


if __name__ == "__main__":
    build_indices()