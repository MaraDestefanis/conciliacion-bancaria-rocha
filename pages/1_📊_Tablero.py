import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.chart_generator import ChartGenerator
import pandas as pd

st.set_page_config(page_title="Tablero", page_icon="📊", layout="wide")

def main():
    st.title("📊 Tablero de Conciliación")
    
    if st.session_state.get('reconciliation_result') is None:
        st.warning("⚠️ No hay datos de conciliación disponibles. Realiza la conciliación en la página principal primero.")
        return
    
    result = st.session_state.reconciliation_result
    stats = result['statistics']
    chart_gen = ChartGenerator()
    
    # KPIs principales
    st.subheader("📈 Indicadores Clave")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Banco",
            f"{stats['total_transacciones_banco']:,}",
            help="Total de transacciones en archivo bancario"
        )
    
    with col2:
        st.metric(
            "Total Sistema", 
            f"{stats['total_transacciones_sistema']:,}",
            help="Total de transacciones en archivo del sistema"
        )
    
    with col3:
        st.metric(
            "Conciliadas",
            f"{stats['total_conciliadas']:,}",
            help="Transacciones exitosamente conciliadas"
        )
    
    with col4:
        porcentaje = stats['porcentaje_conciliacion']
        color = "normal"
        if porcentaje >= 90:
            color = "normal"
        elif porcentaje >= 70:
            color = "normal"
        else:
            color = "inverse"
        
        st.metric(
            "Porcentaje",
            f"{porcentaje:.1f}%",
            help="Porcentaje de conciliación exitosa"
        )
    
    with col5:
        if 'porcentaje_verificacion' in stats:
            st.metric(
                "Verificación",
                f"{stats['porcentaje_verificacion']:.2f}%",
                help="Porcentaje de verificación según IDs"
            )
    
    # ANÁLISIS DE TOTALES DETALLADO (para Workflow 2)
    if 'total_debito_original' in stats:
        st.subheader("💰 Análisis de Totales Detallado")
        
        # Crear tres columnas para organizar mejor
        col_original, col_verificadas, col_diferencias = st.columns(3)
        
        with col_original:
            st.write("**📋 Totales Originales**")
            st.write(f"💳 Débito Banco: ${stats['total_debito_original']:,.2f}")
            st.write(f"💰 Crédito Banco: ${stats['total_credito_original']:,.2f}")
            st.write(f"📤 Debe Sistema: ${stats['total_debe_original']:,.2f}")
            st.write(f"📥 Haber Sistema: ${stats['total_haber_original']:,.2f}")
        
        with col_verificadas:
            st.write("**✅ Totales Verificadas**")
            st.write(f"💳 Débito: ${stats['total_debito_verificadas']:,.2f}")
            st.write(f"💰 Crédito: ${stats['total_credito_verificadas']:,.2f}")
            st.write(f"📤 Debe: ${stats['total_debe_verificadas']:,.2f}")
            st.write(f"📥 Haber: ${stats['total_haber_verificadas']:,.2f}")
            
            st.write("**❌ Totales NO Verificadas**")
            st.write(f"💳 Débito: ${stats['total_debito_no_verificadas']:,.2f}")
            st.write(f"💰 Crédito: ${stats['total_credito_no_verificadas']:,.2f}")
            st.write(f"📤 Debe: ${stats['total_debe_no_verificadas']:,.2f}")
            st.write(f"📥 Haber: ${stats['total_haber_no_verificadas']:,.2f}")
        
        with col_diferencias:
            st.write("**🔍 Control de Diferencias**")
            
            # Validar diferencias (deben ser 0)
            dif_debito = stats.get('dif_debito', 0)
            dif_credito = stats.get('dif_credito', 0)
            dif_debe = stats.get('dif_debe', 0)
            dif_haber = stats.get('dif_haber', 0)
            
            # Mostrar con colores según si hay diferencias
            def mostrar_diferencia(nombre, valor):
                if valor == 0:
                    st.success(f"✅ {nombre}: ${valor}")
                else:
                    st.error(f"⚠️ {nombre}: ${valor}")
            
            mostrar_diferencia("Dif Débito", dif_debito)
            mostrar_diferencia("Dif Crédito", dif_credito)
            mostrar_diferencia("Dif Debe", dif_debe)
            mostrar_diferencia("Dif Haber", dif_haber)
            
            # Resumen general
            total_diferencias = abs(dif_debito) + abs(dif_credito) + abs(dif_debe) + abs(dif_haber)
            if total_diferencias == 0:
                st.success("🎯 **Control perfecto: Sin diferencias**")
            else:
                st.warning(f"⚠️ **Total diferencias: ${total_diferencias}**")
        
        st.metric(
            "% Conciliación",
            f"{porcentaje:.1f}%",
            help="Porcentaje de transacciones conciliadas"
        )
    
    with col5:
        diferencia_total = stats.get('diferencia_total_montos', 0)
        st.metric(
            "Diferencia Total",
            f"${diferencia_total:,.2f}",
            help="Diferencia total en montos conciliados"
        )
    
    st.markdown("---")
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Distribución de Conciliación")
        fig_summary = chart_gen.create_reconciliation_summary(result)
        st.plotly_chart(fig_summary, use_container_width=True)
    
    with col2:
        st.subheader("💰 Análisis de Montos")
        fig_amounts = chart_gen.create_amount_analysis(result)
        st.plotly_chart(fig_amounts, use_container_width=True)
    
    # Timeline
    st.subheader("📅 Timeline de Transacciones")
    fig_timeline = chart_gen.create_timeline_chart(result)
    st.plotly_chart(fig_timeline, use_container_width=True)
    

    
    # Resumen diario
    st.subheader("📅 Resumen Diario")
    fig_daily = chart_gen.create_daily_summary(result)
    st.plotly_chart(fig_daily, use_container_width=True)
    


if __name__ == "__main__":
    main()
