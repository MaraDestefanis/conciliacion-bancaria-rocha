import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ChartGenerator:
    """Generador de gráficos para conciliación bancaria"""
    
    def __init__(self):
        self.colors = {
            'conciliado': '#28a745',  # Verde
            'sin_conciliar': '#dc3545',  # Rojo
            'banco': '#007bff',  # Azul
            'sistema': '#6f42c1',  # Púrpura
            'diferencia': '#fd7e14'  # Naranja
        }
    
    def create_reconciliation_summary(self, reconciliation_result):
        """Crea gráfico de resumen de conciliación"""
        stats = reconciliation_result['statistics']
        
        labels = ['Conciliadas', 'Sin Conciliar Banco', 'Sin Conciliar Sistema']
        values = [
            stats['total_conciliadas'],
            stats['sin_conciliar_banco'],
            stats['sin_conciliar_sistema']
        ]
        colors = [self.colors['conciliado'], self.colors['sin_conciliar'], self.colors['sin_conciliar']]
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=values,
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Resumen de Conciliación",
            font=dict(size=12),
            showlegend=False,
            height=400,
            xaxis_title="Categorías",
            yaxis_title="Cantidad de Registros"
        )
        
        return fig
    
    def create_amount_analysis(self, reconciliation_result):
        """Crea análisis de montos conciliados vs no conciliados"""
        stats = reconciliation_result['statistics']
        
        categories = []
        amounts = []
        colors_list = []
        
        if stats.get('monto_total_conciliado_banco', 0) != 0:
            categories.append('Conciliado')
            amounts.append(abs(stats['monto_total_conciliado_banco']))
            colors_list.append(self.colors['conciliado'])
        
        if stats.get('monto_sin_conciliar_banco', 0) != 0:
            categories.append('Sin Conciliar Banco')
            amounts.append(abs(stats['monto_sin_conciliar_banco']))
            colors_list.append(self.colors['sin_conciliar'])
        
        if stats.get('monto_sin_conciliar_sistema', 0) != 0:
            categories.append('Sin Conciliar Sistema')
            amounts.append(abs(stats['monto_sin_conciliar_sistema']))
            colors_list.append(self.colors['diferencia'])
        
        if not categories:
            # Gráfico vacío si no hay datos
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de montos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title="Análisis de Montos", height=400)
            return fig
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=amounts,
                marker_color=colors_list,
                text=[f"${amt:,.2f}" for amt in amounts],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Análisis de Montos por Categoría",
            xaxis_title="Categoría",
            yaxis_title="Monto ($)",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_timeline_chart(self, reconciliation_result):
        """Crea timeline de transacciones conciliadas y no conciliadas"""
        matched_df = reconciliation_result['matched']
        unmatched_banco = reconciliation_result['unmatched_banco']
        unmatched_sistema = reconciliation_result['unmatched_sistema']
        
        fig = go.Figure()
        
        # Transacciones conciliadas
        if not matched_df.empty and 'Fecha_Banco' in matched_df.columns:
            matched_df_clean = matched_df.dropna(subset=['Fecha_Banco'])
            if not matched_df_clean.empty:
                # Usar nombres de columnas flexibles
                monto_banco_col = 'Monto_Banco' if 'Monto_Banco' in matched_df_clean.columns else 'Monto_Neto'
                monto_sistema_col = 'Monto_Sistema' if 'Monto_Sistema' in matched_df_clean.columns else 'Monto'
                
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(matched_df_clean['Fecha_Banco']),
                    y=matched_df_clean[monto_banco_col],
                    mode='markers',
                    name='Conciliadas',
                    marker=dict(color=self.colors['conciliado'], size=8),
                    text=[f"Banco: ${m:.2f}<br>Sistema: ${s:.2f}" 
                          for m, s in zip(matched_df_clean[monto_banco_col], matched_df_clean[monto_sistema_col])],
                    hovertemplate='<b>Conciliada</b><br>Fecha: %{x}<br>%{text}<extra></extra>'
                ))
        
        # Transacciones sin conciliar del banco
        if not unmatched_banco.empty and 'Fecha' in unmatched_banco.columns:
            unmatched_banco_clean = unmatched_banco.dropna(subset=['Fecha'])
            if not unmatched_banco_clean.empty:
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(unmatched_banco_clean['Fecha']),
                    y=unmatched_banco_clean.get('Monto_Neto', unmatched_banco_clean.get('Monto', 0)),
                    mode='markers',
                    name='Sin Conciliar (Banco)',
                    marker=dict(color=self.colors['banco'], size=6, symbol='x'),
                    text=[f"Monto: ${m:.2f}" for m in unmatched_banco_clean.get('Monto_Neto', unmatched_banco_clean.get('Monto', 0))],
                    hovertemplate='<b>Sin Conciliar - Banco</b><br>Fecha: %{x}<br>%{text}<extra></extra>'
                ))
        
        # Transacciones sin conciliar del sistema
        if not unmatched_sistema.empty and 'Fecha' in unmatched_sistema.columns:
            unmatched_sistema_clean = unmatched_sistema.dropna(subset=['Fecha'])
            if not unmatched_sistema_clean.empty:
                fig.add_trace(go.Scatter(
                    x=pd.to_datetime(unmatched_sistema_clean['Fecha']),
                    y=unmatched_sistema_clean.get('Monto', 0),
                    mode='markers',
                    name='Sin Conciliar (Sistema)',
                    marker=dict(color=self.colors['sistema'], size=6, symbol='diamond'),
                    text=[f"Monto: ${m:.2f}" for m in unmatched_sistema_clean.get('Monto', 0)],
                    hovertemplate='<b>Sin Conciliar - Sistema</b><br>Fecha: %{x}<br>%{text}<extra></extra>'
                ))
        
        fig.update_layout(
            title="Timeline de Transacciones",
            xaxis_title="Fecha",
            yaxis_title="Monto ($)",
            height=500,
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_match_type_distribution(self, reconciliation_result):
        """Crea distribución de tipos de match"""
        matched_df = reconciliation_result['matched']
        
        if matched_df.empty or 'Match_Type' not in matched_df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de tipos de match",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        match_counts = matched_df['Match_Type'].value_counts()
        
        fig = go.Figure(data=[go.Bar(
            x=match_counts.index,
            y=match_counts.values,
            marker_color=self.colors['conciliado'],
            text=match_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Distribución de Tipos de Match",
            xaxis_title="Tipo de Match",
            yaxis_title="Cantidad",
            height=400
        )
        
        return fig
    
    def create_difference_analysis(self, reconciliation_result):
        """Crea análisis de diferencias en montos"""
        matched_df = reconciliation_result['matched']
        
        if matched_df.empty or 'Diferencia_Monto' not in matched_df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de diferencias",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        diferencias = matched_df['Diferencia_Monto'].dropna()
        
        if diferencias.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay diferencias en montos", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        fig = go.Figure(data=[go.Histogram(
            x=diferencias,
            nbinsx=20,
            marker_color=self.colors['diferencia'],
            opacity=0.7
        )])
        
        fig.update_layout(
            title="Distribución de Diferencias en Montos",
            xaxis_title="Diferencia ($)",
            yaxis_title="Frecuencia",
            height=400
        )
        
        return fig
    
    def create_daily_summary(self, reconciliation_result):
        """Crea resumen diario de conciliación"""
        matched_df = reconciliation_result['matched']
        
        if matched_df.empty or 'Fecha_Banco' not in matched_df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos diarios", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Detectar columna de fecha dinámicamente
        fecha_col = None
        for col in ['Fecha_Banco', 'Fecha_ban', 'Fecha']:
            if col in matched_df.columns:
                fecha_col = col
                break
        
        if not fecha_col:
            fig = go.Figure()
            fig.add_annotation(text="No se encontró columna de fecha", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Detectar columna de monto dinámicamente
        monto_col = None
        for col in ['Monto_Banco', 'Monto', 'Débito', 'Crédito']:
            if col in matched_df.columns:
                monto_col = col
                break
        
        if not monto_col:
            monto_col = 'Cantidad'  # Fallback para contar
        
        # Agrupar por fecha
        matched_df['Fecha'] = pd.to_datetime(matched_df[fecha_col]).dt.date
        
        # Verificar si existe columna verificada, si no agregarla
        if 'verificada' not in matched_df.columns:
            matched_df['verificada'] = 'v'  # Marcar todos como verificados por defecto
        
        # Configurar agregaciones dinámicamente
        agg_dict = {'verificada': 'count'}  # Siempre contar registros
        if monto_col in matched_df.columns and monto_col != 'Cantidad':
            agg_dict[monto_col] = 'sum'
        
        daily_summary = matched_df.groupby('Fecha').agg(agg_dict).round(2)
        
        # Renombrar columnas dinámicamente
        if len(agg_dict) == 1:
            daily_summary.columns = ['Cantidad']
        else:
            daily_summary.columns = ['Cantidad', 'Monto_Total']
        
        daily_summary = daily_summary.reset_index()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Cantidad de Transacciones por Día', 'Monto Total por Día'],
            vertical_spacing=0.15
        )
        
        # Cantidad por día
        fig.add_trace(
            go.Bar(
                x=daily_summary['Fecha'],
                y=daily_summary['Cantidad'],
                name='Cantidad',
                marker_color=self.colors['conciliado']
            ),
            row=1, col=1
        )
        
        # Monto por día (solo si existe la columna)
        if 'Monto_Total' in daily_summary.columns:
            fig.add_trace(
                go.Bar(
                    x=daily_summary['Fecha'],
                    y=daily_summary['Monto_Total'],
                    name='Monto Total',
                    marker_color=self.colors['banco']
                ),
                row=2, col=1
            )
        else:
            # Si no hay monto, mostrar solo cantidad
            fig.add_trace(
                go.Bar(
                    x=daily_summary['Fecha'],
                    y=daily_summary['Cantidad'],
                    name='Cantidad (sin montos)',
                    marker_color=self.colors['no_conciliado']
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            title="Resumen Diario de Conciliación",
            height=600,
            showlegend=False
        )
        
        return fig
