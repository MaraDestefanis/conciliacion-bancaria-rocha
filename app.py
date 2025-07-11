import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import numpy as np
from utils.data_processor import DataProcessor
from utils.reconciliation import ReconciliationEngine
from utils.chart_generator import ChartGenerator

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Conciliación Bancaria",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
if 'banco_data' not in st.session_state:
    st.session_state.banco_data = None
if 'sistema_data' not in st.session_state:
    st.session_state.sistema_data = None
if 'reconciliation_result' not in st.session_state:
    st.session_state.reconciliation_result = None

def analytics_section():
    """Sección de Analítica con verificación final"""
    st.markdown("### 📈 **Analítica**", unsafe_allow_html=True)
    
    if st.session_state.reconciliation_result is None:
        st.info("⚠️ Debe procesar archivos primero en la sección de Procesamiento.")
        return
    
    result = st.session_state.reconciliation_result
    
    # Mostrar directamente la verificación final
    st.subheader("🔍 Análisis de Diferencias - Verificación Final")
    execute_final_verification(result)

def execute_final_verification(result):
    """Ejecuta la verificación final según el código proporcionado por el usuario"""
    
    # Datos originales
    banco = result['banco_data']
    sistema = result['sistema_data']
    verificadas_final = result['matched']
    banco_noverif = result['unmatched_banco']
    sistema_noverif = result['unmatched_sistema']
    
    # Detectar qué columnas usar
    if 'debe' in sistema.columns and 'haber' in sistema.columns:
        col_debe = 'debe'
        col_haber = 'haber'
    else:
        col_debe = 'Debe'
        col_haber = 'Haber'
    
    # Totales originales
    total_debito = banco["Débito"].sum() if "Débito" in banco.columns else 0
    total_credito = banco["Crédito"].sum() if "Crédito" in banco.columns else 0
    total_debe = sistema[col_debe].sum() if col_debe in sistema.columns else 0
    total_haber = sistema[col_haber].sum() if col_haber in sistema.columns else 0
    
    st.markdown("#### 📊 Totales Originales:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Débito", f"${total_debito:,.2f}")
    with col2:
        st.metric("Crédito", f"${total_credito:,.2f}")
    with col3:
        st.metric("Debe", f"${total_debe:,.2f}")
    with col4:
        st.metric("Haber", f"${total_haber:,.2f}")
    
    # Totales verificados
    total_debito_v = verificadas_final["Débito"].sum() if "Débito" in verificadas_final.columns else 0
    total_credito_v = verificadas_final["Crédito"].sum() if "Crédito" in verificadas_final.columns else 0
    total_debe_v = verificadas_final[col_debe].sum() if col_debe in verificadas_final.columns else 0
    total_haber_v = verificadas_final[col_haber].sum() if col_haber in verificadas_final.columns else 0
    
    st.markdown("#### ✅ Totales Verificados:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Débito", f"${total_debito_v:,.2f}")
    with col2:
        st.metric("Crédito", f"${total_credito_v:,.2f}")
    with col3:
        st.metric("Debe", f"${total_debe_v:,.2f}")
    with col4:
        st.metric("Haber", f"${total_haber_v:,.2f}")
    
    # Totales no verificados
    total_debito_no_v = banco_noverif["Débito"].sum() if "Débito" in banco_noverif.columns else 0
    total_credito_no_v = banco_noverif["Crédito"].sum() if "Crédito" in banco_noverif.columns else 0
    total_debe_no_v = sistema_noverif[col_debe].sum() if col_debe in sistema_noverif.columns else 0
    total_haber_no_v = sistema_noverif[col_haber].sum() if col_haber in sistema_noverif.columns else 0
    
    st.markdown("#### ❌ Totales NO Verificados:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Débito", f"${total_debito_no_v:,.2f}")
    with col2:
        st.metric("Crédito", f"${total_credito_no_v:,.2f}")
    with col3:
        st.metric("Debe", f"${total_debe_no_v:,.2f}")
    with col4:
        st.metric("Haber", f"${total_haber_no_v:,.2f}")
    
    # Sumas finales (verificadas + no verificadas)
    total_debito_check = total_debito_v + total_debito_no_v
    total_credito_check = total_credito_v + total_credito_no_v
    total_debe_check = total_debe_v + total_debe_no_v
    total_haber_check = total_haber_v + total_haber_no_v
    
    st.markdown("#### 🔄 Sumas Finales (verificadas + no verificadas):")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Débito Check", f"${total_debito_check:,.2f}")
    with col2:
        st.metric("Crédito Check", f"${total_credito_check:,.2f}")
    with col3:
        st.metric("Debe Check", f"${total_debe_check:,.2f}")
    with col4:
        st.metric("Haber Check", f"${total_haber_check:,.2f}")
    
    # Diferencias
    dif_debito = round(total_debito - total_debito_check)
    dif_credito = round(total_credito - total_credito_check)
    dif_debe = round(total_debe - total_debe_check)
    dif_haber = round(total_haber - total_haber_check)
    
    st.markdown("#### ⚖️ Diferencias con los Totales Originales:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color = "normal" if dif_debito == 0 else "inverse"
        st.metric("Dif Débito", f"${dif_debito:,.2f}", delta_color=color)
    with col2:
        color = "normal" if dif_credito == 0 else "inverse"
        st.metric("Dif Crédito", f"${dif_credito:,.2f}", delta_color=color)
    with col3:
        color = "normal" if dif_debe == 0 else "inverse"
        st.metric("Dif Debe", f"${dif_debe:,.2f}", delta_color=color)
    with col4:
        color = "normal" if dif_haber == 0 else "inverse"
        st.metric("Dif Haber", f"${dif_haber:,.2f}", delta_color=color)
    
    # Porcentaje de verificación consistente con la sección de Resultados
    porcentaje_standard = result['statistics'].get('porcentaje_conciliacion', 0)
    st.markdown("#### 📊 Porcentaje de Verificación:")
    st.metric("% Verificación", f"{porcentaje_standard:.2f}%")
    
    # Información adicional sobre el método de cálculo
    total_banco = len(banco) if not banco.empty else 0
    total_verificadas = len(verificadas_final) if not verificadas_final.empty else 0
    st.info(f"Cálculo: {total_verificadas} verificadas de {total_banco} transacciones del banco = {porcentaje_standard:.2f}%")

def main():
    st.title("🏦 Sistema de Conciliación Bancaria")
    st.markdown("---")
    
    # Sidebar para navegación
    with st.sidebar:
        st.header("📋 Panel de Control")
        
        # Estado de archivos cargados
        if st.session_state.banco_data is not None:
            st.success(f"✅ Archivo bancario cargado ({len(st.session_state.banco_data)} registros)")
        else:
            st.warning("⏳ Archivo bancario pendiente")
            
        if st.session_state.sistema_data is not None:
            st.success(f"✅ Archivo sistema cargado ({len(st.session_state.sistema_data)} registros)")
        else:
            st.warning("⏳ Archivo sistema pendiente")
            
        if st.session_state.reconciliation_result is not None:
            st.info(f"📊 Conciliación realizada")
    
    # Tabs principales (corregido)
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Carga de Archivos", "⚙️ Procesamiento", "📊 Resultados", "📈 Analítica"])
    
    with tab1:
        upload_files_section()
    
    with tab2:
        processing_section()
    
    with tab3:
        results_section()
        
    with tab4:
        if st.session_state.reconciliation_result is not None:
            analytics_section()
        else:
            st.info("ℹ️ Ejecuta la conciliación para ver los analíticos.")

def prepare_verified_table_display(result):
    """Prepara la tabla de verificadas con el formato requerido"""
    matched_df = result['matched'].copy()
    
    # Agregar columna "Verificadas" con valor "v"
    matched_df['Verificadas'] = 'v'
    
    # Eliminar las columnas especificadas por el usuario
    columns_to_remove = [
        'Origen_sistema', 'Monto', 'Fecha_Sistema', 'Matched_sistema', 
        'Match_ID_sistema', 'Origen_banco', 'Fecha_Banco', 'Matched_banco',
        'origen_sistema', 'matched_banco', 'matched_sistema', 'Match_ID_banco', 
        'ID_banco', 'ID_sistema', 'verificadas'
    ]
    
    for col in columns_to_remove:
        if col in matched_df.columns:
            matched_df = matched_df.drop(columns=[col])
    
    # Reordenar columnas: poner "Verificadas" antes de "Fecha_banco" y "Nro.Trans." después de "Fecha_sistema"
    columns = matched_df.columns.tolist()
    
    # Reorganizar columnas según la estructura solicitada
    if 'Verificadas' in columns and 'Fecha_banco' in columns:
        # Remover "Verificadas" de su posición actual
        columns.remove('Verificadas')
        # Encontrar la posición de "Fecha_banco"
        fecha_banco_idx = columns.index('Fecha_banco')
        # Insertar "Verificadas" antes de "Fecha_banco"
        columns.insert(fecha_banco_idx, 'Verificadas')
    
    # Mover Nro.Trans. después de Fecha_sistema si existe
    if 'Nro.Trans.' in columns and 'Fecha_sistema' in columns:
        columns.remove('Nro.Trans.')
        fecha_sistema_idx = columns.index('Fecha_sistema')
        columns.insert(fecha_sistema_idx + 1, 'Nro.Trans.')
    
    matched_df = matched_df[columns]
    
    return matched_df

def prepare_banco_table_display(banco_df):
    """Prepara tabla del banco sin ID_banco"""
    display_df = banco_df.copy()
    columns_to_remove = [
        'ID_banco', 'origen_banco', 'matched_banco', 'Match_ID_banco',
        'Origen', 'Monto_Neto', 'Fecha_Banco', 'Documento_Banco', 'Matched', 'Match_ID'
    ]
    for col in columns_to_remove:
        if col in display_df.columns:
            display_df = display_df.drop(columns=[col])
    return display_df

def prepare_sistema_table_display(sistema_df):
    """Prepara tabla del sistema sin IDs ni agregados"""
    display_df = sistema_df.copy()
    columns_to_remove = [
        'ID_sistema', 'origen_sistema', 'matched_sistema', 'Match_ID_sistema',
        'Tipo Valor', 'Detalle', 'Origen', 'Monto', 'Fecha_Sistema', 'Matched', 'Match_ID'
    ]
    for col in columns_to_remove:
        if col in display_df.columns:
            display_df = display_df.drop(columns=[col])
    return display_df

def upload_files_section():
    st.markdown("### 📂 **Carga de Archivos**", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏛️ **Archivo del Banco**")
        st.info("Sube el archivo del banco (debe contener 'BRO' o similar en el nombre)")
        
        banco_file = st.file_uploader(
            "Seleccionar archivo bancario",
            type=['csv', 'xls', 'xlsx'],
            key='banco_upload',
            help="Formatos soportados: CSV, XLS, XLSX"
        )
        
        if banco_file is not None:
            try:
                processor = DataProcessor()
                df = processor.read_file(banco_file)
                
                if processor.is_bank_file(banco_file.name):
                    # Procesar y limpiar archivo bancario
                    processed_df = processor.process_bank_file(df.copy())
                    st.session_state.banco_data = df  # Datos originales
                    st.session_state.banco_processed = processed_df  # Datos procesados
                    st.session_state.banco_filename = banco_file.name
                    st.success(f"✅ Archivo bancario cargado correctamente ({len(processed_df)} filas)")
                    
                    with st.expander("👀 Vista previa de archivo limpiado"):
                        st.dataframe(processed_df.head())
                else:
                    st.warning("⚠️ El archivo no parece ser del banco. Revisa el nombre del archivo.")
                    
            except Exception as e:
                st.error(f"❌ Error al cargar el archivo: {str(e)}")
    
    with col2:
        st.markdown("#### 💾 **Archivo del Sistema**")
        st.info("Sube el archivo del sistema (debe contener 'AYP' o similar en el nombre)")
        
        sistema_file = st.file_uploader(
            "Seleccionar archivo del sistema",
            type=['csv', 'xls', 'xlsx'],
            key='sistema_upload',
            help="Formatos soportados: CSV, XLS, XLSX"
        )
        
        if sistema_file is not None:
            try:
                processor = DataProcessor()
                df = processor.read_file(sistema_file)
                
                if processor.is_system_file(sistema_file.name):
                    # Procesar y limpiar archivo del sistema
                    processed_df = processor.process_system_file(df.copy())
                    st.session_state.sistema_data = df  # Datos originales
                    st.session_state.sistema_processed = processed_df  # Datos procesados
                    st.session_state.sistema_filename = sistema_file.name
                    st.success(f"✅ Archivo del sistema cargado correctamente ({len(processed_df)} filas)")
                    
                    with st.expander("👀 Vista previa de archivo limpiado"):
                        st.dataframe(processed_df.head())
                else:
                    st.warning("⚠️ El archivo no parece ser del sistema. Revisa el nombre del archivo.")
                    
            except Exception as e:
                st.error(f"❌ Error al cargar el archivo: {str(e)}")
    
    # Mostrar resúmenes de archivos en Carga de Archivos (según corrección del usuario)
    if 'banco_processed' in st.session_state and 'sistema_processed' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 **Resúmenes de Archivos**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏛️ **Resumen Archivo Bancario**")
            banco_info = get_file_summary(st.session_state.banco_processed, "banco")
            
            # Mostrar de forma más visual y intuitiva
            st.metric("Total de filas", banco_info["Total de filas"])
            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                st.metric("Total de columnas", banco_info["Total de columnas"])
                st.metric("Valores nulos", banco_info["Valores nulos cantidad"])
            with col_sub2:
                st.metric("Duplicados", banco_info["Cantidad de duplicados"])
                
            # Mostrar totales monetarios
            if "Total Débito" in banco_info:
                st.metric("💰 Total Débito", banco_info["Total Débito"])
            if "Total Crédito" in banco_info:
                st.metric("💰 Total Crédito", banco_info["Total Crédito"])
        
        with col2:
            st.markdown("#### 💾 **Resumen Archivo Sistema**")
            sistema_info = get_file_summary(st.session_state.sistema_processed, "sistema")
            
            # Mostrar de forma más visual y intuitiva
            st.metric("Total de filas", sistema_info["Total de filas"])
            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                st.metric("Total de columnas", sistema_info["Total de columnas"])
                st.metric("Valores nulos", sistema_info["Valores nulos cantidad"])
            with col_sub2:
                st.metric("Duplicados", sistema_info["Cantidad de duplicados"])
                
            # Mostrar totales monetarios
            if "Total Debe" in sistema_info:
                st.metric("💰 Total Debe", sistema_info["Total Debe"])
            if "Total Haber" in sistema_info:
                st.metric("💰 Total Haber", sistema_info["Total Haber"])

def processing_section():
    st.markdown("### ⚙️ **Procesamiento de Datos**", unsafe_allow_html=True)
    
    if 'banco_processed' not in st.session_state or 'sistema_processed' not in st.session_state:
        st.warning("⚠️ Necesitas cargar ambos archivos antes de procesar.")
        return
    
    # Configuración de procesamiento
    st.markdown("#### 🎛️ **Configuración de Procesamiento**")
    
    # Configuraciones de conciliación
    tolerance_days = st.slider(
        "Tolerancia en días para fechas", 
        min_value=0, 
        max_value=15, 
        value=10,
        help="Diferencia máxima de días permitida entre transacciones"
    )
    
    st.info("📍 Los montos se comparan como números enteros exactos (sin decimales)")
    st.session_state.tolerance_days = tolerance_days
    
    # Botón de Iniciar Conciliación después de la tolerancia (más intuitivo)
    if st.button("🚀 Iniciar Conciliación", type="primary", use_container_width=True):
        process_reconciliation()

def process_reconciliation():
    """Procesa la conciliación de los archivos cargados"""
    try:
        with st.spinner("🔄 Procesando conciliación..."):
            # Usar datos ya procesados del session state
            if 'banco_processed' not in st.session_state or 'sistema_processed' not in st.session_state:
                st.error("⚠️ Error: Archivos no procesados correctamente. Intenta cargar los archivos nuevamente.")
                return
            
            # Detectar tipo de workflow
            banco_filename = st.session_state.get('banco_filename', 'unknown')
            sistema_filename = st.session_state.get('sistema_filename', 'unknown')
            processor = DataProcessor()
            workflow_type = processor.get_workflow_type(banco_filename, sistema_filename)
            
            banco_clean = st.session_state.banco_processed.copy()
            sistema_clean = st.session_state.sistema_processed.copy()
            
            # Realizar conciliación con el workflow detectado
            reconciler = ReconciliationEngine(
                tolerance_days=st.session_state.get('tolerance_days', 1)
            )
            
            result = reconciler.reconcile(banco_clean, sistema_clean, workflow_type)
            st.session_state.reconciliation_result = result
            
            # Obtener estadísticas detalladas del resultado
            matches = len(result['matched'])
            total_banco = len(result['banco_data'])
            total_sistema = len(result['sistema_data'])
            unmatched_banco = len(result['unmatched_banco'])
            unmatched_sistema = len(result['unmatched_sistema'])
            porcentaje_verificadas = (matches / max(total_banco, 1)) * 100
            
            # Obtener totales de montos si están disponibles
            stats = result.get('statistics', {})
            
            # Crear mensaje de éxito detallado y profesional
            st.balloons()
            
            # Contenedor principal con el resultado
            with st.container():
                st.success(f"""
                ✅ **CONCILIACIÓN COMPLETADA EXITOSAMENTE**
                
                **Tipo de Workflow:** {workflow_type.upper().replace('_', ' ')}
                """)
                
                # Métricas en columnas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Verificadas", 
                        f"{matches:,}",
                        help="Transacciones que coinciden entre banco y sistema"
                    )
                
                with col2:
                    st.metric(
                        "% Verificadas", 
                        f"{porcentaje_verificadas:.1f}%",
                        help="Porcentaje de verificación sobre total banco"
                    )
                
                with col3:
                    st.metric(
                        "Banco Sin Conciliar", 
                        f"{unmatched_banco:,}",
                        help="Transacciones bancarias sin coincidencia"
                    )
                
                with col4:
                    st.metric(
                        "Sistema Sin Conciliar", 
                        f"{unmatched_sistema:,}",
                        help="Transacciones del sistema sin coincidencia"
                    )
                
                # Totales de montos si están disponibles
                if stats and 'total_verificadas_monto' in stats:
                    st.info(f"""
                    **Resumen de Montos:**
                    - Total Verificadas: ${stats.get('total_verificadas_monto', 0):,.2f}
                    - Total Banco: ${stats.get('total_banco_monto', 0):,.2f}
                    - Total Sistema: ${stats.get('total_sistema_monto', 0):,.2f}
                    """)
            
            # Mensaje de rendimiento
            if matches > 0:
                if porcentaje_verificadas >= 80:
                    st.success(f"🏆 **EXCELENTE RENDIMIENTO:** {porcentaje_verificadas:.1f}% de transacciones verificadas")
                elif porcentaje_verificadas >= 60:
                    st.info(f"👍 **BUEN RENDIMIENTO:** {porcentaje_verificadas:.1f}% de transacciones verificadas")
                else:
                    st.warning(f"⚠️ **RENDIMIENTO MEJORABLE:** {porcentaje_verificadas:.1f}% de transacciones verificadas")
            else:
                st.error("❌ **No se encontraron coincidencias.** Revisa los archivos y configuración.")
            
    except Exception as e:
        st.error(f"❌ Error durante la conciliación: {str(e)}")

def results_section():
    st.markdown("### 📈 **Resultados de Conciliación**", unsafe_allow_html=True)
    
    if st.session_state.reconciliation_result is None:
        st.info("ℹ️ Ejecuta la conciliación para ver los resultados.")
        return
    
    result = st.session_state.reconciliation_result
    chart_gen = ChartGenerator()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Transacciones Banco",
            len(result['banco_data']),
            help="Número total de transacciones en el archivo bancario"
        )
    
    with col2:
        st.metric(
            "Total Transacciones Sistema",
            len(result['sistema_data']),
            help="Número total de transacciones en el archivo del sistema"
        )
    
    with col3:
        conciliadas = len(result['matched'])
        st.metric(
            "Transacciones Conciliadas",
            conciliadas,
            help="Transacciones que coinciden entre ambos archivos"
        )
    
    with col4:
        # Usar el porcentaje estándar calculado por el motor de conciliación
        porcentaje_verificadas = result['statistics'].get('porcentaje_conciliacion', 0)
        st.metric(
            "% Verificadas",
            f"{porcentaje_verificadas:.1f}%",
            help="Porcentaje de transacciones verificadas basado en el total del banco"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de distribución
        fig_dist = chart_gen.create_reconciliation_summary(result)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        # Gráfico de montos
        fig_amounts = chart_gen.create_amount_analysis(result)
        st.plotly_chart(fig_amounts, use_container_width=True)
    
    # Timeline de transacciones
    st.subheader("📅 Timeline de Transacciones")
    fig_timeline = chart_gen.create_timeline_chart(result)
    st.plotly_chart(fig_timeline, use_container_width=True)
    

    
    # Tablas de resultados con columnas corregidas
    st.subheader("📋 Detalle de Resultados")
    
    # Botón para descargar archivo compilado
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📑 Descargar archivo compilado", use_container_width=True, help="Descarga un Excel con todas las hojas: Verificadas final, Sin conciliar banco, Sin conciliar sistema, Dataset banco limpio, Dataset sistema limpio"):
            try:
                workflow_type = result.get('workflow_type', 'workflow_1')
                compiled_excel = create_compiled_excel_download(result, workflow_type)
                
                st.download_button(
                    label="📥 Descargar Excel Compilado",
                    data=compiled_excel,
                    file_name=f"conciliacion_compilada_{workflow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )
                st.success("✅ Archivo Excel compilado generado exitosamente")
            except Exception as e:
                st.error(f"❌ Error generando archivo compilado: {str(e)}")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["✅ Tabla de Verificadas", "❌ Sin Conciliar Banco", "❌ Sin Conciliar Sistema"])
    
    with tab1:
        if len(result['matched']) > 0:
            # Mostrar tabla de verificadas con estructura corregida
            verified_display = prepare_verified_table_display(result)
            st.dataframe(verified_display, use_container_width=True)
            
            # Crear archivo verificadas según el workflow
            workflow_type = result.get('workflow_type', 'workflow_1')
            verified_csv = create_verified_download(result, workflow_type)
            
            st.download_button(
                label="📥 Descargar Verificadas Final (CSV)",
                data=verified_csv,
                file_name=f"verificadas_final_{workflow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        else:
            st.info("No hay transacciones verificadas.")
    
    with tab2:
        if len(result['unmatched_banco']) > 0:
            # Mostrar solo columnas originales del banco (sin ID_banco)
            banco_display = prepare_banco_table_display(result['unmatched_banco'])
            st.dataframe(banco_display, use_container_width=True)
            
            # Crear archivo no verificadas banco según el workflow
            workflow_type = result.get('workflow_type', 'workflow_1')
            unmatched_banco_csv = create_unmatched_banco_download(result, workflow_type)
            
            st.download_button(
                label="📥 Descargar Sin Conciliar Banco (CSV)",
                data=unmatched_banco_csv,
                file_name=f"banco_noverif_{workflow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        else:
            st.info("Todas las transacciones del banco fueron conciliadas.")
    
    with tab3:
        if len(result['unmatched_sistema']) > 0:
            # Mostrar solo columnas originales del sistema (sin IDs ni columnas agregadas)
            sistema_display = prepare_sistema_table_display(result['unmatched_sistema'])
            st.dataframe(sistema_display, use_container_width=True)
            
            # Crear archivo no verificadas sistema según el workflow
            workflow_type = result.get('workflow_type', 'workflow_1')
            unmatched_sistema_csv = create_unmatched_sistema_download(result, workflow_type)
            
            st.download_button(
                label="📥 Descargar Sin Conciliar Sistema (CSV)",
                data=unmatched_sistema_csv,
                file_name=f"sistema_noverific_{workflow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        else:
            st.info("Todas las transacciones del sistema fueron conciliadas.")

def get_file_summary(df, file_type="archivo"):
    """Genera un resumen mejorado de información del archivo según requerimientos"""
    # Limpiar el DataFrame para conteo preciso de nulos
    df_for_analysis = df.copy()
    
    # Solo contar nulos en filas que no están completamente vacías
    # Esto evita contar las filas/columnas que se crearon durante el procesamiento
    non_empty_rows = ~df_for_analysis.isnull().all(axis=1)
    df_for_analysis = df_for_analysis[non_empty_rows]
    
    # Información básica requerida
    null_count = df_for_analysis.isnull().sum().sum()
    
    # Debug: mostrar qué columnas tienen nulos (para depuración)
    if null_count > 0:
        null_by_column = df_for_analysis.isnull().sum()
        columns_with_nulls = null_by_column[null_by_column > 0]
        print(f"🔍 Columnas con nulos en {file_type}: {dict(columns_with_nulls)}")
    
    summary_data = {
        "Total de filas": len(df_for_analysis),
        "Total de columnas": len(df_for_analysis.columns),
        "Valores nulos cantidad": null_count,
        "Cantidad de duplicados": df_for_analysis.duplicated().sum()
    }
    
    # Totales de débito/crédito según el tipo de archivo
    if file_type == "banco":
        # Para archivos bancarios: Débito y Crédito (con tilde)
        if 'Débito' in df.columns and 'Crédito' in df.columns:
            summary_data["Total Débito"] = f"${df['Débito'].sum():,.2f}"
            summary_data["Total Crédito"] = f"${df['Crédito'].sum():,.2f}"
        elif 'Debito' in df.columns and 'Credito' in df.columns:
            summary_data["Total Débito"] = f"${df['Debito'].sum():,.2f}"
            summary_data["Total Crédito"] = f"${df['Credito'].sum():,.2f}"
    else:
        # Para archivos sistema: Debe y Haber
        if 'Debe' in df.columns and 'Haber' in df.columns:
            summary_data["Total Debe"] = f"${df['Debe'].sum():,.2f}"
            summary_data["Total Haber"] = f"${df['Haber'].sum():,.2f}"
        elif 'debe' in df.columns and 'haber' in df.columns:
            summary_data["Total Debe"] = f"${df['debe'].sum():,.2f}"
            summary_data["Total Haber"] = f"${df['haber'].sum():,.2f}"
    
    return summary_data

def create_verified_download(result, workflow_type):
    """Crea archivo de descarga para transacciones verificadas según el workflow"""
    matched_df = result['matched']
    
    if workflow_type == 'workflow_1':
        # Workflow 1: Cuentas 4103, 4355, 10377
        # Columnas exactas del documento de testeo
        verified_df = matched_df.copy()
        verified_df['Verificadas'] = 'v'
        
        columns_order = [
            'Fecha_banco', 'Descripción', 'Número de documento', 'Dependencia', 
            'Débito', 'Crédito', 'Verificadas', 'Fecha_sistema', 'Nro.Trans.', 
            'Nro.Ref.Bco', 'Tipo Valor', 'Concepto', 'Detalle', 'Debe', 'Haber', 
            'Saldo', 'Estado'
        ]
    else:
        # Workflow 2: servima, scotia, brou
        verified_df = matched_df.copy()
        verified_df['verificada'] = 'v'
        
        # Detectar si es archivo Scotia (tiene 'Dep. Origen')
        if 'Dep. Origen' in matched_df.columns:
            # Scotia files - columnas específicas del testeo
            columns_order = [
                'fec', 'documento', 'cliprov', 'debe', 'haber', 'saldo', 'concepto',
                'ID_rocha', 'verificada', 'Dep. Origen', 'Concepto', 'Comprobante',
                'Fecha', 'Débito', 'Crédito', 'Saldo'
            ]
        else:
            # Regular workflow 2
            columns_order = [
                'fec', 'documento', 'cliprov', 'debe', 'haber', 'saldo', 'verificada',
                'Fecha', 'Descripción', 'Número de documento', 'Asunto', 'Dependencia',
                'Débito', 'Crédito'
            ]
    
    # Filtrar solo las columnas que existen y mantener el orden
    available_columns = [col for col in columns_order if col in verified_df.columns]
    if available_columns:
        verified_df = verified_df[available_columns]
    
    return verified_df.to_csv(index=False, encoding='utf-8-sig')

def create_unmatched_banco_download(result, workflow_type):
    """Crea archivo de descarga para registros bancarios sin conciliar"""
    unmatched_df = result['unmatched_banco']
    
    if workflow_type == 'workflow_1':
        # Workflow 1: Cuentas 4103, 4355, 10377 - columnas exactas del testeo
        columns_order = ['Fecha', 'Descripción', 'Número de documento', 'Asunto', 'Dependencia', 'Débito', 'Crédito']
    else:
        # Workflow 2: servima, scotia, brou
        if 'Dep. Origen' in unmatched_df.columns:
            # Scotia files - columnas exactas del testeo
            columns_order = ['Dep. Origen', 'Concepto', 'Comprobante', 'Fecha', 'Débito', 'Crédito', 'Saldo']
        else:
            # Regular workflow 2 - columnas exactas del testeo
            columns_order = ['Fecha', 'Descripción', 'Número de documento', 'Asunto', 'Dependencia', 'Débito', 'Crédito']
    
    # Filtrar solo las columnas que existen y mantener el orden
    available_columns = [col for col in columns_order if col in unmatched_df.columns]
    if available_columns:
        filtered_df = unmatched_df[available_columns]
    else:
        filtered_df = unmatched_df
    
    return filtered_df.to_csv(index=False, encoding='utf-8-sig')

def create_unmatched_sistema_download(result, workflow_type):
    """Crea archivo de descarga para registros del sistema sin conciliar"""
    unmatched_df = result['unmatched_sistema']
    
    if workflow_type == 'workflow_1':
        # Workflow 1: Cuentas 4103, 4355, 10377 - columnas exactas del testeo
        columns_order = ['Fecha', 'Nro.Trans.', 'Nro.Ref.Bco', 'Tipo Valor', 'Concepto', 'Detalle', 'Debe', 'Haber', 'Saldo', 'Estado']
    else:
        # Workflow 2: servima, scotia, brou - columnas exactas del testeo
        columns_order = ['fec', 'documento', 'cliprov', 'debe', 'haber', 'saldo']
    
    # Filtrar solo las columnas que existen y mantener el orden
    available_columns = [col for col in columns_order if col in unmatched_df.columns]
    if available_columns:
        filtered_df = unmatched_df[available_columns]
    else:
        filtered_df = unmatched_df
    
    return filtered_df.to_csv(index=False, encoding='utf-8-sig')

def create_compiled_excel_download(result, workflow_type):
    """Crea archivo Excel compilado con todas las hojas según requerimientos del usuario"""
    from io import BytesIO
    import pandas as pd
    
    def clean_columns(df):
        """Elimina columnas no deseadas de todos los DataFrames"""
        columns_to_remove = [
            'Origen_sistema', 'Monto', 'Fecha_Sistema', 'Matched_sistema', 
            'Match_ID_sistema', 'Origen_banco', 'Fecha_Banco', 'Matched_banco',
            'origen_sistema', 'matched_banco', 'matched_sistema', 'Match_ID_banco', 
            'ID_banco', 'ID_sistema', 'verificadas', 'monto_dif', 'dif_dias',
            'match_quality', 'doc_banco_tail', 'doc_sistema_tail',
            'Debe_int', 'Haber_int', 'Crédito_int', 'Débito_int',  # Columnas _int a eliminar
            'Matched', 'Match_ID'  # Columnas Matched y Match_ID a eliminar
        ]
        
        for col in columns_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])
        return df
    
    def reorder_verified_columns(df):
        """Reordena columnas para poner 'Verificadas' antes de 'Dep.Origen' y 'Dep.Origen' entre 'Fecha' y 'Concepto'"""
        columns = df.columns.tolist()
        
        # Manejar las columnas que necesitan reordenamiento
        columns_to_reorder = ['Verificadas', 'Dep.Origen']
        temp_removed = {}
        
        # Remover las columnas que vamos a reordenar
        for col in columns_to_reorder:
            if col in columns:
                columns.remove(col)
                temp_removed[col] = True
        
        # Buscar la posición correcta para insertar las columnas
        if 'Fecha' in columns and 'Concepto' in columns:
            fecha_idx = columns.index('Fecha')
            concepto_idx = columns.index('Concepto')
            
            # Insertar 'Verificadas' antes de 'Fecha'
            if 'Verificadas' in temp_removed:
                columns.insert(fecha_idx, 'Verificadas')
                # Actualizar índices después de la inserción
                concepto_idx += 1
            
            # Insertar 'Dep.Origen' entre 'Fecha' y 'Concepto'
            if 'Dep.Origen' in temp_removed:
                columns.insert(concepto_idx, 'Dep.Origen')
        
        elif 'Fecha' in columns:
            # Si solo tenemos 'Fecha', poner 'Verificadas' antes y 'Dep.Origen' después
            fecha_idx = columns.index('Fecha')
            if 'Verificadas' in temp_removed:
                columns.insert(fecha_idx, 'Verificadas')
                fecha_idx += 1
            if 'Dep.Origen' in temp_removed:
                columns.insert(fecha_idx + 1, 'Dep.Origen')
        
        else:
            # Si no hay referencias, poner al final
            if 'Verificadas' in temp_removed:
                columns.append('Verificadas')
            if 'Dep.Origen' in temp_removed:
                columns.append('Dep.Origen')
        
        # Reordenar DataFrame
        df = df[columns]
        return df
    
    # Crear buffer para Excel
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja 1: Verificadas final
        if len(result['matched']) > 0:
            verified_df = result['matched'].copy()
            
            # Limpiar columnas no deseadas primero
            verified_df = clean_columns(verified_df)
            
            # Agregar columna 'Verificadas' solo si no existe
            if 'Verificadas' not in verified_df.columns:
                verified_df['Verificadas'] = 'v'
            
            # Reordenar columnas después de saldo
            if 'Saldo' in verified_df.columns:
                columns = verified_df.columns.tolist()
                
                # Remover 'Verificadas' si ya existe
                if 'Verificadas' in columns:
                    columns.remove('Verificadas')
                
                # Encontrar posición de 'Saldo' e insertar 'Verificadas' después
                saldo_idx = columns.index('Saldo')
                columns.insert(saldo_idx + 1, 'Verificadas')
                
                # Reordenar DataFrame
                verified_df = verified_df[columns]
            
            verified_df.to_excel(writer, sheet_name='Verificadas final', index=False)
        
        # Hoja 2: Sin conciliar banco
        if len(result['unmatched_banco']) > 0:
            banco_df = result['unmatched_banco'].copy()
            banco_df = clean_columns(banco_df)
            banco_df.to_excel(writer, sheet_name='Sin conciliar banco', index=False)
        
        # Hoja 3: Sin conciliar sistema
        if len(result['unmatched_sistema']) > 0:
            sistema_df = result['unmatched_sistema'].copy()
            sistema_df = clean_columns(sistema_df)
            sistema_df.to_excel(writer, sheet_name='Sin conciliar sistema', index=False)
        
        # Hoja 4: Dataset banco limpio
        if 'banco_data' in result:
            banco_clean_df = result['banco_data'].copy()
            banco_clean_df = clean_columns(banco_clean_df)
            banco_clean_df.to_excel(writer, sheet_name='Dataset banco limpio', index=False)
        
        # Hoja 5: Dataset sistema limpio
        if 'sistema_data' in result:
            sistema_clean_df = result['sistema_data'].copy()
            sistema_clean_df = clean_columns(sistema_clean_df)
            sistema_clean_df.to_excel(writer, sheet_name='Dataset sistema limpio', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()



if __name__ == "__main__":
    main()

