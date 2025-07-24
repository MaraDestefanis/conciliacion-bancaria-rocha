import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

class ReconciliationEngine:
    """Motor de conciliación bancaria"""
    
    def __init__(self, tolerance_days=10):
        self.tolerance_days = tolerance_days
        self.quality_metrics = {}
        self.workflow_type = 'workflow_1'  # Default
        # Solo comparación exacta de enteros para montos
        
    def reconcile(self, banco_df, sistema_df, workflow_type='workflow_1'):
        """Realiza la conciliación entre archivos bancarios y de sistema"""
        self.workflow_type = workflow_type
        
        print(f"🔍 Iniciando conciliación - {workflow_type}:")
        print(f"   Banco: {len(banco_df)} filas, columnas: {list(banco_df.columns)}")
        print(f"   Sistema: {len(sistema_df)} filas, columnas: {list(sistema_df.columns)}")
        
        # ANÁLISIS DE CALIDAD DE DATOS
        print("🔍 Analizando calidad de datos...")
        quality_report = self._analyze_data_quality(banco_df, sistema_df)
        
        # Preparar datos según el workflow
        banco_clean = self._prepare_bank_data(banco_df.copy())
        sistema_clean = self._prepare_system_data(sistema_df.copy())
        
        print(f"📊 Datos preparados:")
        print(f"   Banco: {len(banco_clean)} filas")
        print(f"   Sistema: {len(sistema_clean)} filas")
        
        # Verificar montos de ejemplo
        if len(banco_clean) > 0:
            print(f"   Ejemplo banco - Monto_Neto: {banco_clean.iloc[0].get('Monto_Neto', 'N/A')}")
        if len(sistema_clean) > 0:
            print(f"   Ejemplo sistema - Monto: {sistema_clean.iloc[0].get('Monto', 'N/A')}")
        
        # Realizar matching
        matched, unmatched_banco, unmatched_sistema = self._perform_matching(
            banco_clean, sistema_clean
        )
        
        print(f"✅ Resultado conciliación:")
        print(f"   Matches: {len(matched)}")
        print(f"   Sin conciliar banco: {len(unmatched_banco)}")
        print(f"   Sin conciliar sistema: {len(unmatched_sistema)}")
        
        # Generar estadísticas
        stats = self._generate_statistics(matched, unmatched_banco, unmatched_sistema)
        
        return {
            'matched': matched,
            'unmatched_banco': unmatched_banco,
            'unmatched_sistema': unmatched_sistema,
            'banco_data': banco_clean,
            'sistema_data': sistema_clean,
            'statistics': stats,
            'workflow_type': workflow_type
        }
    
    def _prepare_bank_data(self, df):
        """Prepara datos bancarios para conciliación"""
        # Mantener ID_banco existente si ya existe
        if 'ID_banco' not in df.columns:
            df['ID_banco'] = range(1, len(df) + 1)
        df['Origen'] = 'Banco'
        
        # Asegurar que tenemos las columnas necesarias (usando nombres correctos del notebook)
        if 'Monto_Neto' not in df.columns:
            if 'Crédito' in df.columns and 'Débito' in df.columns:
                df['Monto_Neto'] = df['Crédito'].fillna(0) - df['Débito'].fillna(0)
            elif 'Credito' in df.columns and 'Debito' in df.columns:
                df['Monto_Neto'] = df['Credito'].fillna(0) - df['Debito'].fillna(0)
            elif 'Monto' in df.columns:
                df['Monto_Neto'] = df['Monto']
            else:
                df['Monto_Neto'] = 0
        
        # Normalizar fechas para banco
        if 'Fecha' in df.columns:
            df['Fecha_Banco'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.normalize()
        
        # Para archivos Scotia, el documento está en 'Comprobante'
        if 'Comprobante' in df.columns and 'Número de documento' not in df.columns:
            df['Documento_Banco'] = df['Comprobante'].astype(str)
        elif 'Número de documento' in df.columns:
            df['Documento_Banco'] = df['Número de documento'].astype(str)
        
        # Columna de matching
        df['Matched'] = False
        df['Match_ID'] = None
        
        return df
    
    def _prepare_system_data(self, df):
        """Prepara datos del sistema para conciliación"""
        # Mantener ID_sistema existente si ya existe
        if 'ID_sistema' not in df.columns:
            df['ID_sistema'] = range(1, len(df) + 1)
        df['Origen'] = 'Sistema'
        
        # Asegurar columna de monto (usando nombres correctos del notebook)
        if 'Monto' not in df.columns:
            if 'Debe' in df.columns and 'Haber' in df.columns:
                # Para sistema: primero convertir a numérico
                df['Debe'] = pd.to_numeric(df['Debe'], errors='coerce').fillna(0)
                df['Haber'] = pd.to_numeric(df['Haber'], errors='coerce').fillna(0)
                # Para sistema: usar valores absolutos directamente (no restar)
                df['Monto'] = df['Debe'] + df['Haber']  # Sumar ambos para obtener monto total
                # Si ambos están vacíos, usar el que tenga valor
                mask_debe = df['Debe'] > 0
                mask_haber = df['Haber'] > 0
                df.loc[mask_debe & ~mask_haber, 'Monto'] = df.loc[mask_debe & ~mask_haber, 'Debe']
                df.loc[~mask_debe & mask_haber, 'Monto'] = df.loc[~mask_debe & mask_haber, 'Haber']
            elif 'debe' in df.columns and 'haber' in df.columns:
                # Workflow 2: debe/haber en minúsculas
                df['debe'] = pd.to_numeric(df['debe'], errors='coerce').fillna(0)
                df['haber'] = pd.to_numeric(df['haber'], errors='coerce').fillna(0)
                df['Monto'] = df['haber'].fillna(0) - df['debe'].fillna(0)
            elif 'Monto_Neto' in df.columns:
                df['Monto'] = df['Monto_Neto']
            else:
                df['Monto'] = 0
        
        # Normalizar fechas según el workflow
        if self.workflow_type == 'workflow_2' and 'fec' in df.columns:
            df['Fecha_Sistema'] = pd.to_datetime(df['fec'], errors='coerce').dt.normalize()
        elif self.workflow_type == 'workflow_1' and 'Fecha' in df.columns:
            # Para Workflow 1 (cuentas 4103, 4355, 10377): usar columna 'Fecha'
            df['Fecha_Sistema'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.normalize()
        elif 'Fecha' in df.columns:
            df['Fecha_Sistema'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.normalize()
        elif 'fec' in df.columns:
            df['Fecha_Sistema'] = pd.to_datetime(df['fec'], errors='coerce').dt.normalize()
        
        df['Matched'] = False
        df['Match_ID'] = None
        
        return df
    
    def _perform_matching(self, banco_df, sistema_df):
        """Realiza el matching entre transacciones"""
        if self.workflow_type == 'workflow_2':
            return self._perform_workflow2_matching(banco_df, sistema_df)
        else:
            return self._perform_workflow1_matching(banco_df, sistema_df)
    
    def _perform_workflow1_matching(self, banco_df, sistema_df):
        """Matching para Workflow 1 usando tail matching (últimos 3 dígitos) + tolerancia de fechas como en notebook"""
        print("🔄 Ejecutando Workflow 1 con tail matching")
        
        # Copias seguras
        bco = banco_df.copy()
        sis = sistema_df.copy()
        
        # Función para obtener los últimos 3 dígitos como en tu notebook
        def cola_3(s):
            s = s.fillna('').astype(str).str.strip()
            return s.str[-3:].str.zfill(3)  # '7' -> '007'
        
        # Preparar colas de 3 dígitos para el banco (usar Numero_Documento)
        doc_col_banco = None
        for col in ['Numero_Documento', 'Número de documento']:
            if col in bco.columns:
                doc_col_banco = col
                break
        
        if not doc_col_banco:
            print("⚠️ No se encontró columna de número de documento en banco")
            return pd.DataFrame(), banco_df, sistema_df
            
        bco['tail'] = cola_3(bco[doc_col_banco])
        
        # Preparar colas de 3 dígitos para el sistema (usar Nro.Ref.Bco)
        if 'Nro.Ref.Bco' not in sis.columns:
            print("⚠️ No se encontró columna Nro.Ref.Bco en sistema")
            return pd.DataFrame(), banco_df, sistema_df
            
        sis['tail'] = cola_3(sis['Nro.Ref.Bco'])
        
        # Merge por cola de 3 dígitos
        merged = sis.merge(
            bco,
            on='tail',
            how='inner',
            suffixes=('_sistema', '_banco'),
            validate='many_to_many'
        )
        
        if merged.empty:
            print("⚠️ No hubo coincidencias por cola de 3")
            return pd.DataFrame(), banco_df, sistema_df
        
        print(f"📋 Encontrados {len(merged)} matches por tail matching")
        
        # Debugging de fechas antes de procesar
        print(f"🔍 Debug fechas antes de conversión:")
        print(f"   Muestra Fecha_sistema: {merged['Fecha_sistema'].head(3).tolist()}")
        print(f"   Muestra Fecha_banco: {merged['Fecha_banco'].head(3).tolist()}")
        
        # Procesar fechas con más opciones de formato y normalizar
        merged['Fecha_sistema'] = pd.to_datetime(merged['Fecha_sistema'], format='mixed', errors='coerce').dt.normalize()
        merged['Fecha_banco'] = pd.to_datetime(merged['Fecha_banco'], format='mixed', errors='coerce').dt.normalize()
        
        # Verificar conversión exitosa
        fecha_sistema_nulas = merged['Fecha_sistema'].isna().sum()
        fecha_banco_nulas = merged['Fecha_banco'].isna().sum()
        print(f"📊 Fechas convertidas - Sistema NaN: {fecha_sistema_nulas}, Banco NaN: {fecha_banco_nulas}")
        
        if fecha_sistema_nulas > 0 or fecha_banco_nulas > 0:
            print("⚠️ Problemas con conversión de fechas - intentando formatos alternativos")
            # Intentar otros formatos comunes
            if fecha_sistema_nulas > 0:
                merged['Fecha_sistema'] = pd.to_datetime(merged['Fecha_sistema'], dayfirst=True, errors='coerce')
            if fecha_banco_nulas > 0:
                merged['Fecha_banco'] = pd.to_datetime(merged['Fecha_banco'], dayfirst=True, errors='coerce')
        
        # Calcular diferencias solo si las fechas son válidas
        # CORRECCIÓN: dif_dias debe ser positivo cuando fecha_sistema > fecha_banco
        merged['dif_dias'] = (merged['Fecha_sistema'] - merged['Fecha_banco']).dt.days
        
        # Calcular diferencia de montos
        merged['monto_dif'] = merged['Monto'] - merged['Monto_Neto']
        
        print(f"📊 Análisis de diferencias de fechas:")
        print(f"   Min diferencia: {merged['dif_dias'].min()}")
        print(f"   Max diferencia: {merged['dif_dias'].max()}")
        valid_diffs = merged['dif_dias'].notna()
        print(f"   Diferencias válidas: {valid_diffs.sum()} de {len(merged)}")
        if valid_diffs.any():
            in_range = ((merged['dif_dias'] >= 0) & (merged['dif_dias'] <= self.tolerance_days) & valid_diffs).sum()
            print(f"   Registros con dif 0 a +{self.tolerance_days}: {in_range}")
        
        # CORRECCIÓN CRÍTICA: SOLO verificar transacciones que cumplan AMBAS condiciones
        merged['verificada'] = ''
        merged['match_quality'] = ''
        
        # ÚNICA CONDICIÓN DE VERIFICACIÓN: fecha sistema dentro de tolerancia DESPUÉS de fecha banco + montos enteros iguales
        print(f"🔍 DEBUG - Aplicando tolerancia: fecha sistema debe estar 0 a +{self.tolerance_days} días después de fecha banco")
        print(f"🔍 DEBUG - Comparando solo la parte entera de los montos (sin decimales)")
        
        # Convertir montos a enteros para comparación (sin decimales)
        merged['Monto_entero'] = merged['Monto'].fillna(0).astype(float).astype(int)
        merged['Monto_Neto_entero'] = merged['Monto_Neto'].fillna(0).astype(float).astype(int)
        
        verificacion_estricta = (
            (merged['dif_dias'] >= 0) &  # Fecha sistema igual o posterior a fecha banco
            (merged['dif_dias'] <= self.tolerance_days) &  # Fecha sistema dentro de tolerancia
            merged['dif_dias'].notna() &  # Solo fechas válidas
            (merged['Monto_entero'] == merged['Monto_Neto_entero'])  # Montos enteros iguales
        )
        merged.loc[verificacion_estricta, 'verificada'] = 'v'
        
        # Clasificar calidad del match para las verificadas
        # Match exacto: fecha exacta
        exact_match = verificacion_estricta & (merged['dif_dias'] == 0)
        merged.loc[exact_match, 'match_quality'] = 'exacto'
        
        # Match por tolerancia: dentro de rango pero no exacto
        tolerance_match = verificacion_estricta & (merged['dif_dias'] != 0)
        merged.loc[tolerance_match, 'match_quality'] = 'tolerancia_fecha'
        
        # VALIDACIÓN ADICIONAL: revisar duplicados
        duplicated_banco = merged['Número de documento'].duplicated(keep=False)
        duplicated_sistema = merged['Nro.Ref.Bco'].duplicated(keep=False)
        
        if duplicated_banco.any() or duplicated_sistema.any():
            print(f"⚠️ Advertencia: {duplicated_banco.sum()} duplicados banco, {duplicated_sistema.sum()} duplicados sistema")
        
        # Filtrar solo las verificadas
        verificadas = merged[merged['verificada'] == 'v'].copy()
        verificadas.reset_index(drop=True, inplace=True)
        
        print(f"🔍 DEBUG - Análisis de verificación:")
        print(f"   Total registros después del merge: {len(merged)}")
        print(f"   Registros marcados como verificados: {len(verificadas)}")
        if len(verificadas) > 0:
            print(f"   Muestra diferencias de días: {verificadas['dif_dias'].head(3).tolist()}")
            print(f"   Muestra montos banco (decimales): {verificadas['Monto_Neto'].head(3).tolist()}")
            print(f"   Muestra montos sistema (decimales): {verificadas['Monto'].head(3).tolist()}")
            print(f"   Muestra montos banco (enteros): {verificadas['Monto_Neto_entero'].head(3).tolist()}")
            print(f"   Muestra montos sistema (enteros): {verificadas['Monto_entero'].head(3).tolist()}")
            print(f"   Muestra fechas banco: {verificadas['Fecha_banco'].head(3).tolist()}")
            print(f"   Muestra fechas sistema: {verificadas['Fecha_sistema'].head(3).tolist()}")
            # Verificar si hay diferencias de días fuera del rango
            dif_fuera_rango = verificadas[(verificadas['dif_dias'] < 0) | (verificadas['dif_dias'] > self.tolerance_days)]
            if len(dif_fuera_rango) > 0:
                print(f"   ⚠️ PROBLEMA: {len(dif_fuera_rango)} registros verificados con fechas fuera del rango 0 a +{self.tolerance_days}")
                print(f"      Diferencias problemáticas: {dif_fuera_rango['dif_dias'].head(5).tolist()}")
            else:
                print(f"   ✅ Todas las verificadas cumplen: fechas 0 a +{self.tolerance_days} días Y montos enteros iguales")
        
        if verificadas.empty:
            print("⚠️ No se encontraron registros dentro de la tolerancia de fechas Y montos exactos")
            return pd.DataFrame(), banco_df, sistema_df
        
        # Limpiar columnas temporales
        verificadas = verificadas.drop(columns=['tail', 'dif_dias', 'Monto_entero', 'Monto_Neto_entero'], errors='ignore')
        
        # Deduplicar por ID_sistema e ID_banco como en tu notebook
        verificadas = verificadas.drop_duplicates(subset='ID_sistema', keep='first')
        verificadas = verificadas.drop_duplicates(subset='ID_banco', keep='first')
        verificadas = verificadas.reset_index(drop=True)
        
        # Calcular no coincidentes
        matched_sistema_ids = verificadas['ID_sistema'].unique()
        unmatched_sistema = sistema_df[~sistema_df['ID_sistema'].isin(matched_sistema_ids)]
        
        matched_banco_ids = verificadas['ID_banco'].unique()
        unmatched_banco = banco_df[~banco_df['ID_banco'].isin(matched_banco_ids)]
        
        print(f"🎯 Workflow 1 completado: {len(verificadas)} registros verificados")
        return verificadas, unmatched_banco, unmatched_sistema
    
    def _perform_workflow2_matching(self, banco_df, sistema_df):
        """Matching para Workflow 2 usando merge directo como en el código original"""
        # Preparar columnas siguiendo exactamente el código original
        banco_df = banco_df.copy()
        sistema_df = sistema_df.copy()
        
        # Asegurar que tenemos las columnas necesarias con nombres correctos
        if 'Crédito' not in banco_df.columns:
            banco_df['Crédito'] = banco_df.get('Credito', 0)
        if 'Débito' not in banco_df.columns:
            banco_df['Débito'] = banco_df.get('Debito', 0)
        
        # Convertir montos a enteros exactamente como en el código original
        banco_df['Crédito_int'] = banco_df['Crédito'].fillna(0).astype(int)
        banco_df['Débito_int'] = banco_df['Débito'].fillna(0).astype(int)
        sistema_df['Debe_int'] = sistema_df['debe'].fillna(0).astype(int)
        sistema_df['Haber_int'] = sistema_df['haber'].fillna(0).astype(int)
        
        # Asegurar formato de fecha correcto para sistema (fec)
        sistema_df['fec'] = pd.to_datetime(sistema_df['fec'], format="%d/%m/%Y", errors='coerce', dayfirst=True)
        
        # Merge directo usando la lógica invertida del código original
        # Haber(sistema) vs Débito(banco), Debe(sistema) vs Crédito(banco)
        merged = sistema_df.merge(
            banco_df,
            how='inner',
            left_on=['Haber_int', 'Debe_int'],    # Claves del sistema
            right_on=['Débito_int', 'Crédito_int'],  # Claves del banco
            suffixes=('_sistema', '_banco')
        )
        
        if len(merged) == 0:
            # No hay matches con merge directo
            return pd.DataFrame(), banco_df, sistema_df
        
        # Aplicar condición de fecha (máximo 3 días como en el código original)
        condition = (merged["Fecha"] <= merged["fec"] + pd.Timedelta(days=3))
        
        # Filtrar solo los registros que cumplen la condición de fecha
        verificadas = merged[condition].copy()
        
        if len(verificadas) == 0:
            return pd.DataFrame(), banco_df, sistema_df
        
        # Eliminar duplicados como en el código original
        verificadas = verificadas.drop_duplicates(subset='ID_sistema', keep='first')
        verificadas = verificadas.drop_duplicates(subset='ID_banco', keep='first')
        
        # Crear unmatched DataFrames
        matched_banco_ids = verificadas['ID_banco'].tolist()
        matched_sistema_ids = verificadas['ID_sistema'].tolist()
        
        unmatched_banco = banco_df[~banco_df['ID_banco'].isin(matched_banco_ids)].copy()
        unmatched_sistema = sistema_df[~sistema_df['ID_sistema'].isin(matched_sistema_ids)].copy()
        
        return verificadas, unmatched_banco, unmatched_sistema
    
    def _is_exact_match(self, row_banco, row_sistema):
        """Verifica si hay match exacto entre dos transacciones"""
        # Usar fechas normalizadas
        fecha_banco = row_banco.get('Fecha_Banco')
        fecha_sistema = row_sistema.get('Fecha_Sistema')
        
        if pd.isna(fecha_banco) or pd.isna(fecha_sistema):
            return False
        
        if fecha_banco.date() != fecha_sistema.date():
            return False
        
        # Comparar montos como enteros (sin decimales)
        monto_banco = int(float(row_banco.get('Monto_Neto', 0) or 0))
        monto_sistema = int(float(row_sistema.get('Monto', 0) or 0))
        
        return monto_banco == monto_sistema
    
    def _is_tolerant_match(self, row_banco, row_sistema, tolerance_days=None):
        """Verifica si hay match con tolerancia en fechas pero montos exactos"""
        if tolerance_days is None:
            tolerance_days = self.tolerance_days
            
        # Usar fechas normalizadas
        fecha_banco = row_banco.get('Fecha_Banco')
        fecha_sistema = row_sistema.get('Fecha_Sistema')
        
        if pd.isna(fecha_banco) or pd.isna(fecha_sistema):
            return False
        
        diff_days = abs((fecha_banco - fecha_sistema).days)
        if diff_days > tolerance_days:
            return False
        
        # Comparar montos como enteros (exactos)
        monto_banco = int(float(row_banco.get('Monto_Neto', 0) or 0))
        monto_sistema = int(float(row_sistema.get('Monto', 0) or 0))
        
        return monto_banco == monto_sistema
    
    def _is_document_match(self, row_banco, row_sistema):
        """Verifica match por número de documento/referencia"""
        # Usar documento normalizado
        doc_banco = str(row_banco.get('Documento_Banco', '')).strip()
        
        if self.workflow_type == 'workflow_1':
            doc_sistema = str(row_sistema.get('Nro.Ref.Bco', '')).strip()
        else:
            # Workflow 2: usar 'documento'
            doc_sistema = str(row_sistema.get('documento', '')).strip()
        
        if not doc_banco or not doc_sistema or doc_banco == 'nan' or doc_sistema == 'nan':
            return False
        
        # Match exacto de documento
        if doc_banco == doc_sistema:
            # Verificar que los montos como enteros sean iguales
            monto_banco = int(float(row_banco.get('Monto_Neto', 0) or 0))
            monto_sistema = int(float(row_sistema.get('Monto', 0) or 0))
            
            return monto_banco == monto_sistema
        
        return False
    
    def _create_match_record(self, row_banco, row_sistema, match_type):
        """Crea un registro de match"""
        return {
            'Match_Type': match_type,
            'Fecha_Banco': row_banco.get('Fecha'),
            'Fecha_Sistema': row_sistema.get('Fecha'),
            'Monto_Banco': row_banco.get('Monto_Neto', 0),
            'Monto_Sistema': row_sistema.get('Monto', 0),
            'Diferencia_Monto': float(row_banco.get('Monto_Neto', 0) or 0) - float(row_sistema.get('Monto', 0) or 0),
            'Documento_Banco': row_banco.get('Numero_Documento', ''),
            'Documento_Sistema': row_sistema.get('Documento', ''),
            'Descripcion_Banco': row_banco.get('Descripcion', ''),
            'Concepto_Sistema': row_sistema.get('Concepto', ''),
            'ID_Banco': row_banco.get('ID_Banco'),
            'ID_Sistema': row_sistema.get('ID_Sistema'),
            'Diferencia_Dias': self._calculate_date_diff(row_banco.get('Fecha'), row_sistema.get('Fecha'))
        }
    
    def _calculate_date_diff(self, fecha1, fecha2):
        """Calcula diferencia en días entre dos fechas"""
        try:
            f1 = pd.to_datetime(fecha1, errors='coerce')
            f2 = pd.to_datetime(fecha2, errors='coerce')
            
            if pd.isna(f1) or pd.isna(f2):
                return None
            
            return (f1 - f2).days
        except:
            return None
    
    def _generate_statistics(self, matched_df, unmatched_banco, unmatched_sistema):
        """Genera estadísticas de conciliación con análisis de totales detallado"""
        # Reconstruir datos originales combinando matched y unmatched
        banco_original = pd.concat([matched_df, unmatched_banco]) if not matched_df.empty else unmatched_banco
        sistema_original = pd.concat([matched_df, unmatched_sistema]) if not matched_df.empty else unmatched_sistema
        
        total_banco = len(banco_original)
        total_sistema = len(sistema_original)
        total_matched = len(matched_df) if not matched_df.empty else 0
        
        stats = {
            'total_transacciones_banco': total_banco,
            'total_transacciones_sistema': total_sistema,
            'total_conciliadas': total_matched,
            'sin_conciliar_banco': len(unmatched_banco),
            'sin_conciliar_sistema': len(unmatched_sistema),
            'porcentaje_conciliacion': (total_matched / max(total_banco, 1)) * 100,
            'diferencias_encontradas': total_matched
        }
        
        # ANÁLISIS DE TOTALES DETALLADO (siguiendo el código del usuario)
        if self.workflow_type == 'workflow_2':
            # Para Workflow 2: usar columnas debe/haber y Débito/Crédito
            stats.update(self._calculate_workflow2_totals(matched_df, unmatched_banco, unmatched_sistema))
        else:
            # Para Workflow 1: usar las columnas estándar
            stats.update(self._calculate_workflow1_totals(matched_df, unmatched_banco, unmatched_sistema))
        
        # Estadísticas de montos básicas
        if not matched_df.empty:
            # Calcular montos conciliados basado en las columnas disponibles
            if 'Débito' in matched_df.columns and 'Crédito' in matched_df.columns:
                debito_conciliado = matched_df['Débito'].fillna(0).sum()
                credito_conciliado = matched_df['Crédito'].fillna(0).sum()
                stats['monto_total_conciliado_banco'] = abs(debito_conciliado) + abs(credito_conciliado)
            elif 'Monto_Banco' in matched_df.columns:
                stats['monto_total_conciliado_banco'] = matched_df['Monto_Banco'].sum()
            
            if 'debe' in matched_df.columns and 'haber' in matched_df.columns:
                debe_conciliado = matched_df['debe'].fillna(0).sum()
                haber_conciliado = matched_df['haber'].fillna(0).sum()
                stats['monto_total_conciliado_sistema'] = abs(debe_conciliado) + abs(haber_conciliado)
            elif 'Debe' in matched_df.columns and 'Haber' in matched_df.columns:
                debe_conciliado = matched_df['Debe'].fillna(0).sum()
                haber_conciliado = matched_df['Haber'].fillna(0).sum()
                stats['monto_total_conciliado_sistema'] = abs(debe_conciliado) + abs(haber_conciliado)
            elif 'Monto_Sistema' in matched_df.columns:
                stats['monto_total_conciliado_sistema'] = matched_df['Monto_Sistema'].sum()
            
            if 'Diferencia_Monto' in matched_df.columns:
                stats['diferencia_total_montos'] = matched_df['Diferencia_Monto'].sum()
            
            # Estadísticas por tipo de match
            if 'Match_Type' in matched_df.columns:
                match_types = matched_df['Match_Type'].value_counts().to_dict()
                stats['tipos_match'] = match_types
        
        # Montos sin conciliar
        if not unmatched_banco.empty:
            if 'Débito' in unmatched_banco.columns and 'Crédito' in unmatched_banco.columns:
                debito_no_conciliado = unmatched_banco['Débito'].fillna(0).sum()
                credito_no_conciliado = unmatched_banco['Crédito'].fillna(0).sum()
                stats['monto_sin_conciliar_banco'] = abs(debito_no_conciliado) + abs(credito_no_conciliado)
            elif 'Monto_Neto' in unmatched_banco.columns:
                stats['monto_sin_conciliar_banco'] = abs(unmatched_banco['Monto_Neto'].sum())
        
        if not unmatched_sistema.empty:
            if 'debe' in unmatched_sistema.columns and 'haber' in unmatched_sistema.columns:
                debe_no_conciliado = unmatched_sistema['debe'].fillna(0).sum()
                haber_no_conciliado = unmatched_sistema['haber'].fillna(0).sum()
                stats['monto_sin_conciliar_sistema'] = abs(debe_no_conciliado) + abs(haber_no_conciliado)
            elif 'Debe' in unmatched_sistema.columns and 'Haber' in unmatched_sistema.columns:
                debe_no_conciliado = unmatched_sistema['Debe'].fillna(0).sum()
                haber_no_conciliado = unmatched_sistema['Haber'].fillna(0).sum()
                stats['monto_sin_conciliar_sistema'] = abs(debe_no_conciliado) + abs(haber_no_conciliado)
            elif 'Monto' in unmatched_sistema.columns:
                stats['monto_sin_conciliar_sistema'] = abs(unmatched_sistema['Monto'].sum())
        
        # Agregar métricas de calidad al resultado
        stats['quality_metrics'] = self.quality_metrics
        
        return stats
    
    def _analyze_data_quality(self, banco_df, sistema_df):
        """Analiza la calidad de los datos antes de la conciliación"""
        quality = {
            'banco_issues': [],
            'sistema_issues': [],
            'general_warnings': []
        }
        
        # Análisis del banco
        if 'Fecha' in banco_df.columns:
            null_dates_banco = banco_df['Fecha'].isna().sum()
            if null_dates_banco > 0:
                quality['banco_issues'].append(f"{null_dates_banco} fechas nulas en banco")
        
        if 'Número de documento' in banco_df.columns:
            null_docs_banco = banco_df['Número de documento'].isna().sum()
            duplicate_docs_banco = banco_df['Número de documento'].duplicated().sum()
            if null_docs_banco > 0:
                quality['banco_issues'].append(f"{null_docs_banco} números de documento nulos en banco")
            if duplicate_docs_banco > 0:
                quality['banco_issues'].append(f"{duplicate_docs_banco} números de documento duplicados en banco")
        
        # Análisis del sistema
        fecha_col = 'Fecha' if 'Fecha' in sistema_df.columns else 'fec' if 'fec' in sistema_df.columns else None
        if fecha_col:
            null_dates_sistema = sistema_df[fecha_col].isna().sum()
            if null_dates_sistema > 0:
                quality['sistema_issues'].append(f"{null_dates_sistema} fechas nulas en sistema")
        
        ref_col = 'Nro.Ref.Bco' if 'Nro.Ref.Bco' in sistema_df.columns else 'documento' if 'documento' in sistema_df.columns else None
        if ref_col:
            null_refs_sistema = sistema_df[ref_col].isna().sum()
            duplicate_refs_sistema = sistema_df[ref_col].duplicated().sum()
            if null_refs_sistema > 0:
                quality['sistema_issues'].append(f"{null_refs_sistema} referencias nulas en sistema")
            if duplicate_refs_sistema > 0:
                quality['sistema_issues'].append(f"{duplicate_refs_sistema} referencias duplicadas en sistema")
        
        # Análisis de rangos de fechas
        if fecha_col and 'Fecha' in banco_df.columns:
            try:
                banco_dates = pd.to_datetime(banco_df['Fecha'], errors='coerce')
                sistema_dates = pd.to_datetime(sistema_df[fecha_col], errors='coerce')
                
                banco_min = banco_dates.min()
                banco_max = banco_dates.max()
                sistema_min = sistema_dates.min()
                sistema_max = sistema_dates.max()
                
                if pd.notna(banco_min) and pd.notna(sistema_min):
                    date_gap = abs((banco_min - sistema_min).days)
                    if date_gap > 30:
                        quality['general_warnings'].append(f"Gran diferencia en rangos de fechas: {date_gap} días")
            except:
                quality['general_warnings'].append("Error analizando rangos de fechas")
        
        # Guardar métricas de calidad
        self.quality_metrics = quality
        
        # Imprimir warnings de calidad
        if quality['banco_issues']:
            print(f"⚠️ Problemas en banco: {'; '.join(quality['banco_issues'])}")
        if quality['sistema_issues']:
            print(f"⚠️ Problemas en sistema: {'; '.join(quality['sistema_issues'])}")
        if quality['general_warnings']:
            print(f"⚠️ Advertencias generales: {'; '.join(quality['general_warnings'])}")
        
        return quality
    
    def _calculate_workflow2_totals(self, verificadas, banco_noverif, sistema_noverif):
        """Calcula totales detallados para Workflow 2 siguiendo el código del usuario"""
        totals = {}
        
        # Reconstruir datos originales
        banco_original = pd.concat([verificadas, banco_noverif]) if not verificadas.empty else banco_noverif
        sistema_original = pd.concat([verificadas, sistema_noverif]) if not verificadas.empty else sistema_noverif
        
        # TOTALES ORIGINALES del banco y sistema
        totals['total_debito_original'] = banco_original.get('Débito', pd.Series([])).sum()
        totals['total_credito_original'] = banco_original.get('Crédito', pd.Series([])).sum()
        totals['total_debe_original'] = sistema_original.get('debe', pd.Series([])).sum()
        totals['total_haber_original'] = sistema_original.get('haber', pd.Series([])).sum()
        
        # TOTALES VERIFICADAS
        if not verificadas.empty:
            totals['total_debito_verificadas'] = verificadas.get('Débito', pd.Series([])).sum()
            totals['total_credito_verificadas'] = verificadas.get('Crédito', pd.Series([])).sum()
            totals['total_debe_verificadas'] = verificadas.get('debe', pd.Series([])).sum()
            totals['total_haber_verificadas'] = verificadas.get('haber', pd.Series([])).sum()
        else:
            totals['total_debito_verificadas'] = 0
            totals['total_credito_verificadas'] = 0
            totals['total_debe_verificadas'] = 0
            totals['total_haber_verificadas'] = 0
        
        # TOTALES NO VERIFICADAS
        totals['total_debito_no_verificadas'] = banco_noverif.get('Débito', pd.Series([])).sum()
        totals['total_credito_no_verificadas'] = banco_noverif.get('Crédito', pd.Series([])).sum()
        totals['total_debe_no_verificadas'] = sistema_noverif.get('debe', pd.Series([])).sum()
        totals['total_haber_no_verificadas'] = sistema_noverif.get('haber', pd.Series([])).sum()
        
        # SUMAS FINALES (Check)
        totals['total_debito_check'] = totals['total_debito_verificadas'] + totals['total_debito_no_verificadas']
        totals['total_credito_check'] = totals['total_credito_verificadas'] + totals['total_credito_no_verificadas']
        totals['total_debe_check'] = totals['total_debe_verificadas'] + totals['total_debe_no_verificadas']
        totals['total_haber_check'] = totals['total_haber_verificadas'] + totals['total_haber_no_verificadas']
        
        # DIFERENCIAS (redondeadas como en el código original)
        totals['dif_debito'] = round(totals['total_debito_original'] - totals['total_debito_check'])
        totals['dif_credito'] = round(totals['total_credito_original'] - totals['total_credito_check'])
        totals['dif_debe'] = round(totals['total_debe_original'] - totals['total_debe_check'])
        totals['dif_haber'] = round(totals['total_haber_original'] - totals['total_haber_check'])
        
        # PORCENTAJE DE VERIFICACIÓN
        if not sistema_original.empty and 'ID_sistema' in sistema_original.columns:
            suma_sistema = sistema_original['ID_sistema'].sum()
            if not verificadas.empty and 'ID_sistema' in verificadas.columns:
                suma_verificadas = verificadas['ID_sistema'].sum()
                totals['porcentaje_verificacion'] = (suma_verificadas / suma_sistema) * 100 if suma_sistema > 0 else 0
            else:
                totals['porcentaje_verificacion'] = 0
        else:
            totals['porcentaje_verificacion'] = 0
        
        return totals
    
    def _calculate_workflow1_totals(self, verificadas, banco_noverif, sistema_noverif):
        """Calcula totales básicos para Workflow 1"""
        totals = {}
        
        # Para Workflow 1, usar las columnas estándar
        banco_original = pd.concat([verificadas, banco_noverif]) if not verificadas.empty else banco_noverif
        sistema_original = pd.concat([verificadas, sistema_noverif]) if not verificadas.empty else sistema_noverif
        
        totals['total_banco_original'] = banco_original.get('Monto_Neto', pd.Series([])).sum()
        totals['total_sistema_original'] = sistema_original.get('Monto', pd.Series([])).sum()
        
        if not verificadas.empty:
            totals['total_verificadas'] = len(verificadas)
            totals['monto_verificadas'] = verificadas.get('Monto_Banco', pd.Series([])).sum()
        else:
            totals['total_verificadas'] = 0
            totals['monto_verificadas'] = 0
        
        return totals
