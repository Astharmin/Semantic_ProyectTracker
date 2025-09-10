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

    # Verificar archivo de configuración y leerlo
    config_path = Path(__file__).parent / 'config.yaml'
    if not config_path.exists():
        print(f"✗ Error: El archivo de configuración {config_path} no existe")
        return

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Leer parámetros desde config
    excel_path = Path(__file__).parent / config['data']['excel_path']
    sheet_name = config['data'].get('sheet_name', 0)
    id_column = config['data']['id_column']
    text_columns = config['data']['text_columns']

    # Verificar que el archivo existe
    if not excel_path.exists():
        print(f"✗ Error: El archivo {excel_path} no existe")
        return
    print(f"✓ Archivo encontrado: {excel_path}")

    # Cargar datos
    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        engine='openpyxl',
        dtype=str,
        na_values=['', 'NULL', 'NaN', 'N/A']
    )

    # Mostrar columnas reales
    print(f"Columnas encontradas en el archivo Excel: {df.columns.tolist()}")

    # Preprocesar texto
    for col in text_columns:
        if col not in df.columns:
            print(f"✗ Error: La columna '{col}' no está en el archivo Excel.")
            return

    field_translations = {
        'price': 'precio',
        'reference': 'referencia',
        'features': 'caracteristicas',
        'category': 'categoria',
        'description': 'descripcion'
    }

    df['search_text'] = df[text_columns].apply(
        lambda row: ' '.join([
            preprocess_text(row[col]) + ' ' +
            preprocess_text(col) + ' ' +
            preprocess_text(field_translations.get(col, col))
            for col in text_columns
        ]),
        axis=1
    )

    # Crear índice BM25 (SQLite FTS5)
    conn = sqlite3.connect('product_index.db')
    cursor = conn.cursor()

    # Ajusta las columnas de la tabla FTS5 de acuerdo a los text_columns
    fts_columns = ', '.join(text_columns + ['search_text'])
    cursor.execute(f'''
    CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
    USING fts5({fts_columns})
    ''')

    # Insertar datos en FTS5 usando sólo columnas que existan
    for _, row in df.iterrows():
        values = [str(row.get(col, "")) for col in text_columns]
        values.append(row['search_text'])
        placeholders = ', '.join(['?'] * len(values))
        cursor.execute(f'''
        INSERT INTO products_fts 
        ({', '.join(text_columns)}, search_text) 
        VALUES ({placeholders})
        ''', values)

    conn.commit()

    # Crear embeddings y FAISS
    model = SentenceTransformer(config['model']['embedding_model'])
    embeddings = model.encode(df['search_text'].tolist(), show_progress_bar=True)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, 'faiss_index.bin')
    df[[id_column]].to_csv('product_ids.csv', index=False)
    df.to_pickle('product_data.pkl')

    print("Índices construidos exitosamente!")
    print(f"Productos indexados: {len(df)}")
    print(f"Dimensión de embeddings: {embeddings.shape[1]}")

    conn.close()

if __name__ == "__main__":
    build_indices()