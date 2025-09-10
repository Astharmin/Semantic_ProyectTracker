import streamlit as st
import pandas as pd
from search import searcher

st.set_page_config(page_title="Búsqueda Semántica de Productos", layout="wide")

st.title("🔍 Búsqueda Semántica de Productos")
st.markdown("Herramienta para encontrar productos similares basada en descripciones de clientes")

# Entrada de texto
query = st.text_area(
    "Describe lo que necesitas:",
    height=100,
    placeholder="Ej: Necesito tornillos de acero inoxidable para exteriores, cabeza hexagonal, 10mm de diámetro..."
)

# Búsqueda
if st.button("Buscar Productos") and query:
    with st.spinner("Buscando productos similares..."):
        results = searcher.semantic_search(query)

    if results:
        st.success(f"Encontrados {len(results)} productos relevantes")

        # Mostrar resultados
        for i, result in enumerate(results, 1):
            with st.expander(f"#{i} - {result['title']} (Score: {result['score']}/100)"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.subheader(result['title'])
                    st.write(f"**Referencia:** {result['reference']}")
                    st.write(f"**Precio:** ${result['price'] if result['price'] else 'N/A'}")
                    st.write(f"**Descripción:** {result['description']}")
                    if result['match_reason']:
                        st.info(f"**Por qué coincidió:** {result['match_reason']}")

                with col2:
                    st.metric("Similitud", f"{result['score']}/100")
    else:
        st.warning("No se encontraron productos que coincidan con tu búsqueda")

# Información adicional
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Cómo funciona:**
    1. Escribe lo que necesitas en tus propias palabras
    2. El sistema busca coincidencias semánticas
    3. Los resultados se ordenan por relevancia

    **Campos analizados:**
    - Título del producto
    - Descripción
    - Características técnicas

    **Score de similitud:**
    - 90-100: Coincidencia excelente
    - 70-89: Coincidencia muy buena
    - 50-69: Coincidencia aceptable
    - <50: Coincidencia débil
    """)

# Cerrar conexión al final
import atexit

atexit.register(searcher.close)