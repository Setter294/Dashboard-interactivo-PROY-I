[README.md](https://github.com/user-attachments/files/27406737/README.md)
# 📊 Dashboard — Empleo en el sector tecnológico de EEUU (2001–2025)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dashboard-datos-interactivo.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75.svg?logo=plotly&logoColor=white)](https://plotly.com/python/)

> 🚀 **Demo en vivo:** [https://dashboard-datos-interactivo.streamlit.app/](https://dashboard-datos-interactivo.streamlit.app/)

Dashboard interactivo que analiza la evolución del empleo en 25 grandes empresas tecnológicas de EEUU durante el periodo 2001–2025. Incluye filtros dinámicos, KPIs en tiempo real y visualizaciones que permiten explorar contrataciones, despidos, variaciones netas e ingresos a través de los grandes ciclos económicos del periodo (burbuja puntocom, crisis financiera, boom COVID y ajuste post-COVID).

Desarrollado como parte del **Proyecto I — Comprensión de datos** del Grado en Ciencia de Datos de la **UPV ETSINF** (curso 2025-26).

---

## 🎯 Características principales

- **Filtros interactivos** en sidebar: selector múltiple de empresas y slider de rango de años.
- **Toggle de contexto histórico**: muestra/oculta franjas sombreadas con los periodos económicos clave.
- **4 KPIs dinámicos**: total de despidos, tasa de contratación media, récord de ingresos y cambio neto de empleos (con delta interanual).
- **Gráficas reactivas (Plotly)**:
  - Variación neta anual (barras verde/rojo según signo).
  - Contrataciones vs despidos (áreas con líneas superpuestas).
  - Distribución de variación neta por empresa (boxplot).
  - Mapa de calor empresa × año con escala divergente.
- **Análisis adicional**: top 5 empresas por crecimiento/reducción y tabla detallada con descarga en CSV.
- **Tema oscuro** consistente en toda la aplicación.

---

## 🛠️ Stack tecnológico

| Componente | Uso |
|------------|-----|
| **Streamlit** | Framework web del dashboard |
| **Pandas** | Manipulación y agregación de datos |
| **NumPy** | Operaciones numéricas y máscaras |
| **Plotly** | Gráficas interactivas |

---

## 🚀 Ejecución en local

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/<nombre-repo>.git
cd <nombre-repo>
```

### 2. Crear entorno virtual *(recomendado)*

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Lanzar el dashboard

```bash
streamlit run dashboard.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`. Si no se abre, copia esa URL en tu navegador.

> 💡 **Importante:** el archivo `tech_employment_2000_2025.csv` debe estar en la misma carpeta que `dashboard.py`. La función de carga es robusta y admite tanto el formato estándar (`sep=','`, `decimal='.'`) como el formato Statgraphics (`sep=';'`, `decimal=','`) gracias a un fallback automático.

---

## 📁 Estructura del proyecto

```
.
├── dashboard.py                       # Aplicación Streamlit principal
├── tech_employment_2000_2025.csv      # Dataset (25 empresas × 25 años)
├── requirements.txt                   # Dependencias Python
├── analisis_completo_comentado.ipynb  # Notebook de análisis estadístico
└── README.md                          # Este archivo
```

---

## 📈 Sobre el dataset

| Aspecto | Detalle |
|---------|---------|
| Empresas | 25 (Amazon, Microsoft, Apple, Alphabet, Meta, Intel, AMD, NVIDIA, Oracle, etc.) |
| Periodo | 2001–2025 (25 años) |
| Observaciones | 532 filas |
| Variables clave | `employees_start`, `employees_end`, `new_hires`, `layoffs`, `net_change`, `hiring_rate_pct`, `attrition_rate_pct`, `revenue_billions_usd`, `gdp_growth_us_pct`, `unemployment_rate_us_pct` |

El dashboard genera además variables derivadas durante la carga: `tamanyo_empresa`, `categoria_empresa` (según antigüedad de la empresa en cada año), `periodo` (ciclo económico) y transformaciones logarítmicas para manejar los valores extremos de Amazon.

---

## 👥 Autoría

**Proyecto I — Comprensión de datos** | Grado en Ciencia de Datos | UPV ETSINF | Curso 2025-26

- Pau Cantos Sales
- Rubén Delgado Palacios
- Andreu Esteve Rodríguez
- Álvaro de Llano Santos
- Iván Martínez Castellot

**Tutor:** Arturo Hernández Sánchez

---

## 📜 Licencia

Proyecto académico desarrollado con fines educativos en el marco del Grado en Ciencia de Datos de la UPV.
