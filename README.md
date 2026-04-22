# Tablero de Canasta Básica Mexicana

Aplicación web en Flask para estimar y comparar el costo de la canasta básica mexicana por producto, tienda y contexto socioeconómico.

## Ejecución local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000`.

La base SQLite se crea automáticamente en `instance/canasta_basica.db` y se llena con datos iniciales si está vacía.

## Despliegue en PythonAnywhere

1. Sube el proyecto a PythonAnywhere.
2. Crea un entorno virtual e instala dependencias:

```bash
pip install -r requirements.txt
```

3. En la pestaña **Web**, configura Flask con el archivo WSGI.
4. En el archivo WSGI usa:

```python
import sys
path = "/home/tu_usuario/canasta_basica_mexicana"
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

5. Recarga la aplicación web desde PythonAnywhere.
