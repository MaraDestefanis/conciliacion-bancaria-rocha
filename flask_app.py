
from flask import Flask, render_template_string
import subprocess
import threading
import time
import requests

app = Flask(__name__)

# Variable global para el proceso de Streamlit
streamlit_process = None

def start_streamlit():
    """Inicia el servidor Streamlit en background"""
    global streamlit_process
    try:
        streamlit_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8502",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ])
        time.sleep(5)  # Esperar a que Streamlit inicie
    except Exception as e:
        print(f"Error iniciando Streamlit: {e}")

@app.route('/')
def index():
    """Página principal que redirige a Streamlit"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema de Conciliación Bancaria</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
            .container { text-align: center; padding: 50px; }
            .loading { font-size: 18px; color: #666; }
            iframe { width: 100%; height: 100vh; border: none; }
        </style>
    </head>
    <body>
        <div id="loading" class="container">
            <h1>Sistema de Conciliación Bancaria</h1>
            <p class="loading">Cargando aplicación...</p>
        </div>
        <iframe id="streamlit-frame" src="/streamlit" style="display: none;"></iframe>
        <script>
            setTimeout(() => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('streamlit-frame').style.display = 'block';
            }, 3000);
        </script>
    </body>
    </html>
    """)

@app.route('/streamlit')
def streamlit_proxy():
    """Proxy para el servidor Streamlit"""
    return render_template_string("""
    <script>
        window.location.href = 'http://localhost:8502';
    </script>
    """)

if __name__ == '__main__':
    # Iniciar Streamlit en background
    threading.Thread(target=start_streamlit, daemon=True).start()
    
    # Iniciar Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
