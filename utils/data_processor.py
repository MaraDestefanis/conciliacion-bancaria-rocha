import pandas as pd
import numpy as np
import io
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """Clase para procesar y limpiar archivos bancarios y de sistema"""
    
    def __init__(self):
        self.bank_keywords = ['BRO', 'BROU', 'BANCO', 'BANK']
        self.system_keywords = ['AYP', 'SISTEMA', 'SYSTEM', 'LOGICO']
    
    def read_file(self, uploaded_file):
        """Lee un archivo subido y lo convierte a DataFrame"""
        if uploaded_file is None:
            raise ValueError("No se ha proporcionado ningún archivo")
        
        # Obtener el contenido del archivo
        file_content = uploaded_file.getvalue()
        
        # Determinar el tipo de archivo y leer
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(io.StringIO(file_content.decode('utf-8')))
        elif uploaded_file.name.endswith('.xls'):
            return pd.read_excel(io.BytesIO(file_content), engine='xlrd')
        elif uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        else:
            raise ValueError(f"Formato de archivo no soportado: {uploaded_file.name}")
    
    def is_bank_file(self, filename):
        """Determina si un archivo es del banco basado en su nombre"""
        filename_upper = filename.upper()
        return any(keyword in filename_upper for keyword in self.bank_keywords)
    
    def is_system_file(self, filename):
        """Determina si un archivo es del sistema basado en su nombre"""
        filename_upper = filename.upper()
        return any(keyword in filename_upper for keyword in self.system_keywords)
    
    def get_workflow_type(self, banco_filename, sistema_filename):
        """Determina el tipo de workflow basado en los nombres de archivo"""
        # Workflow 1: Cuentas 4103, 4355, 10377 (usan columna 'Fecha' en sistema)
        if any(account in banco_filename for account in ['4103', '4355', '10377']):
            return 'workflow_1'
        
        # Workflow 2: servima, scotia, brou mato (usan columna 'fec' en sistema)
        servima_keywords = ['servima', 'scotia', 'mato']
        if any(keyword in banco_filename.lower() for keyword in servima_keywords):
            return 'workflow_2'
            
        # Default al workflow 1
        return 'workflow_1'
    
    def _is_scotia_file(self, df):
        """Detecta si es un archivo del banco Scotia"""
        # Buscar patrones típicos de Scotia en las primeras filas
        for idx in range(min(20, len(df))):
            row_str = ' '.join(df.iloc[idx].astype(str).str.upper())
            if 'SCOTIA' in row_str or 'FECHA REFERENCIA' in row_str:
                return True
        return False
    
    def process_bank_file(self, df):
        """Procesa y limpia un archivo bancario siguiendo el método exacto del usuario"""
        df_clean = df.copy()
        print(f"📋 Procesando archivo banco: {len(df_clean)} filas, {len(df_clean.columns)} columnas")
        
        # Detectar si es archivo Scotia y aplicar procesamiento específico
        is_scotia = self._is_scotia_bank_file(df_clean)
        
        if is_scotia:
            print("🏦 Archivo Scotia detectado - aplicando procesamiento específico")
            # Buscar fila con "Dep. Origen" específico para Scotia
            header_row = None
            for idx in range(min(25, len(df_clean))):
                row_str = ' '.join(df_clean.iloc[idx].astype(str)).upper()
                if 'DEP. ORIGEN' in row_str and 'FECHA' in row_str:
                    header_row = idx
                    break
            
            if header_row is not None:
                df_clean = df_clean.iloc[header_row:].reset_index(drop=True)
                df_clean.columns = df_clean.iloc[0]
                df_clean = df_clean.drop(df_clean.index[0]).reset_index(drop=True)
                print(f"✅ Headers Scotia encontrados en fila {header_row}")
        else:
            # Método exacto del usuario: buscar fila con "Fecha" sin ":"
            fila_fecha = df_clean.apply(lambda fila: (
                fila.astype(str).str.contains("Fecha", case=False, na=False) & 
                ~fila.astype(str).str.contains(":", na=False)
            )).any(axis=1)
            
            if fila_fecha.any():
                indice_fecha = fila_fecha.idxmax()
                df_clean = df_clean.loc[indice_fecha:].reset_index(drop=True)
                df_clean.columns = df_clean.iloc[0]
                df_clean = df_clean.drop(df_clean.index[0]).reset_index(drop=True)
                print(f"✅ Headers banco encontrados en fila {indice_fecha}")
        
        # Aplicar corrección de codificación
        df_clean = self._corregir_columnas_codificacion(df_clean)
        
        # Eliminar filas después de "Saldo Final"
        valores_a_dejar = ["Saldo Final", "saldo final", "Saldo final", " Saldo anterior"]
        mask = df_clean.apply(lambda row: row.astype(str).str.strip().isin(valores_a_dejar).any(), axis=1)
        primera_fila_saldo = mask[mask].index[0] if mask.any() else None
        if primera_fila_saldo is not None:
            df_clean = df_clean.iloc[:primera_fila_saldo].reset_index(drop=True)
        
        # Eliminar columnas y filas completamente vacías
        df_clean = df_clean.dropna(axis=1, how="all").dropna(how="all").reset_index(drop=True)
        
        # Eliminar filas con "saldo inicial"
        filtro = df_clean.apply(lambda fila: fila.astype(str).str.contains(r'^saldo inicial$', case=False, regex=True)).any(axis=1)
        df_clean = df_clean[~filtro].reset_index(drop=True)
        
        # Procesar fechas usando método del usuario
        if "Fecha" in df_clean.columns:
            df_clean["Fecha"] = pd.to_datetime(df_clean["Fecha"], format="mixed", errors='coerce')
            df_clean["Fecha"] = df_clean["Fecha"].dt.normalize()
        
        # Convertir columnas de documento a string
        valores_str = ["Número de documento", " Concepto", "Comprobante"]
        columnas_existentes = [col for col in valores_str if col in df_clean.columns]
        for col in columnas_existentes:
            df_clean[col] = df_clean[col].astype(str)
        
        # Convertir columnas numéricas con mejor manejo de errores
        valores_num = ["Crédito", "Débito", "Saldo", "saldo"]
        columnas_existentes = [col for col in valores_num if col in df_clean.columns]
        for col in columnas_existentes:
            # Limpiar valores antes de conversión
            df_clean[col] = df_clean[col].astype(str).str.replace(',', '').str.replace('$', '').str.strip()
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
        
        # Agregar ID y rellenar NaN
        df_clean['ID_banco'] = range(1, len(df_clean) + 1)
        if "Crédito" in df_clean.columns and "Débito" in df_clean.columns:
            df_clean[["Crédito", "Débito"]] = df_clean[["Crédito", "Débito"]].fillna(0)
        
        # Limpiar tipos de datos para evitar errores de Arrow
        df_clean = self.clean_data_types(df_clean)
        
        print(f"✅ Banco procesado: {len(df_clean)} filas, columnas: {list(df_clean.columns)}")
        return df_clean
    
    def process_system_file(self, df):
        """Procesa y limpia un archivo del sistema siguiendo el método exacto del usuario"""
        df_clean = df.copy()
        print(f"📋 Procesando archivo sistema: {len(df_clean)} filas, {len(df_clean.columns)} columnas")
        
        # Método exacto del usuario: buscar fila que contiene exactamente 'Fecha' o 'fec' (sin dos puntos)
        mask = df_clean.apply(lambda fila: fila.astype(str).str.strip().str.match(r'^(Fecha|fec)$', case=False, na=False)).any(axis=1)
        
        if mask.any():
            indice_fecha = mask[mask].index[0]
            df_clean = df_clean.loc[indice_fecha:].reset_index(drop=True)
            df_clean.columns = df_clean.iloc[0]
            df_clean = df_clean.drop(df_clean.index[0]).reset_index(drop=True)
            print(f"✅ Headers sistema encontrados en fila {indice_fecha}")
        
        # Limpiar columnas y filas vacías
        df_clean = df_clean.dropna(axis=1, how="all").dropna(how="all").reset_index(drop=True)
        
        # Eliminar filas después de "Saldos Finales"
        saldos_finales = ["Saldos Finales", "Saldo Final"]
        columnas_busqueda = ['documento', 'Nro.Ref.Bco']
        patron = '|'.join(saldos_finales)
        
        for col in columnas_busqueda:
            if col in df_clean.columns:
                mask = df_clean[col].astype(str).str.strip().str.contains(patron, case=False, na=False)
                if mask.any():
                    primera_ocurrencia = mask[mask].index[0]
                    df_clean = df_clean.iloc[:primera_ocurrencia].reset_index(drop=True)
                    break
        
        # Limpiar formato de fechas (eliminar comillas simples)
        columnas_fecha = ['fec', 'Fecha']
        for col in columnas_fecha:
            if col in df_clean.columns:
                if not pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                    df_clean[col] = df_clean[col].astype(str).str.replace("^['´]", "", regex=True).str.strip()
        
        # Procesar fechas usando método del usuario
        columnas_fecha = ["fec", "Fecha"]
        columnas_existentes = [col for col in columnas_fecha if col in df_clean.columns]
        for col in columnas_existentes:
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], format='mixed', errors='coerce')
                df_clean[col] = df_clean[col].dt.normalize()
                print(f"✅ Columna '{col}' convertida a datetime")
            except Exception as e:
                print(f"❌ Error procesando columna '{col}': {e}")
        
        # Convertir columnas de referencia a string
        columnas_referencia = ["Nro.Ref.Bco", "documento"]
        columnas_existentes = [col for col in columnas_referencia if col in df_clean.columns]
        for col in columnas_existentes:
            try:
                df_clean[col] = df_clean[col].astype(str)
                print(f"✅ Columna '{col}' convertida a string")
            except Exception as e:
                print(f"❌ Error convirtiendo columna '{col}': {e}")
        
        # Convertir columnas numéricas
        columnas_numericas = ["Debe", "Haber", "Saldo", "debe", "haber", "saldo"]
        columnas_existentes = [col for col in columnas_numericas if col in df_clean.columns]
        for col in columnas_existentes:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Agregar ID
        df_clean['ID_sistema'] = range(1, len(df_clean) + 1)
        
        # Rellenar columnas contables con 0
        columnas_buscadas = ["debe", "haber", "Debe", "Haber"]
        columnas_existentes = [col for col in columnas_buscadas if col in df_clean.columns]
        if columnas_existentes:
            df_clean[columnas_existentes] = df_clean[columnas_existentes].fillna(0)
            print(f"✅ Columnas rellenadas con 0: {columnas_existentes}")
        
        # Eliminar filas con patrones de saldo
        patron = r'^\s*saldo\s+(?:inicial|anterior|final)\s*$'
        mask = df_clean.apply(
            lambda fila: fila.astype(str).str.contains(patron, case=False, regex=True)
        ).any(axis=1)
        if mask.any():
            df_clean = df_clean.drop(index=mask[mask].index[0]).reset_index(drop=True)
        
        print(f"✅ Sistema procesado: {len(df_clean)} filas, columnas: {list(df_clean.columns)}")
        return df_clean
    
    def _fix_duplicate_columns(self, df):
        """Arregla nombres de columnas duplicados"""
        columns = df.columns.tolist()
        new_columns = []
        column_counts = {}
        
        for col in columns:
            col_str = str(col).strip()
            if col_str == 'nan' or col_str == '' or pd.isna(col):
                col_str = 'Column_Unknown'
            
            if col_str in column_counts:
                column_counts[col_str] += 1
                new_col = f"{col_str}_{column_counts[col_str]}"
            else:
                column_counts[col_str] = 0
                new_col = col_str
            
            new_columns.append(new_col)
        
        df.columns = new_columns
        return df
    
    def _find_header_row(self, df, keywords):
        """Encuentra la fila que contiene los headers basada en palabras clave"""
        for idx, row in df.iterrows():
            row_str = ' '.join(row.astype(str).str.upper())
            # Buscar tanto 'FECHA' como 'FEC' para diferentes formatos
            date_keywords = ['FECHA', 'FEC', 'DATE']
            has_date = any(date_kw in row_str for date_kw in date_keywords)
            has_other_keywords = any(keyword.upper() in row_str for keyword in keywords if keyword.upper() not in date_keywords)
            
            if has_date or has_other_keywords:
                return idx
        return None
    
    def _clean_bank_data(self, df):
        """Limpia datos específicos del banco siguiendo la lógica del notebook original"""
        
        # Paso 1: Encontrar la fila que contiene "Fecha" (sin ":") y empezar desde ahí
        fila_fecha = df.apply(lambda fila: (
            fila.astype(str).str.contains("Fecha", case=False, na=False) & 
            ~fila.astype(str).str.contains(":", na=False)
        )).any(axis=1)
        
        if fila_fecha.any():
            indice_fecha = fila_fecha.idxmax()
            df = df.loc[indice_fecha:].reset_index(drop=True)
            
            # Usar primera fila como headers pero manejar duplicados
            new_headers = []
            used_names = set()
            
            for i, col_value in enumerate(df.iloc[0]):
                # Convertir a string y limpiar
                col_name = str(col_value).strip()
                
                # Si está vacío, usar posición de columna
                if not col_name or col_name.lower() in ['nan', 'none', '']:
                    col_name = f'Column_{i}'
                
                # Manejar duplicados agregando sufijo
                original_name = col_name
                counter = 1
                while col_name in used_names:
                    col_name = f"{original_name}_{counter}"
                    counter += 1
                
                used_names.add(col_name)
                new_headers.append(col_name)
            
            df.columns = new_headers
            df = df.drop(df.index[0]).reset_index(drop=True)
        
        # Paso 2: Eliminar filas desde "Saldo Final" hacia abajo
        valores_a_dejar = ["Saldo Final", "saldo final", "Saldo final", " Saldo anterior"]
        mask = df.apply(lambda row: row.astype(str).str.strip().isin(valores_a_dejar).any(), axis=1)
        primera_fila_saldo = mask[mask].index[0] if mask.any() else None
        
        if primera_fila_saldo is not None:
            df = df.iloc[:primera_fila_saldo].reset_index(drop=True)
        
        # Paso 3: Eliminar columnas y filas completamente vacías
        df = df.dropna(axis=1, how="all").dropna(how="all").reset_index(drop=True)
        
        # Paso 4: Eliminar filas que contengan "saldo inicial"
        filtro = df.apply(lambda fila: fila.astype(str).str.contains(r'^saldo inicial$', case=False, regex=True)).any(axis=1)
        df = df[~filtro].reset_index(drop=True)
        
        return df
    
    def _clean_system_data(self, df):
        """Limpia datos específicos del sistema siguiendo la lógica del notebook original"""
        
        # Paso 1: Encontrar la fila que contiene exactamente 'Fecha' o 'fec' y reorganizar
        mask = df.apply(lambda fila: fila.astype(str).str.strip().str.match(r'^(Fecha|fec)$', case=False, na=False)).any(axis=1)
        
        if mask.any():
            indice_fecha = mask[mask].index[0]
            df = df.loc[indice_fecha:].reset_index(drop=True)
            
            # Usar primera fila como headers pero manejar duplicados
            new_headers = []
            used_names = set()
            
            for i, col_value in enumerate(df.iloc[0]):
                # Convertir a string y limpiar
                col_name = str(col_value).strip()
                
                # Si está vacío, usar posición de columna
                if not col_name or col_name.lower() in ['nan', 'none', '']:
                    col_name = f'Column_{i}'
                
                # Manejar duplicados agregando sufijo
                original_name = col_name
                counter = 1
                while col_name in used_names:
                    col_name = f"{original_name}_{counter}"
                    counter += 1
                
                used_names.add(col_name)
                new_headers.append(col_name)
            
            df.columns = new_headers
            df = df.drop(df.index[0]).reset_index(drop=True)
        
        # Paso 2: Limpiar columnas y filas vacías
        df = df.dropna(axis=1, how="all").dropna(how="all").reset_index(drop=True)
        
        # Paso 3: Eliminar filas después de "Saldos Finales"
        saldos_finales = ["Saldos Finales", "Saldo Final"]
        columnas_busqueda = ['documento', 'Nro.Ref:Bco']
        patron = '|'.join(saldos_finales)
        
        for col in columnas_busqueda:
            if col in df.columns:
                mask = df[col].astype(str).str.strip().str.contains(patron, case=False, na=False)
                if mask.any():
                    primera_ocurrencia = mask[mask].index[0]
                    df = df.iloc[:primera_ocurrencia].reset_index(drop=True)
                    break
        
        return df
    
    def _normalize_bank_columns(self, df):
        """Normaliza los nombres de columnas del banco"""
        column_mapping = {
            'FECHA': 'Fecha',
            'FEC': 'Fecha',
            'Date': 'Fecha',
            'FECHA REFERENCIA': 'Fecha',  # Para archivos Scotia
            'DESCRIPCION': 'Descripcion',
            'DESCRIPCIÓN': 'Descripcion',
            'Description': 'Descripcion',
            'NUMERO DE DOCUMENTO': 'Numero_Documento',
            'NÚMERO DE DOCUMENTO': 'Numero_Documento',
            'NRO DOCUMENTO': 'Numero_Documento',
            'NRO. DOCUMENTO': 'Numero_Documento',
            'Document Number': 'Numero_Documento',
            'DOCUMENTO': 'Numero_Documento',
            'DEBITO': 'Debito',
            'DÉBITO': 'Debito',
            'DEB': 'Debito',
            'Debit': 'Debito',
            'CREDITO': 'Credito',
            'CRÉDITO': 'Credito',
            'CRED': 'Credito',
            'Credit': 'Credito',
            'ASUNTO': 'Asunto',
            'Subject': 'Asunto',
            'CONCEPTO': 'Asunto',
            'DEPENDENCIA': 'Dependencia',
            'DEP': 'Dependencia',
            'DEP. ORIGEN': 'Dep_Origen',  # Para archivos Scotia
            'COMPROBANTE': 'Comprobante'
        }
        
        # Normalizar nombres de columnas
        df.columns = df.columns.astype(str)
        new_columns = []
        for col in df.columns:
            col_upper = col.strip().upper()
            new_col = column_mapping.get(col_upper, col.strip())
            new_columns.append(new_col)
        
        df.columns = new_columns
        
        return df
    
    def _normalize_system_columns(self, df):
        """Normaliza los nombres de columnas del sistema"""
        # Asegurar que las columnas son strings y limpias
        df.columns = [str(col).strip() for col in df.columns]
        
        # Mapeo más específico para sistema
        column_mapping = {
            'FECHA': 'Fecha',
            'FEC': 'Fecha',
            'Date': 'Fecha',
            'NRO.TRANS.': 'Nro.Trans.',
            'NRO TRANS': 'Nro.Trans.',
            'NROTRANS': 'Nro.Trans.',
            'NRO.REF.BCO': 'Nro.Ref.Bco',
            'NRO REF BCO': 'Nro.Ref.Bco',
            'NROREFBCO': 'Nro.Ref.Bco',
            'REF.BCO': 'Nro.Ref.Bco',
            'REFBCO': 'Nro.Ref.Bco',
            'TIPO VALOR': 'Tipo Valor',
            'TIPOVALOR': 'Tipo Valor',
            'CONCEPTO': 'Concepto',
            'DETALLE': 'Detalle',
            'DEBE': 'Debe',
            'HABER': 'Haber',
            'SALDO': 'Saldo',
            'ESTADO': 'Estado',
            'DOCUMENTO': 'documento',
            'CLIPROV': 'cliprov',
            'debe': 'debe',
            'haber': 'haber',
            'saldo': 'saldo'
        }
        
        # Aplicar mapeo y verificar duplicados
        new_columns = []
        used_names = set()
        
        for i, col in enumerate(df.columns):
            col_upper = str(col).strip().upper()
            new_col = column_mapping.get(col_upper, str(col).strip())
            
            # Evitar duplicados agregando sufijo si es necesario
            original_new_col = new_col
            counter = 1
            while new_col in used_names:
                new_col = f"{original_new_col}_{counter}"
                counter += 1
            
            used_names.add(new_col)
            new_columns.append(new_col)
        
        df.columns = new_columns
        
        return df
    
    def _process_dates_and_amounts(self, df):
        """Procesa fechas y montos en el DataFrame"""
        # Procesar fechas - buscar cualquier columna que contenga fecha
        date_columns = ['Fecha', 'Date', 'FEC']
        date_col_found = None
        
        # Buscar columna de fecha
        for col in df.columns:
            col_upper = str(col).upper()
            if any(date_kw in col_upper for date_kw in ['FECHA', 'FEC', 'DATE']):
                date_col_found = col
                break
        
        if date_col_found:
            # Renombrar a 'Fecha' para estandarizar
            if date_col_found != 'Fecha':
                df = df.rename(columns={date_col_found: 'Fecha'})
            
            # Formatear fecha siguiendo el notebook original - formato d/m/Y
            df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors='coerce', dayfirst=True)
            df["Fecha"] = df["Fecha"].dt.normalize()
        
        # Convertir columnas específicas a string (del notebook original)
        valores_str = ["Número de documento", " Concepto", "Concepto"]
        columnas_existentes = [col for col in valores_str if col in df.columns]
        
        for col in columnas_existentes:
            df[col] = df[col].astype(str)
        
        # Corregir problemas de encoding
        df = self._corregir_columnas_codificacion(df)
        
        # Procesar montos (débito, crédito, monto) - convertir a numérico
        valores_num = ["Crédito", "Débito", "Saldo", "saldo"]
        columnas_existentes = [col for col in valores_num if col in df.columns]
        
        for col in columnas_existentes:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Agregar ID y rellenar NaN en columnas numéricas (del notebook original)
        df['ID_banco'] = range(1, len(df) + 1)
        if 'Crédito' in df.columns and 'Débito' in df.columns:
            df[["Crédito", "Débito"]] = df[["Crédito", "Débito"]].fillna(0)
        
        return df
    
    def _convert_to_numeric(self, series):
        """Convierte una serie a numérica, manejando diferentes formatos"""
        # Reemplazar comas por puntos para decimales
        series_clean = series.astype(str).str.replace(',', '.')
        
        # Remover caracteres no numéricos excepto punto y signo negativo
        series_clean = series_clean.str.replace(r'[^\d.-]', '', regex=True)
        
        # Convertir a numérico
        return pd.to_numeric(series_clean, errors='coerce')
    
    def get_summary(self, df, file_type="archivo"):
        """Genera un resumen del DataFrame procesado"""
        summary = {
            'tipo': file_type,
            'filas': len(df),
            'columnas': len(df.columns),
            'columnas_disponibles': list(df.columns),
            'fecha_desde': None,
            'fecha_hasta': None,
            'total_montos': None,
            'valores_nulos': df.isnull().sum().sum()
        }
        
        # Información de fechas
        if 'Fecha' in df.columns:
            dates = pd.to_datetime(df['Fecha'], errors='coerce')
            summary['fecha_desde'] = dates.min()
            summary['fecha_hasta'] = dates.max()
        
        # Información de montos
        amount_cols = ['Monto', 'Monto_Neto', 'Credito', 'Debito']
        for col in amount_cols:
            if col in df.columns:
                total = df[col].sum()
                if not pd.isna(total):
                    summary[f'total_{col.lower()}'] = total
        
        return summary
    
    def clean_data_types(self, df):
        """Limpia tipos de datos mixtos para evitar errores de Arrow"""
        df_clean = df.copy()
        
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                # Convertir todos los valores a string para consistencia
                df_clean[col] = df_clean[col].astype(str)
                # Reemplazar 'nan' strings con valores vacíos
                df_clean[col] = df_clean[col].replace('nan', '')
        
        return df_clean
    
    def _corregir_columnas_codificacion(self, df):
        """Corrige nombres de columnas mal codificados por problemas de encoding"""
        column_corrections = {
            "DÃ©bito": "Débito",
            "CrÃ©dito": "Crédito",
            "DescripciÃ³n": "Descripción",
            "NÃºmero": "Número"
        }
        
        for old_name, new_name in column_corrections.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        return df
    
    def _is_scotia_bank_file(self, df):
        """Detecta si es un archivo del banco Scotia específicamente"""
        # Buscar patrones típicos de Scotia en las primeras filas
        for idx in range(min(20, len(df))):
            row_str = ' '.join(df.iloc[idx].astype(str)).upper()
            if 'SCOTIA' in row_str or 'FECHA REFERENCIA' in row_str:
                return True
        return False
    
    def _procesar_columnas_fecha_sistema(self, df):
        """Detecta columnas de fecha ('fec' o 'Fecha') y las convierte a datetime normalizado"""
        columnas_fecha = ["fec", "Fecha"]
        columnas_existentes = [col for col in columnas_fecha if col in df.columns]
        
        for col in columnas_existentes:
            try:
                print(f"🔍 Procesando columna fecha '{col}' - muestra: {df[col].head(3).tolist()}")
                
                # Usar tu recomendación: mixed y luego normalize
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col], format='mixed', errors='coerce')
                    df[col] = df[col].dt.normalize()
                
                exitosos = len(df) - df[col].isna().sum()
                print(f"✅ Columna '{col}' procesada: {exitosos}/{len(df)} fechas válidas")
                
            except Exception as e:
                print(f"❌ Error procesando columna '{col}': {e}")
                # Fallback si falla
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df[col] = df[col].dt.normalize()
                    exitosos = len(df) - df[col].isna().sum()
                    print(f"✅ Fallback exitoso: {exitosos}/{len(df)} fechas válidas")
                except:
                    print(f"❌ Fallback también falló para '{col}'")
        
        return df
    
    def _convertir_columnas_str_sistema(self, df):
        """Detecta columnas de referencia y las convierte a string"""
        columnas_referencia = ["Nro.Ref.Bco", "documento"]
        columnas_existentes = [col for col in columnas_referencia if col in df.columns]
        
        for col in columnas_existentes:
            try:
                df[col] = df[col].astype(str)
            except Exception as e:
                print(f"Error convirtiendo columna '{col}': {e}")
        
        return df
    
    def _convertir_columnas_numericas_sistema(self, df):
        """Convierte columnas numéricas del sistema"""
        columnas_numericas = ["Debe", "Haber", "Saldo", "debe", "haber", "saldo"]
        columnas_existentes = [col for col in columnas_numericas if col in df.columns]
        
        for col in columnas_existentes:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _rellenar_columnas_contables_sistema(self, df):
        """Detecta columnas contables específicas y las rellena con 0"""
        columnas_buscadas = ["debe", "haber", "Debe", "Haber"]
        columnas_existentes = [col for col in columnas_buscadas if col in df.columns]
        
        if columnas_existentes:
            df[columnas_existentes] = df[columnas_existentes].fillna(0)
        
        return df
