# Sistema de Conciliación Bancaria

Sistema web avanzado para conciliación bancaria automatizada con dos flujos de trabajo especializados.

## 🎯 Características principales

- **Interfaz web interactiva** con Streamlit
- **Dos workflows especializados**:
  - Workflow 1: Cuentas 4103, 4355, 10377 (matching por cola + tolerancia fechas)
  - Workflow 2: Cuentas servima, scotia, mato (merge directo por montos)
- **Análisis avanzado** con gráficos interactivos
- **Descarga de resultados** en múltiples formatos
- **Procesamiento Scotia optimizado** (73+ matches logrados)

## 📋 Requisitos

- Python 3.8+
- Streamlit
- Pandas
- Plotly
- openpyxl
- xlrd

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tuusuario/conciliacion-bancaria.git
cd conciliacion-bancaria
```

2. Instalar dependencias:
```bash
pip install -r requirements-nuthost.txt
```

3. Ejecutar la aplicación:
```bash
streamlit run app.py
```

## 🌐 Deployment

### Opción 1: Nuthost (Hosting compartido)
```bash
# Usar archivos preparados para Nuthost
python3 setup_nuthost.py
# Seguir instrucciones en DEPLOYMENT_NUTHOST.md
```

### Opción 2: Replit
```bash
# Configuración automática incluida
# Puerto: 5000
```

## 📊 Uso

1. **Subir archivos**: Banco y sistema
2. **Procesamiento**: Automático según tipo de cuenta
3. **Resultados**: Visualización y descarga
4. **Análisis**: Gráficos y estadísticas detalladas

## 🔧 Estructura del proyecto

```
├── app.py                 # Aplicación principal
├── utils/
│   ├── data_processor.py  # Procesamiento de datos
│   ├── reconciliation.py  # Motor de conciliación
│   └── chart_generator.py # Generación de gráficos
├── pages/
│   └── 1_📊_Tablero.py   # Dashboard
├── flask_app.py          # Wrapper Flask (para hosting)
├── wsgi.py               # Configuración WSGI
└── requirements-nuthost.txt
```

## 🎯 Workflows soportados

- **Cuentas 4103, 4355, 10377**: Matching por últimos 3 dígitos + tolerancia de fechas
- **Cuentas servima, scotia, mato**: Merge directo por montos exactos
- **Archivos Scotia**: Procesamiento especializado con corrección de encoding

## 📈 Resultados típicos

- Workflow 1: 77+ transacciones verificadas
- Workflow 2 (Scotia): 73+ matches logrados
- Descarga en Excel con 5 hojas de resultados

## 🛠️ Desarrollo

El sistema está optimizado para:
- Procesamiento de archivos XLS/XLSX
- Detección automática de headers
- Limpieza de datos avanzada
- Matching inteligente con tolerancias configurables

## 📝 Licencia

Uso exclusivo para conciliación bancaria empresarial.