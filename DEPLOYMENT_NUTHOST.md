
# INSTRUCCIONES PARA DEPLOYMENT EN NUTHOST

## Archivos necesarios para subir:
1. app.py (aplicación principal Streamlit)
2. flask_app.py (wrapper Flask)
3. wsgi.py (archivo WSGI)
4. requirements-nuthost.txt (dependencias)
5. utils/ (carpeta completa con módulos)
6. pages/ (carpeta completa si existe)
7. .streamlit/ (configuración de Streamlit)

## Pasos en Nuthost:

1. **Subir archivos:**
   - Conectar por FTP/FileManager
   - Subir todos los archivos al directorio public_html/

2. **Instalar dependencias:**
   - En el panel de control de Nuthost
   - Ir a "Python App" o "Python Setup"
   - Subir requirements-nuthost.txt
   - Ejecutar: pip install -r requirements-nuthost.txt

3. **Configurar aplicación Python:**
   - Archivo de inicio: wsgi.py
   - Función de aplicación: app
   - Python version: 3.8+ 

4. **Variables de entorno (si es necesario):**
   - Agregar en el panel de control
   - PORT=5000

5. **Reiniciar aplicación:**
   - Desde el panel de control
   - "Restart Python App"

## URL de acceso:
https://tudominio.nuthost.com

## Troubleshooting:
- Si no carga: verificar logs en panel de control
- Si error de dependencias: verificar requirements-nuthost.txt
- Si error de permisos: verificar que todos los archivos se subieron

## Nota importante:
Esta configuración funciona para hostings compartidos que soportan Python/Flask.
Streamlit se ejecuta como servicio interno y Flask actúa como proxy.
