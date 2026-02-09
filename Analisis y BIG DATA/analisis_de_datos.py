import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

st.set_page_config(page_title="Analizador Interactivo Mejorado", layout="wide")

st.title("Analizador Interactivo y Mejorado con Limpieza Automática")

def limpiar_y_maquetar(df: pd.DataFrame) -> pd.DataFrame:
    # Eliminar filas completamente vacías
    df = df.dropna(how='all')

    # Detectar encabezado correcto si las columnas tienen muchos 'Unnamed'
    if df.columns.str.contains('Unnamed').sum() > len(df.columns) // 2:
        for i in range(min(3, len(df))):  # revisar primeras 3 filas
            if df.iloc[i].notna().sum() > len(df.columns) / 2:
                df.columns = df.iloc[i]
                df = df.drop(index=range(i+1))
                break

    # Quitar columnas con nombre Unnamed o vacío
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Resetear índice
    df = df.reset_index(drop=True)

    # Opcional: rellenar NaNs en columnas clave si quieres
    # df['Proyecto'] = df['Proyecto'].fillna('No especificado')

    return df

uploaded_file = st.file_uploader(
    "Sube tu archivo (Excel, CSV, TSV)", type=["xlsx", "xls", "csv", "tsv"]
)

if uploaded_file is not None:
    file_type = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_type in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        elif file_type == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_type == 'tsv':
            df = pd.read_csv(uploaded_file, sep='\t')
        else:
            st.error("Formato no soportado.")
            st.stop()
    except Exception as e:
        st.error(f"Error leyendo archivo: {e}")
        st.stop()

    df = limpiar_y_maquetar(df)

    if df.empty:
        st.warning("Archivo vacío o sin datos útiles después de limpiar.")
        st.stop()

    st.subheader("Vista previa de datos")
    st.dataframe(df.head())

    columnas_objeto = df.select_dtypes(include=['object']).columns.tolist()
    columnas_numericas = df.select_dtypes(include=['number', 'timedelta']).columns.tolist()
    columnas_fecha = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()

    if not columnas_fecha and columnas_objeto:
        to_datetime_cols = st.multiselect("Convertir columnas a fecha (opcional)", columnas_objeto)
        for col in to_datetime_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        columnas_fecha = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()

    st.sidebar.header("Filtros mejorados")
    filtros = dict()

    # Multi-selección texto y fechas
    for col in columnas_objeto + columnas_fecha:
        opciones_raw = df[col].dropna().astype(str).unique().tolist()
        opciones = sorted(opciones_raw)
        seleccion = st.sidebar.multiselect(f"Filtrar por {col}", opciones, default=opciones)
        if seleccion and len(seleccion) < len(opciones):
            filtros[col] = seleccion

    columnas_numericas_real = []
    for col in columnas_numericas:
        if np.issubdtype(df[col].dtype, np.timedelta64):
            df[col + '_seg'] = df[col].dt.total_seconds()
            columnas_numericas_real.append(col + '_seg')
        else:
            columnas_numericas_real.append(col)

    for col in columnas_numericas_real:
        col_data = df[col].dropna()
        if col_data.empty:
            continue
        min_val = col_data.min()
        max_val = col_data.max()
        rango = st.sidebar.slider(
            f"Rango para {col.replace('_seg', ' (segundos)')}",
            float(min_val), float(max_val),
            (float(min_val), float(max_val))
        )
        filtros[col] = rango

    df_filtrado = df.copy()
    for col, vals in filtros.items():
        if col in columnas_objeto + columnas_fecha:
            df_filtrado = df_filtrado[df_filtrado[col].astype(str).isin(vals)]
        else:
            df_filtrado = df_filtrado[(df_filtrado[col] >= vals[0]) & (df_filtrado[col] <= vals[1])]

    st.subheader(f"Datos filtrados - {len(df_filtrado)} filas")
    st.dataframe(df_filtrado)

    st.subheader("Métricas principales")
    if columnas_numericas_real:
        col1, col2 = st.columns(2)
        with col1:
            for col in columnas_numericas_real[:len(columnas_numericas_real)//2 + 1]:
                val = df_filtrado[col].sum() if not df_filtrado.empty else 0
                st.metric(f"Suma {col.replace('_seg',' (segundos)')}", round(val, 2))
        with col2:
            for col in columnas_numericas_real[len(columnas_numericas_real)//2 + 1:]:
                val = df_filtrado[col].mean() if not df_filtrado.empty else 0
                st.metric(f"Promedio {col.replace('_seg',' (segundos)')}", round(val, 2))

    st.subheader("Visualización")
    if not df_filtrado.empty and columnas_objeto and columnas_numericas_real:
        cat_col = columnas_objeto[0]
        num_col = columnas_numericas_real[0]
        resumen = df_filtrado.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
        if not resumen.empty:
            fig, ax = plt.subplots(figsize=(8,4))
            resumen.plot(kind='bar', ax=ax, color='cornflowerblue')
            ax.set_ylabel(num_col.replace('_seg', ' (segundos)'))
            ax.set_xlabel(cat_col)
            ax.set_title(f"Suma de {num_col.replace('_seg', ' (segundos)')} por {cat_col}")
            st.pyplot(fig)
        else:
            st.info("No hay datos para graficar con los filtros actuales.")

    st.subheader("Clustering")
    cols_cluster = st.multiselect("Columnas numéricas para clustering (mínimo 2)", columnas_numericas_real)
    if len(cols_cluster) >= 2 and not df_filtrado.empty:
        data_cluster = df_filtrado[cols_cluster].dropna()
        if len(data_cluster) > 0:
            pca = PCA(n_components=2)
            pca_res = pca.fit_transform(data_cluster)

            n_clusters = st.slider("Número de clusters", 2, 6, 3)
            kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
            clusters = kmeans.fit_predict(data_cluster)

            fig2, ax2 = plt.subplots(figsize=(8,5))
            scatter = ax2.scatter(pca_res[:,0], pca_res[:,1], c=clusters, cmap='viridis', alpha=0.7)
            legend = ax2.legend(*scatter.legend_elements(), title="Clusters")
            ax2.add_artist(legend)
            ax2.set_xlabel("PCA 1")
            ax2.set_ylabel("PCA 2")
            ax2.set_title("Clustering con PCA 2D")
            st.pyplot(fig2)
        else:
            st.info("No hay suficientes datos para clustering tras filtrar.")
    else:
        st.info("Selecciona al menos 2 columnas numéricas para clustering.")

    st.subheader("Exportar resultados filtrados")
    formato = st.selectbox("Formato de exportación", ["Excel (.xlsx)", "CSV (.csv)"])
    towrite = io.BytesIO()
    if formato == "Excel (.xlsx)":
        df_filtrado.to_excel(towrite, index=False)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        nombre = "datos_filtrados.xlsx"
    else:
        towrite_str = io.StringIO()
        df_filtrado.to_csv(towrite_str, index=False)
        mime = "text/csv"
        nombre = "datos_filtrados.csv"

    st.download_button(
        "Descargar archivo filtrado",
        data=towrite if formato.startswith("Excel") else towrite_str.getvalue(),
        file_name=nombre,
        mime=mime,
    )

else:
    st.info("Sube un archivo para comenzar a analizar tus datos. Soporta Excel, CSV y TSV.")
