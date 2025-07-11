# Guía de Deployment: GitHub → Nuthost

## 🚀 Estrategia recomendada: GitHub como repositorio central

### Ventajas de usar GitHub:
- ✅ Backup automático del código
- ✅ Control de versiones
- ✅ Facilita actualizaciones posteriores
- ✅ Deployment directo desde GitHub a Nuthost
- ✅ Colaboración y mantenimiento simplificado

## 📋 Pasos detallados

### 1. Preparar el repositorio GitHub

1. **Crear repositorio nuevo en GitHub**:
   ```
   Nombre: conciliacion-bancaria-rocha
   Descripción: Sistema web de conciliación bancaria automatizada
   Privado: Sí (recomendado para uso empresarial)
   ```

2. **Clonar e inicializar**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Sistema de conciliación bancaria completo"
   git branch -M main
   git remote add origin https://github.com/TUUSUARIO/conciliacion-bancaria-rocha.git
   git push -u origin main
   ```

### 2. Archivos incluidos en el repositorio

```
📁 Estructura del proyecto:
├── 📄 app.py                    # Aplicación principal Streamlit
├── 📁 utils/
│   ├── 📄 data_processor.py     # Procesamiento de datos
│   ├── 📄 reconciliation.py     # Motor de conciliación
│   └── 📄 chart_generator.py    # Generación de gráficos
├── 📁 pages/
│   └── 📄 1_📊_Tablero.py      # Dashboard
├── 📄 flask_app.py             # Wrapper Flask (para Nuthost)
├── 📄 wsgi.py                  # Configuración WSGI
├── 📄 requirements-nuthost.txt  # Dependencias para hosting
├── 📄 requirements-github.txt   # Dependencias completas
├── 📄 README.md                # Documentación
├── 📄 DEPLOYMENT_NUTHOST.md    # Instrucciones específicas Nuthost
└── 📄 .gitignore               # Archivos a ignorar
```

### 3. Deployment desde GitHub a Nuthost

#### Opción A: Descarga directa desde GitHub
1. **En GitHub**: Ir a tu repositorio → Code → Download ZIP
2. **Descomprimir** el archivo
3. **Subir vía FTP/FileManager** a Nuthost (public_html/)

#### Opción B: Git clone en Nuthost (si soporta SSH)
```bash
# En el terminal de Nuthost (si está disponible)
cd public_html
git clone https://github.com/TUUSUARIO/conciliacion-bancaria-rocha.git .
```

### 4. Configuración en Nuthost

1. **Panel de control Nuthost**:
   - Ir a "Python App" o "Aplicaciones Python"
   - Archivo de inicio: `wsgi.py`
   - Función: `app`
   - Python version: 3.8+

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements-nuthost.txt
   ```

3. **Configurar variables de entorno** (si es necesario):
   - `PORT=5000`

4. **Reiniciar aplicación**

### 5. Mantenimiento futuro

#### Para actualizaciones:
1. **Hacer cambios en Replit/local**
2. **Commit y push a GitHub**:
   ```bash
   git add .
   git commit -m "Mejoras en sistema de conciliación"
   git push
   ```
3. **Descargar nueva versión en Nuthost**
4. **Reiniciar aplicación**

## 🎯 URL final
Tu sistema estará disponible en:
`https://tudominio.nuthost.com`

## 🔧 Troubleshooting

### Problemas comunes:
- **Error 500**: Verificar logs en panel Nuthost
- **Dependencias faltantes**: Verificar requirements-nuthost.txt
- **Permisos**: Asegurar que todos los archivos se subieron
- **Puerto**: Verificar configuración WSGI

### Logs útiles:
- Panel Nuthost → Logs → Error logs
- Panel Nuthost → Logs → Access logs

## 📞 Soporte
- GitHub Issues para bugs
- Documentación en README.md
- Instrucciones específicas en DEPLOYMENT_NUTHOST.md