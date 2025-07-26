# 🤖 Chatbot Inteligente - I.E.P. Barton

## 📋 Descripción

Sistema de chatbot inteligente desarrollado para el **I.E.P. Barton** que automatiza el proceso de matrícula y atención al cliente. El chatbot proporciona información sobre requisitos, costos, verificación de matrículas y gestión de documentos de manera interactiva y eficiente.

## ✨ Características Principales

- **🤖 Chatbot Inteligente**: Sistema conversacional avanzado con manejo de contexto
- **📚 Gestión de Matrículas**: Proceso completo de matrícula automatizado
- **📄 Gestión de Documentos**: Subida y verificación de documentos requeridos
- **💰 Información de Costos**: Consulta automática de precios y pagos
- **🔍 Verificación de Alumnos**: Búsqueda por código SIAGE
- **📊 Base de Datos SQLite**: Almacenamiento persistente de sesiones y datos
- **🌐 API REST**: Interfaz programática completa
- **📱 Frontend Demo**: Interfaz web interactiva para pruebas

## 🏗️ Arquitectura del Sistema

```
backend-chatbot/
├── api_inteligente.py          # API principal con endpoints REST
├── chatbot_inteligente.py      # Lógica del chatbot inteligente
├── chatbot_matricula.py        # Sistema de matrícula
├── config.py                   # Configuración centralizada
├── api.py                      # API secundaria
├── requirements.txt            # Dependencias Python
├── chatbot_db.sqlite          # Base de datos SQLite
├── frontend_demo.html         # Interfaz web demo
├── documentos/                # Carpeta para archivos subidos
└── venv/                     # Entorno virtual Python
```

## 🚀 Tecnologías Utilizadas

### Backend

- **Python 3.x**: Lenguaje principal
- **Flask**: Framework web para la API
- **Flask-CORS**: Manejo de CORS para integración frontend
- **SQLite**: Base de datos ligera y eficiente
- **Pandas**: Procesamiento de datos CSV
- **OpenPyXL**: Manejo de archivos Excel

### Frontend

- **HTML5/CSS3**: Interfaz web responsive
- **JavaScript**: Lógica del cliente
- **Fetch API**: Comunicación con el backend

## 📦 Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**

   ```bash
   git clone <url-del-repositorio>
   cd backend-chatbot
   ```

2. **Crear entorno virtual**

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   # o
   venv\Scripts\activate     # En Windows
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la base de datos**
   ```bash
   python -c "from chatbot_inteligente import ChatbotInteligente; ChatbotInteligente()"
   ```

## 🎯 Uso

### Iniciar el Servidor

```bash
python api_inteligente.py
```

El servidor se ejecutará en `http://localhost:5001`

### Endpoints Principales

#### 🤖 Chatbot Inteligente

- **POST** `/chatbot-inteligente`
  - Procesa mensajes del usuario
  - Maneja archivos subidos
  - Mantiene contexto de conversación

#### 📋 Verificación de Matrícula

- **POST** `/verificar-matricula`
  - Busca alumnos por código SIAGE
  - Calcula pagos pendientes
  - Proporciona estado de matrícula

#### 📄 Gestión de Documentos

- **GET** `/documentos/<session_id>`
  - Obtiene documentos de una sesión

#### 📊 Información del Sistema

- **GET** `/requisitos/<grado>`
  - Obtiene requisitos por grado
- **GET** `/costos`
  - Consulta costos de matrícula
- **GET** `/grados`
  - Lista grados disponibles
- **GET** `/estadisticas`
  - Estadísticas del sistema

#### 🔧 Gestión de Sesiones

- **POST** `/nueva-sesion`
  - Crea nueva sesión de chat
- **GET** `/sesion/<session_id>`
  - Obtiene estado de sesión
- **GET** `/historial/<session_id>`
  - Historial de conversación
- **DELETE** `/limpiar-sesion/<session_id>`
  - Limpia sesión

### Ejemplo de Uso - API

```python
import requests
import json

# URL base del servidor
BASE_URL = "http://localhost:5001"

# Crear nueva sesión
response = requests.post(f"{BASE_URL}/nueva-sesion")
session_data = response.json()
session_id = session_data['session_id']

# Enviar mensaje al chatbot
mensaje_data = {
    "mensaje": "Hola, quiero información sobre matrícula",
    "session_id": session_id
}

response = requests.post(
    f"{BASE_URL}/chatbot-inteligente",
    json=mensaje_data
)

respuesta = response.json()
print(respuesta['mensaje'])
```

### Interfaz Web Demo

Abre `frontend_demo.html` en tu navegador para probar el chatbot de manera interactiva.

## ⚙️ Configuración

### Archivo `config.py`

El archivo de configuración centralizada incluye:

- **Configuración del servidor**: Host, puerto, modo debug
- **Base de datos**: Ruta y configuración
- **Archivos**: Tipos permitidos, tamaño máximo
- **Costos**: Precios de matrícula y pensión
- **Grados**: Niveles educativos disponibles
- **Requisitos**: Documentos necesarios por grado
- **Mensajes**: Textos predefinidos del chatbot
- **CORS**: Orígenes permitidos

### Personalización

Para personalizar el sistema:

1. **Modificar costos**: Editar `COSTOS_MATRICULA` en `config.py`
2. **Agregar grados**: Actualizar `GRADOS_DISPONIBLES`
3. **Cambiar requisitos**: Modificar `REQUISITOS_GRADO`
4. **Personalizar mensajes**: Editar `MENSAJES`

## 📊 Estructura de la Base de Datos

### Tablas Principales

#### `sesiones`

- Almacena información de sesiones de chat
- Campos: id, estado, datos_contexto, fecha_creacion, etc.

#### `documentos`

- Gestiona archivos subidos por usuarios
- Campos: id, sesion_id, tipo_documento, nombre_archivo, etc.

#### `historial_conversacion`

- Registra mensajes y respuestas
- Campos: id, sesion_id, mensaje_usuario, respuesta_bot, timestamp

#### `requisitos_grado`

- Almacena requisitos por nivel educativo
- Campos: grado, requisitos, descripcion

## 🔄 Flujo de Trabajo

### Proceso de Matrícula

1. **Saludo inicial** → El chatbot saluda y se presenta
2. **Información de matrícula** → Proporciona detalles del proceso
3. **Selección de grado** → Usuario elige nivel educativo
4. **Requisitos** → Muestra documentos necesarios
5. **Subida de documentos** → Usuario envía archivos
6. **Verificación** → Sistema valida documentos
7. **Contacto asesor** → Conecta con personal especializado

### Estados de Sesión

- `inicio`: Sesión recién creada
- `matricula`: Proceso de matrícula iniciado
- `seleccion_grado`: Usuario eligiendo grado
- `requisitos`: Mostrando requisitos
- `subida_documentos`: Esperando documentos
- `verificacion`: Validando información
- `contacto_asesor`: Conectando con asesor

## 🛠️ Desarrollo

### Estructura del Código

#### `chatbot_inteligente.py`

- Clase principal `ChatbotInteligente`
- Manejo de sesiones y contexto
- Procesamiento de mensajes
- Gestión de archivos

#### `api_inteligente.py`

- Endpoints REST
- Manejo de errores
- Validación de datos
- Integración con chatbot

#### `chatbot_matricula.py`

- Sistema de matrícula
- Carga de datos CSV
- Búsqueda de alumnos
- Cálculo de pagos

### Agregar Nuevas Funcionalidades

1. **Nuevo endpoint**: Agregar en `api_inteligente.py`
2. **Nueva lógica**: Implementar en `chatbot_inteligente.py`
3. **Configuración**: Actualizar `config.py` si es necesario
4. **Base de datos**: Crear tablas si se requieren

## 🧪 Testing

### Pruebas Manuales

1. **Iniciar servidor**: `python api_inteligente.py`
2. **Abrir frontend**: `frontend_demo.html`
3. **Probar flujo completo**: Desde saludo hasta contacto asesor

### Endpoints de Prueba

- **Health Check**: `GET /health`
- **Estadísticas**: `GET /estadisticas`

## 📝 Logs

El sistema genera logs en `server.log` con información detallada de:

- Mensajes recibidos
- Errores y excepciones
- Operaciones de base de datos
- Estado de sesiones

## 🔒 Seguridad

- **Validación de entrada**: Todos los datos se validan
- **Límites de archivo**: Tamaño máximo configurable
- **Tipos de archivo**: Solo extensiones permitidas
- **CORS configurado**: Orígenes específicos permitidos

## 🚀 Despliegue

### Producción

1. **Configurar servidor web** (nginx, Apache)
2. **Usar WSGI** (gunicorn, uwsgi)
3. **Configurar SSL/TLS**
4. **Backup de base de datos**
5. **Monitoreo de logs**

### Variables de Entorno

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export DATABASE_PATH=/path/to/chatbot_db.sqlite
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Contacto

**I.E.P. Barton**

- Email: [email@barton.edu.pe]
- Teléfono: [número de contacto]
- Dirección: [dirección de la institución]

## 🙏 Agradecimientos

- Equipo de desarrollo del I.E.P. Barton
- Comunidad de Flask y Python
- Contribuidores del proyecto

---

**Desarrollado con ❤️ para el I.E.P. Barton**
