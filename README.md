# 🚀 Semantic Product Search

### 🧠 Motor de Búsqueda Inteligente para Catálogos de Productos

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Vector-FAISS-00A98F?logo=facebook"/>
  <img src="https://img.shields.io/badge/Embeddings-SentenceTransformers-FF6B6B"/>
  <img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit"/>
  <img src="https://img.shields.io/badge/Index-SQLite_FTS5-003B57?logo=sqlite"/>
  <img src="https://img.shields.io/badge/Licencia-MIT-green"/>
</p>

> **Sistema híbrido de búsqueda semántica que entiende el lenguaje natural para encontrar productos relevantes.**

---

## ✨ Características Principales

- 🔤 **Embeddings Multilingües:** Comprensión semántica avanzada con SentenceTransformers.
- 🧩 **Búsqueda Híbrida:** Combina BM25 (texto) y FAISS (vectorial) para máxima precisión.
- 🏆 **Re-ranking Inteligente:** Reordena resultados según relevancia real.
- 📊 **Scoring Explicativo:** Puntuación 0-100 con explicación de coincidencias.
- 🖥️ **Interfaz Intuitiva:** UI moderna y fácil de usar con Streamlit.

---

## ⚡ Instalación Rápida

```bash
pip install -r requirements.txt
```

---

## 🗺️ Arquitectura del Sistema

```mermaid
graph TD
    A[📦 Excel Catálogo] --> B[⚙️ Preprocesamiento]
    B --> C[🗄️ SQLite FTS5]
    B --> D[🔎 FAISS Index]
    C --> E[🔤 BM25 Search]
    D --> F[🧠 Semantic Search]
    E --> G[🤝 Hybrid Ranking]
    F --> G
    G --> H[🖥️ Streamlit UI]
```

---

## 📚 Licencia

Este proyecto está bajo la licencia MIT.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Siéntete libre de abrir issues o pull requests.

---