import os
from typing import Dict, Any

class Config:
    """Configuración del sistema de chatbot"""
    
    # Configuración de la base de datos
    DATABASE_PATH = "chatbot_db.sqlite"
    
    # Configuración del servidor
    HOST = "0.0.0.0"
    PORT = 5001
    DEBUG = True
    
    # Configuración de archivos
    UPLOAD_FOLDER = "documentos"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif'}
    
    # Configuración del chatbot
    MAX_MESSAGE_LENGTH = 1000
    SESSION_TIMEOUT_HOURS = 24
    
    # Configuración de costos (en soles)
    COSTOS_MATRICULA = {
        "matricula": 300,
        "pension_mensual": 150,
    }
    
    # Configuración de grados disponibles
    GRADOS_DISPONIBLES = [
        "1er grado",
        "2do grado", 
        "3er grado",
        "4to grado"
    ]
    
    # Configuración de requisitos por grado
    REQUISITOS_GRADO = {
        "1er grado": "DNI del menor, Código de SIAGE, Libreta de notas del año anterior, Recibo de agua/luz",
        "2do grado": "DNI del menor, Código de SIAGE, Libreta de notas del año anterior, Recibo de agua/luz",
        "3er grado": "DNI del menor, Código de SIAGE, Libreta de notas del año anterior, Recibo de agua/luz",
        "4to grado": "DNI del menor, Código de SIAGE, Libreta de notas del año anterior, Recibo de agua/luz"
    }
    
    # Configuración de mensajes del chatbot
    MENSAJES = {
        "saludo": "¡Hola! 👋 Soy el Asistente Virtual del I.E.P. Barton. Me alegra saludarte. ¿En qué puedo ayudarte hoy?",
        "error_conexion": "Error de conexión con el servidor. Por favor, intenta nuevamente.",
        "archivo_subido": "¡Excelente! 📄 He recibido el documento. Lo estoy revisando para confirmar que esté correcto.",
        "asesor_contacto": "Un asesor especializado se pondrá en contacto contigo en los próximos 30 minutos.",
        "matricula_iniciada": "¡Perfecto! 🎓 Te ayudo con el proceso de matrícula. El I.E.P. Barton ofrece una educación de calidad para primaria.",
        "sin_codigo_SIAGE": "Entiendo que no tienes el código SIAGE. No te preocupes, esto es muy común. Te recomiendo que te acerques a nuestra secretaría para que puedan ayudarte a obtenerlo.",
        "redireccion_presencial": "Para agilizar tu proceso de matrícula, te sugiero que visites nuestra institución. Nuestra secretaría te ayudará a:",
        "agradecimiento_paciencia": "¡Muchas gracias por tu paciencia! 🙏 Esperamos verte pronto en el I.E.P. Barton. Si tienes alguna otra consulta, no dudes en preguntarme."
    }
    
    # Configuración de CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
        "exp://localhost:19000",
        "exp://192.168.1.100:19000"
    ]
    
    @classmethod
    def get_database_path(cls) -> str:
        """Obtiene la ruta de la base de datos"""
        return cls.DATABASE_PATH
    
    @classmethod
    def get_upload_folder(cls) -> str:
        """Obtiene la carpeta de uploads"""
        return cls.UPLOAD_FOLDER
    
    @classmethod
    def get_costos(cls) -> Dict[str, int]:
        """Obtiene los costos de matrícula"""
        return cls.COSTOS_MATRICULA
    
    @classmethod
    def get_grados(cls) -> list:
        """Obtiene los grados disponibles"""
        return cls.GRADOS_DISPONIBLES
    
    @classmethod
    def get_requisitos(cls, grado: str) -> str:
        """Obtiene los requisitos para un grado específico"""
        return cls.REQUISITOS_GRADO.get(grado, "Requisitos no disponibles")
    
    @classmethod
    def get_mensaje(cls, clave: str) -> str:
        """Obtiene un mensaje específico"""
        return cls.MENSAJES.get(clave, "Mensaje no disponible")
    
    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida"""
        import os
        
        # Si el archivo no tiene extensión, asumir que es una imagen (común en fotos móviles)
        if '.' not in filename:
            return True  # Permitir archivos sin extensión (fotos móviles)
        
        # Verificar extensión
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in {ext[1:] for ext in cls.ALLOWED_EXTENSIONS}
    
    @classmethod
    def get_file_extension(cls, filename: str) -> str:
        """Obtiene la extensión del archivo o asigna una por defecto"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        else:
            # Para archivos sin extensión (fotos móviles), asumir JPEG
            return 'jpg'
    
    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        """Obtiene la configuración del servidor"""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG
        } 