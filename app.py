import streamlit as st
import pandas as pd
import threading
from search import SemanticSearcher

_local = threading.local()


def get_searcher():

    if not hasattr(_local, 'searcher'):
        _local.searcher = SemanticSearcher()
    return _local.searcher


st.set_page_config(page_title="Búsqueda Semántica de Productos", layout="wide")

st.title("🔍 Búsqueda Semántica de Productos")
st.markdown("Herramienta para encontrar productos similares basada en descripciones de clientes")

# Entrada de texto
query = st.text_area(
    "Describe lo que necesitas:",
    height=100,
    placeholder="Ej: Necesito tornillos de acero inoxidable para exteriores, cabeza hexagonal, 10mm de diámetro..."
)

# Slider para número de resultados
top_k = st.slider("Número de resultados a mostrar:", 1, 20, 5)

# Búsqueda
if st.button("Buscar Productos") and query:
    # Obtener instancia del buscador para este thread
    searcher = get_searcher()

    with st.spinner("Buscando productos similares..."):
        results = searcher.semantic_search(query, top_k=top_k)

    if results:
        st.success(f"Encontrados {len(results)} productos relevantes")

        # Mostrar resultados
        for i, result in enumerate(results, 1):
            with st.expander(f"#{i} - {result['title']} (Score: {result['score']}/100)"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.subheader(result['title'])
                    st.write(f"**Referencia:** {result['reference']}")
                    st.write(f"**Precio:** ${result['price']}")
                    st.write(f"**Descripción:** {result['description']}")
                    if result['match_reason'] and result['match_reason'] != "Coincidencia semántica":
                        st.info(f"**Por qué coincidió:** {result['match_reason']}")
                    else:
                        st.info("**Coincidencia semántica:** El sistema encontró similitud en el significado general")

                with col2:
                    st.metric("Similitud", f"{result['score']:.1f}")
                    # Barra de progreso visual
                    st.progress(result['score'] / 100)

                    # Indicador de calidad de coincidencia
                    if result['score'] >= 90:
                        st.success("⭐ Excelente coincidencia")
                    elif result['score'] >= 70:
                        st.success("✓ Buena coincidencia")
                    elif result['score'] >= 50:
                        st.warning("↗ Coincidencia aceptable")
                    else:
                        st.info("↘ Coincidencia débil")

        # Tabla resumen
        st.subheader("📊 Resumen de resultados")
        summary_data = []
        for result in results:
            summary_data.append({
                'Producto': result['title'],
                'Referencia': result['reference'],
                'Precio': result['price'],
                'Score': f"{result['score']:.1f}"
            })

        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

    else:
        st.warning("No se encontraron productos que coincidan con tu búsqueda")
        st.info("💡 Sugerencia: Intenta usar términos más generales o describe el producto de otra manera")

# Información adicional
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Cómo funciona:**
    1. Escribe lo que necesitas en tus propias palabras
    2. El sistema busca coincidencias semánticas
    3. Los resultados se ordenan por relevancia

    **Tecnología utilizada:**
    - 🤖 Modelos de embeddings multilingües
    - 🔍 Búsqueda híbrida (BM25 + Semántica)
    - 📊 Re-ranking inteligente

    **Score de similitud:**
    - 🟢 90-100: Coincidencia excelente
    - 🟡 70-89: Coincidencia muy buena  
    - 🟠 50-69: Coincidencia aceptable
    - 🔴 <50: Coincidencia débil
    """)

    # Estadísticas del sistema (usamos una instancia temporal)
    try:
        temp_searcher = SemanticSearcher()
        st.header("📈 Estadísticas")
        st.write(f"**Productos indexados:** {len(temp_searcher.product_data)}")
        st.write(f"**Modelo de embeddings:** {temp_searcher.config['model']['embedding_model'].split('/')[-1]}")
        st.write(f"**Dimensiones:** {temp_searcher.faiss_index.d}")
        temp_searcher.close()
    except:
        st.write("**Estadísticas:** No disponibles")

# Ejemplo de búsquedas sugeridas
with st.sidebar:
    st.header("💡 Ejemplos de búsqueda")
    examples = [
        "tornillos acero inoxidable",
        "herramientas electricas profesionales",
        "materiales construcción resistentes",
        "productos para jardinería",
        "equipos de seguridad industrial"
    ]

    for example in examples:
        if st.button(f"\"{example}\"", key=f"example_{example}"):
            st.session_state.query = example
            st.rerun()

# CSS personalizado para mejor apariencia
st.markdown("""
<style>
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stExpander > div:first-child {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px 10px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# Limpieza al cerrar la aplicación
import atexit


@atexit.register
def cleanup():
    if hasattr(_local, 'searcher'):
        _local.searcher.close()