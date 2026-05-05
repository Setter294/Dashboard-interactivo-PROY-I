"""
================================================================================
 Dashboard interactivo — Evolución del empleo en el sector tecnológico de EEUU
 Proyecto I — Grado en Ciencia de Datos | UPV ETSINF | Curso 2025-26
--------------------------------------------------------------------------------
 Esta aplicación Streamlit replica la lógica de preprocesamiento y las
 visualizaciones principales del notebook `analisis_completo_comentado.ipynb`,
 envolviéndolas en una interfaz interactiva con filtros, KPIs y tablas.

 Versión 3:
   • Toggle de contexto histórico
   • KPI delta interanual
   • Boxplot por empresa (CON Amazon)
   • Heatmap empresa × año (variación neta) — sustituye al de correlaciones
   • Títulos limpios sin prefijos "Figura X"
================================================================================
"""

# ─── Importación de librerías ─────────────────────────────────────────────────
import pandas as pd                       # Manipulación de DataFrames
import numpy as np                        # Operaciones numéricas
import streamlit as st                    # Framework web del dashboard
import plotly.graph_objects as go         # Gráficas interactivas (low-level)
import warnings
warnings.filterwarnings('ignore')


# ══════════════════════════════════════════════════════════════════════════════
#  1. CONFIGURACIÓN GLOBAL Y PALETA DE COLORES
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Empleo Tech EEUU 2001-2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Paleta de colores (idéntica al notebook) ────────────────────────────────
BLUE   = '#2166AC'   # Azul: crecimiento, tendencias positivas
RED    = '#B2182B'   # Rojo: reducción, resultados negativos
GREEN  = '#4DAC26'   # Verde: crecimiento neto positivo
PURPLE = '#762A83'   # Morado: empresas pequeñas
GOLD   = '#D4A017'   # Dorado: empresas maduras


# ─── CSS personalizado para reforzar el tema oscuro ──────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    section[data-testid="stSidebar"] { background-color: #1A1D24; }

    /* Etiquetas (tags) del multiselect en rojo, como en la imagen */
    span[data-baseweb="tag"] {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #FF4B4B !important;
    }

    div[data-testid="stMetricValue"] { font-size: 2.4rem; font-weight: 600; }
    div[data-testid="stMetricLabel"] { font-size: 0.95rem; opacity: 0.85; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  2. CARGA Y PREPROCESAMIENTO DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def cargar_y_procesar_datos(ruta_csv: str = 'tech_employment_2000_2025.csv') -> pd.DataFrame:
    """
    Carga el CSV y aplica EXACTAMENTE el mismo preprocesamiento que el notebook:
      1. Lectura con sep=';' y decimal=','  (formato Statgraphics-compatible).
         Si la cabecera no tiene la forma esperada, fallback a sep=',', decimal='.'.
      2. Creación de las variables: tamanyo_empresa, categoria_empresa, periodo.
      3. Transformaciones logarítmicas para manejar la escala de Amazon.
    """
    # ── Carga primaria con parámetros del notebook ───────────────────────────
    df = pd.read_csv(ruta_csv, sep=';', decimal=',')
    if df.shape[1] <= 1:                         # Fallback a formato estándar
        df = pd.read_csv(ruta_csv, sep=',', decimal='.')

    # ── Variable 1: Tamaño de empresa según plantilla inicial ───────────────
    df['tamanyo_empresa'] = pd.cut(
        df['employees_start'],
        bins=[0, 5000, 50000, 200000, float('inf')],
        labels=['Pequeña (<5k)', 'Media (5k-50k)',
                'Grande (50k-200k)', 'Gigante (>200k)']
    )

    # ── Variable 2: Categoría según antigüedad de la empresa ─────────────────
    anyo_fundacion = {
        'Intel': 1968, 'AMD': 1969, 'SAP': 1972, 'Microsoft': 1975, 'Apple': 1976,
        'Oracle': 1977, 'Adobe': 1982, 'NVIDIA': 1993, 'Amazon': 1994, 'Netflix': 1997,
        'PayPal': 1998, 'Salesforce': 1999, 'LinkedIn': 2003, 'Tesla': 2003,
        'Alphabet': 2004, 'Meta': 2004, 'Shopify': 2004, 'X (Twitter)': 2006,
        'Airbnb': 2008, 'Uber': 2009, 'Block': 2009, 'Pinterest': 2010,
        'Stripe': 2010, 'Snap': 2011, 'Lyft': 2012,
    }

    def categorizar(company, year):
        f = anyo_fundacion.get(company, year)
        antiguedad = year - f
        if antiguedad >= 20:   return 'Consolidada (>20a)'
        elif antiguedad >= 10: return 'Madura (10-20a)'
        else:                  return 'Joven (<10a)'

    df['categoria_empresa'] = df.apply(
        lambda r: categorizar(r['company'], r['year']), axis=1
    )

    # ── Variable 3: Periodo histórico ────────────────────────────────────────
    def get_periodo(y):
        if y <= 2003:   return '01-03: Burbuja puntocom'
        elif y <= 2007: return '04-07: Recuperación'
        elif y <= 2010: return '08-10: Crisis financiera'
        elif y <= 2019: return '11-19: Boom digital'
        elif y <= 2021: return '20-21: Boom COVID'
        else:           return '22-25: Ajuste post-COVID'

    df['periodo'] = df['year'].apply(get_periodo)

    # ── Variable 4: Transformaciones logarítmicas (para Amazon) ─────────────
    # sign(x)*log1p(|x|) preserva el signo y evita log(0).
    for v in ['net_change', 'layoffs', 'new_hires', 'revenue_billions_usd']:
        df[v + '_log'] = np.sign(df[v]) * np.log1p(np.abs(df[v]))

    return df


df = cargar_y_procesar_datos()


# ══════════════════════════════════════════════════════════════════════════════
#  3. SIDEBAR — FILTROS DEL PROYECTO
# ══════════════════════════════════════════════════════════════════════════════

st.sidebar.title("Filtros del Proyecto")

# ── Filtro 1: selector múltiple de empresas ──────────────────────────────────
todas_empresas = sorted(df['company'].unique().tolist())
empresas_sel = st.sidebar.multiselect(
    "Selecciona Empresas:",
    options=todas_empresas,
    default=todas_empresas,
    help="Puedes seleccionar varias empresas simultáneamente."
)

# ── Filtro 2: slider de rango de años ───────────────────────────────────────
anyo_min, anyo_max = int(df['year'].min()), int(df['year'].max())
rango_anyos = st.sidebar.slider(
    "Rango de Años:",
    min_value=anyo_min, max_value=anyo_max,
    value=(anyo_min, anyo_max), step=1
)

# ── Toggle para mostrar/ocultar el contexto histórico ───────────────────────
# Controla las zonas sombreadas (puntocom, crisis, COVID...) en las gráficas
# de evolución temporal. ON → fondo con franjas; OFF → fondo limpio.
mostrar_contexto = st.sidebar.toggle(
    "Mostrar contexto histórico",
    value=True,
    help="Activa o desactiva las franjas de los periodos históricos clave "
         "(burbuja puntocom, crisis financiera, boom COVID, ajuste post-COVID)."
)

# ── Información adicional ───────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Acerca del dataset")
st.sidebar.markdown(
    f"- **Empresas totales:** {df['company'].nunique()}\n"
    f"- **Periodo completo:** {anyo_min}–{anyo_max}\n"
    f"- **Observaciones:** {len(df):,}"
)


# ── Aplicación de los filtros ────────────────────────────────────────────────
if not empresas_sel:
    st.warning("⚠️ Por favor, selecciona al menos una empresa en la barra lateral.")
    st.stop()

mask = (
    df['company'].isin(empresas_sel) &
    df['year'].between(rango_anyos[0], rango_anyos[1])
)
df_filt = df.loc[mask].copy()

if df_filt.empty:
    st.warning("⚠️ No hay datos para la combinación de filtros seleccionada.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  4. ENCABEZADO Y KPIs SUPERIORES
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(
    f"#### Proyecto I — Grado en Ciencia de Datos. "
    f"Análisis del periodo **{rango_anyos[0]} - {rango_anyos[1]}**"
)

col1, col2, col3, col4 = st.columns(4)

# ── KPI 1: Total Despidos ────────────────────────────────────────────────────
total_despidos = int(df_filt['layoffs'].sum())
col1.metric(
    label="Total Despidos",
    value=f"{total_despidos:,}".replace(",", ".")
)

# ── KPI 2: Tasa de Contratación Media ────────────────────────────────────────
tasa_contratacion_media = df_filt['hiring_rate_pct'].mean()
col2.metric(
    label="Tasa Contratación Media",
    value=f"{tasa_contratacion_media:.2f}%"
)

# ── KPI 3: Récord de ingresos ────────────────────────────────────────────────
record_ingresos = df_filt['revenue_billions_usd'].max()
col3.metric(
    label="Récord Ingresos",
    value=f"${record_ingresos:.2f}B"
)

# ── KPI 4: Cambio Neto Empleos — DELTA INTERANUAL ───────────────────────────
# El delta compara la variación neta del ÚLTIMO año del rango frente al
# año inmediatamente anterior. Si el rango contiene un solo año, se omite.
cambio_neto = int(df_filt['net_change'].sum())
nc_por_anyo = df_filt.groupby('year')['net_change'].sum().sort_index()

if len(nc_por_anyo) >= 2:
    ultimo_anyo  = int(nc_por_anyo.index[-1])
    anyo_previo  = int(nc_por_anyo.index[-2])
    delta_valor  = int(nc_por_anyo.iloc[-1] - nc_por_anyo.iloc[-2])
    delta_str    = f"{delta_valor:+,} ({anyo_previo}→{ultimo_anyo})".replace(",", ".")

    col4.metric(
        label="Cambio Neto Empleos",
        value=f"{cambio_neto:,}".replace(",", "."),
        delta=delta_str,
        help=f"Delta = variación neta de {ultimo_anyo} menos la de {anyo_previo}."
    )
else:
    col4.metric(
        label="Cambio Neto Empleos",
        value=f"{cambio_neto:,}".replace(",", ".")
    )

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  5. GRÁFICAS DE EVOLUCIÓN — VARIACIÓN NETA Y CONTRATACIONES vs DESPIDOS
# ══════════════════════════════════════════════════════════════════════════════

# ── Agregación anual sobre el filtro ────────────────────────────────────────
anual = df_filt.groupby('year').agg(
    net_change=('net_change', 'sum'),
    new_hires=('new_hires',  'sum'),
    layoffs=('layoffs',    'sum'),
).reset_index()

# ── Periodos históricos (idénticos al notebook) ─────────────────────────────
periodos_zoom = [
    (2001, 2003, 'Burbuja puntocom & 11-S', '#FFD700'),
    (2008, 2010, 'Crisis financiera',       '#FFA07A'),
    (2020, 2021, 'Boom COVID',              '#90EE90'),
    (2022, 2024, 'Ajuste post-COVID',       '#FFB6C1'),
]


def anyadir_zonas_historicas(fig, y_etiqueta=None, mostrar_etiquetas=False):
    """
    Añade rectángulos verticales (axvspan) a la figura SOLO si el toggle
    `mostrar_contexto` está activado. Si está desactivado, no hace nada
    y el fondo queda limpio.
    """
    if not mostrar_contexto:
        return
    for ini, fin, lbl, color in periodos_zoom:
        if fin < rango_anyos[0] or ini > rango_anyos[1]:
            continue
        fig.add_vrect(
            x0=ini - 0.5, x1=fin + 0.5,
            fillcolor=color, opacity=0.13,
            layer="below", line_width=0,
        )
        if mostrar_etiquetas and y_etiqueta is not None:
            fig.add_annotation(
                x=(ini + fin) / 2, y=y_etiqueta,
                text=lbl, showarrow=False,
                font=dict(size=9, color="black"),
                bgcolor=color, opacity=0.85,
                bordercolor=color, xanchor='center',
            )


col_g1, col_g2 = st.columns(2)

# ──────────────────────────────────────────────────────────────────────────────
#  Variación neta anual (barras)
# ──────────────────────────────────────────────────────────────────────────────
with col_g1:
    st.markdown("### Variación neta anual")
    st.caption(
        "Suma agregada de las empresas seleccionadas. "
        "Verde = crecimiento; Rojo = reducción."
    )

    colors_nc = [GREEN if v >= 0 else RED for v in anual['net_change']]

    fig1a = go.Figure()
    fig1a.add_trace(go.Bar(
        x=anual['year'],
        y=anual['net_change'] / 1000,
        marker_color=colors_nc,
        marker_line_width=0,
        opacity=0.85,
        name='Variación neta',
        hovertemplate='<b>Año %{x}</b><br>Variación neta: %{y:.1f}k<extra></extra>',
    ))
    fig1a.add_hline(y=0, line_color='#888', line_width=1)
    anyadir_zonas_historicas(fig1a)

    fig1a.update_layout(
        template='plotly_dark',
        height=480,
        margin=dict(l=10, r=10, t=20, b=40),
        xaxis_title='Año',
        yaxis_title='Variación neta (miles de empleados)',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig1a, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
#  Contrataciones vs Despidos (líneas con relleno)
# ──────────────────────────────────────────────────────────────────────────────
with col_g2:
    st.markdown("### Contrataciones vs Despidos")
    st.caption(
        "Áreas rellenas con líneas superpuestas. El cruce de curvas indica "
        "los años en los que los despidos superan a las contrataciones."
    )

    fig1b = go.Figure()

    fig1b.add_trace(go.Scatter(
        x=anual['year'], y=anual['new_hires'] / 1000,
        mode='lines',
        line=dict(color=BLUE, width=2.5),
        fill='tozeroy',
        fillcolor='rgba(33, 102, 172, 0.35)',
        name='Nuevas contrataciones',
        hovertemplate='<b>Año %{x}</b><br>Contrataciones: %{y:.1f}k<extra></extra>',
    ))
    fig1b.add_trace(go.Scatter(
        x=anual['year'], y=anual['layoffs'] / 1000,
        mode='lines',
        line=dict(color=RED, width=2.5),
        fill='tozeroy',
        fillcolor='rgba(178, 24, 43, 0.45)',
        name='Despidos',
        hovertemplate='<b>Año %{x}</b><br>Despidos: %{y:.1f}k<extra></extra>',
    ))

    y_max = max(anual['new_hires'].max(), anual['layoffs'].max()) / 1000
    y_etiqueta = y_max * 0.92 if y_max > 0 else 30

    anyadir_zonas_historicas(
        fig1b, y_etiqueta=y_etiqueta, mostrar_etiquetas=True
    )

    fig1b.update_layout(
        template='plotly_dark',
        height=480,
        margin=dict(l=10, r=10, t=20, b=40),
        xaxis_title='Año',
        yaxis_title='Empleados (miles)',
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='right', x=1,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig1b, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  6. BOXPLOT POR EMPRESA — ✨ AHORA INCLUYE AMAZON
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### Distribución de la variación neta por empresa")
st.caption(
    "Boxplot con cajas azul claro, mediana roja gruesa y outliers en rojo. "
    "Empresas ordenadas de mayor a menor mediana de variación neta."
)

# ── ✨ Subconjunto INCLUYENDO Amazon: usamos directamente el filtro general ─
# Antes: df_sin = df_filt[df_filt['company'] != 'Amazon']
# Ahora: df_plot = df_filt (todas las empresas seleccionadas, sin excluir Amazon)
df_plot = df_filt.copy()

if df_plot.empty:
    st.info("ℹ️ No hay datos para mostrar con los filtros actuales.")
else:
    # ── Mediana de net_change por empresa, en miles, ordenada descendente ───
    medianas_emp = (
        df_plot.groupby('company')['net_change']
               .median()
               .div(1000)                           # Pasamos a miles
               .sort_values(ascending=False)        # Mayor → menor mediana
    )
    orden_empresas = medianas_emp.index.tolist()

    fig_box = go.Figure()

    # ── Una caja Plotly por empresa, en el orden establecido ────────────────
    # NOTA: en Plotly, `line.color` controla simultáneamente el contorno de la
    # caja Y la línea de la mediana. Para conseguir "borde azul + mediana roja"
    # ponemos el contorno azul y luego superponemos la mediana roja con
    # `add_shape()` (workaround estándar).
    for empresa in orden_empresas:
        datos = df_plot.loc[df_plot['company'] == empresa, 'net_change'] / 1000
        fig_box.add_trace(go.Box(
            y=datos,
            name=empresa,
            fillcolor='#D6E8F5',                   # Cajas azul claro
            line=dict(color=BLUE, width=1.5),      # Borde azul oscuro
            marker=dict(
                color='red', size=5,
                line=dict(color='red', width=0.5),
                outliercolor='red',                # Outliers rojos
            ),
            boxpoints='outliers',                  # Solo se ven los outliers
            showlegend=False,
            hovertemplate=(
                f'<b>{empresa}</b><br>'
                'Variación neta: %{y:.2f}k<extra></extra>'
            ),
        ))

    # ── Línea roja gruesa SOBRE cada mediana (workaround Plotly) ────────────
    # Las cajas categóricas ocupan posiciones 0, 1, 2, ... en el eje X.
    for i, empresa in enumerate(orden_empresas):
        mediana = medianas_emp[empresa]
        fig_box.add_shape(
            type='line',
            xref='x', yref='y',
            x0=i - 0.35, x1=i + 0.35,
            y0=mediana,  y1=mediana,
            line=dict(color='red', width=3),       # Mediana roja y gruesa
            layer='above',
        )

    # Línea horizontal en y=0 para referencia visual
    fig_box.add_hline(y=0, line_color='#888', line_width=1, line_dash='dot')

    fig_box.update_layout(
        template='plotly_dark',
        height=520,
        margin=dict(l=10, r=10, t=20, b=80),
        xaxis_title='Empresa',
        yaxis_title='Variación neta (miles de empleados)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_box, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  7. ✨ NUEVO HEATMAP — VARIACIÓN NETA POR EMPRESA Y AÑO
# ══════════════════════════════════════════════════════════════════════════════
#
#  Sustituye al anterior heatmap de correlaciones. Es la traducción a Plotly
#  del mapa de calor de la celda 9 del notebook (empresa × año, con el orden
#  de empresas según media histórica descendente).
#
#  La escala se cierra entre -10 y +10 (miles) para que los años extremos de
#  Amazon no decoloren el resto: cualquier valor por encima de +10 satura en
#  azul oscuro y por debajo de -10 satura en rojo oscuro.
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### Mapa de calor: variación neta por empresa y año")
st.caption(
    "Cada celda muestra la variación neta anual de empleados (en miles). "
    "Empresas ordenadas por media histórica descendente. "
    "Azul = crecimiento; Rojo = reducción. Escala saturada en ±10k."
)

# ── Tabla pivotada: empresa en filas, año en columnas ───────────────────────
# pivot_table reorganiza el DataFrame para que cada fila sea una empresa
# y cada columna sea un año. El valor de cada celda es la suma de net_change.
pivot = df_filt.pivot_table(
    index='company',
    columns='year',
    values='net_change',
    aggfunc='sum',
)

# Pasamos a miles para mostrar en la misma escala que el resto del dashboard
pivot_k = pivot / 1000

# ── Orden de las empresas: por MEDIA HISTÓRICA descendente ──────────────────
# Las empresas con mayor crecimiento promedio van arriba.
# pivot.mean(axis=1) ignora NaN automáticamente (años sin datos).
orden_companies = pivot_k.mean(axis=1).sort_values(ascending=False).index.tolist()
pivot_k = pivot_k.loc[orden_companies]

# ── Heatmap Plotly ──────────────────────────────────────────────────────────
# colorscale='RdBu_r': red→white→blue (negativo→cero→positivo).
# zmin/zmax cerrados a ±10 para evitar que Amazon decolore todo el mapa.
# zmid=0 garantiza que el blanco corresponda exactamente al cero.
fig_hm = go.Figure(data=go.Heatmap(
    z=pivot_k.values,
    x=pivot_k.columns.astype(str),                 # Años como categorías
    y=pivot_k.index,                               # Empresas
    colorscale='RdBu_r',                           # Rojo (neg) → Azul (pos)
    zmin=-10, zmax=10, zmid=0,                     # Escala saturada en ±10k
    hovertemplate=(
        '<b>%{y}</b> · Año %{x}<br>'
        'Variación neta: %{z:.2f}k empleados<extra></extra>'
    ),
    hoverongaps=False,                             # No tooltip en celdas vacías
    colorbar=dict(
        title=dict(text='Var. neta<br>(miles)', side='right'),
        thickness=15, len=0.85,
        tickvals=[-10, -5, 0, 5, 10],
        ticktext=['≤-10', '-5', '0', '+5', '≥+10'],
    ),
    xgap=1, ygap=1,                                # Mínima separación visual
))

# Calculamos altura dinámica: ~22 px por empresa, mínimo 400 px.
n_empresas = len(pivot_k.index)
altura_hm = max(400, 28 * n_empresas)

fig_hm.update_layout(
    template='plotly_dark',
    height=altura_hm,
    margin=dict(l=10, r=10, t=20, b=40),
    xaxis=dict(title='Año', side='bottom'),
    yaxis=dict(title='Empresa', autorange='reversed'),  # Mayor crecim. arriba
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
st.plotly_chart(fig_hm, use_container_width=True)

# ── Insights del notebook (interpretación del heatmap) ──────────────────────
st.info(
    "**📌 Insights clave del mapa de calor**\n\n"
    "1. **Amazon domina en crecimiento absoluto** durante 2010–2021, "
    "justificando su tratamiento diferenciado en análisis estadísticos.\n\n"
    "2. **Las crisis de 2001–2003 y 2008–2010** afectan principalmente a las "
    "empresas maduras (Intel, AMD, Microsoft, Oracle).\n\n"
    "3. **El ajuste de 2022–2023** es el más transversal: afecta simultáneamente "
    "a empresas de todos los tamaños, siendo el episodio más sistémico del periodo."
)


# ══════════════════════════════════════════════════════════════════════════════
#  8. ANÁLISIS EXTRA — TOP 5 CRECIMIENTO/REDUCCIÓN Y TABLA FILTRABLE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 📈 Análisis adicional")

ranking_empresas = (
    df_filt.groupby('company')['net_change']
           .sum()
           .sort_values(ascending=False)
)

col_top1, col_top2 = st.columns(2)

with col_top1:
    st.markdown("### 🏆 Top 5 empresas por crecimiento")
    top5_crec = (
        ranking_empresas.head(5)
        .reset_index()
        .rename(columns={'company': 'Empresa', 'net_change': 'Cambio neto'})
    )
    top5_crec['Cambio neto'] = top5_crec['Cambio neto'].map(
        lambda x: f"{int(x):,}".replace(",", ".")
    )
    st.dataframe(top5_crec, use_container_width=True, hide_index=True)

with col_top2:
    st.markdown("### 📉 Top 5 empresas por reducción")
    top5_red = (
        ranking_empresas.tail(5).sort_values()
        .reset_index()
        .rename(columns={'company': 'Empresa', 'net_change': 'Cambio neto'})
    )
    top5_red['Cambio neto'] = top5_red['Cambio neto'].map(
        lambda x: f"{int(x):,}".replace(",", ".")
    )
    st.dataframe(top5_red, use_container_width=True, hide_index=True)


# ── Tabla filtrable y descarga ──────────────────────────────────────────────
st.markdown("### 📋 Datos detallados (filtrables)")

cols_tabla = [
    'company', 'year', 'employees_start', 'employees_end',
    'new_hires', 'layoffs', 'net_change',
    'hiring_rate_pct', 'attrition_rate_pct',
    'revenue_billions_usd', 'tamanyo_empresa',
    'categoria_empresa', 'periodo'
]

st.dataframe(
    df_filt[cols_tabla].sort_values(['company', 'year']).reset_index(drop=True),
    use_container_width=True, height=380, hide_index=True,
)

csv_bytes = df_filt[cols_tabla].to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Descargar datos filtrados (CSV)",
    data=csv_bytes,
    file_name=f"empleo_tech_{rango_anyos[0]}_{rango_anyos[1]}.csv",
    mime="text/csv",
)


# ══════════════════════════════════════════════════════════════════════════════
#  9. PIE DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.caption(
    "Proyecto I — Comprensión de datos | Grado en Ciencia de Datos | "
    "UPV ETSINF | Curso 2025-26"
)
