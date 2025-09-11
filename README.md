# 🔍 Semantic Product Search - Motor de Búsqueda Inteligente

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![FAISS](https://img.shields.io/badge/Vector-FAISS-00A98F?logo=facebook)
![SentenceTransformers](https://img.shields.io/badge/Embeddings-SentenceTransformers-FF6B6B)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit)
![SQLite](https://img.shields.io/badge/Index-SQLite_FTS5-003B57?logo=sqlite)
![License](https://img.shields.io/badge/Licencia-MIT-green)

> *"Sistema híbrido de búsqueda semántica que entiende el lenguaje natural para encontrar productos relevantes"*

## 🌟 Características Principales

### 🔬 Búsqueda Híbrida Inteligente
- **🤖 Embeddings Multilingües**: Modelos SentenceTransformers para comprensión semántica
- **🔍 BM25 + FAISS**: Combinación de búsqueda textual y vectorial
- **🎯 Re-ranking**: Reordenamiento inteligente por relevancia
- **📊 Scoring**: Puntuación 0-100 con explicaciones de coincidencia

### 🚀 Instalación Rápida
```bash
pip install -r requirements.txt
```
### ⚙️ Configuración
```bash
python build_index.py

# Ejecucion de App
streamlit run app.py
streamlit run app.py --browser.serverAddress=localhost
 ````

### 💻 Stack Tecnológico Avanzado
```mermaid
graph TB
    A[Excel Catalogo] --> B[Preprocesamiento]
    B --> C[SQLite FTS5]
    B --> D[FAISS Index]
    C --> E[BM25 Search]
    D --> F[Semantic Search]
    E --> G[Hybrid Ranking]
    F --> G
    G --> H[Streamlit UI]
```
