import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import re
from config import Config

class ChatbotInteligente:
    def __init__(self):
        self.db_path = Config.get_database_path()
        self.init_database()
        
    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla para sesiones de chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesiones (
                id TEXT PRIMARY KEY,
                estado TEXT,
                datos_contexto TEXT,
                fecha_creacion TIMESTAMP,
                fecha_actualizacion TIMESTAMP,
                nombre_usuario TEXT,
                telefono_usuario TEXT
            )
        ''')
        
        # Verificar si las columnas nombre_usuario y telefono_usuario existen
        cursor.execute("PRAGMA table_info(sesiones)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        # Agregar columnas si no existen
        if 'nombre_usuario' not in columnas:
            cursor.execute('ALTER TABLE sesiones ADD COLUMN nombre_usuario TEXT')
            print("✅ Columna nombre_usuario agregada a la tabla sesiones")
        
        if 'telefono_usuario' not in columnas:
            cursor.execute('ALTER TABLE sesiones ADD COLUMN telefono_usuario TEXT')
            print("✅ Columna telefono_usuario agregada a la tabla sesiones")
        
        # Tabla para documentos subidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id TEXT PRIMARY KEY,
                sesion_id TEXT,
                tipo_documento TEXT,
                nombre_archivo TEXT,
                ruta_archivo TEXT,
                estado TEXT,
                fecha_subida TIMESTAMP,
                FOREIGN KEY (sesion_id) REFERENCES sesiones (id)
            )
        ''')
        
        # Tabla para requisitos por grado
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requisitos_grado (
                grado TEXT PRIMARY KEY,
                requisitos TEXT,
                descripcion TEXT
            )
        ''')
        
        # Tabla para historial de conversación
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_conversacion (
                id TEXT PRIMARY KEY,
                sesion_id TEXT,
                mensaje_usuario TEXT,
                respuesta_bot TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (sesion_id) REFERENCES sesiones (id)
            )
        ''')
        
        # Insertar requisitos por grado si no existen
        for grado in Config.get_grados():
            requisitos = Config.get_requisitos(grado)
            descripcion = f"{grado} de primaria"
            
            cursor.execute('''
                INSERT OR IGNORE INTO requisitos_grado (grado, requisitos, descripcion)
                VALUES (?, ?, ?)
            ''', (grado, requisitos, descripcion))
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
    
    def crear_sesion(self, user_id: str = None) -> str:
        """Crea una nueva sesión de chat"""
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sesiones (id, estado, datos_contexto, fecha_creacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, "inicio", json.dumps({}), datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        return session_id
    
    def obtener_estado_sesion(self, session_id: str) -> Dict[str, Any]:
        """Obtiene el estado actual de una sesión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT estado, datos_contexto, nombre_usuario, telefono_usuario FROM sesiones WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "estado": result[0],
                "datos_contexto": json.loads(result[1]) if result[1] else {},
                "nombre_usuario": result[2],
                "telefono_usuario": result[3]
            }
        return {"estado": "inicio", "datos_contexto": {}, "nombre_usuario": None, "telefono_usuario": None}
    
    def actualizar_estado_sesion(self, session_id: str, estado: str, datos_contexto: Dict[str, Any]):
        """Actualiza el estado de una sesión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sesiones 
            SET estado = ?, datos_contexto = ?, fecha_actualizacion = ?
            WHERE id = ?
        ''', (estado, json.dumps(datos_contexto), datetime.now(), session_id))
        
        conn.commit()
        conn.close()
    
    def guardar_mensaje_historial(self, session_id: str, mensaje_usuario: str, respuesta_bot: str):
        """Guarda un mensaje en el historial de conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historial_conversacion (id, sesion_id, mensaje_usuario, respuesta_bot, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), session_id, mensaje_usuario, respuesta_bot, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def guardar_documento(self, session_id: str, tipo_documento: str, nombre_archivo: str, contenido_archivo: bytes) -> str:
        """Guarda un documento subido por el usuario"""
        doc_id = str(uuid.uuid4())
        upload_folder = Config.get_upload_folder()
        
        # Manejar archivos sin extensión (común en fotos móviles)
        if '.' not in nombre_archivo:
            extension = Config.get_file_extension(nombre_archivo)
            nombre_archivo = f"{nombre_archivo}.{extension}"
        
        ruta_archivo = f"{upload_folder}/{doc_id}_{nombre_archivo}"
        
        # Crear directorio si no existe
        os.makedirs(upload_folder, exist_ok=True)
        
        # Verificar extensión permitida
        if not Config.is_allowed_file(nombre_archivo):
            raise ValueError(f"Tipo de archivo no permitido: {nombre_archivo}")
        
        # Verificar tamaño del archivo
        if len(contenido_archivo) > Config.MAX_FILE_SIZE:
            raise ValueError(f"Archivo demasiado grande. Máximo {Config.MAX_FILE_SIZE / (1024*1024)}MB")
        
        # Guardar archivo
        with open(ruta_archivo, "wb") as f:
            f.write(contenido_archivo)
        
        # Guardar en base de datos
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documentos (id, sesion_id, tipo_documento, nombre_archivo, ruta_archivo, estado, fecha_subida)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (doc_id, session_id, tipo_documento, nombre_archivo, ruta_archivo, "pendiente", datetime.now()))
        
        conn.commit()
        conn.close()
        
        return doc_id
    
    def obtener_requisitos_grado(self, grado: str) -> Optional[str]:
        """Obtiene los requisitos para un grado específico"""
        return Config.get_requisitos(grado)
    
    def extraer_nombre_telefono(self, mensaje: str) -> Dict[str, str]:
        """Extrae nombre y teléfono del mensaje del usuario de forma más robusta"""
        nombre = None
        telefono = None
        
        # Limpiar el mensaje
        mensaje_limpio = mensaje.strip()
        
        # Patrones más robustos para teléfono (formato peruano)
        # Patrones: +51 999 123 456, 999123456, 999 123 456, 999-123-456
        telefono_patterns = [
            r'(\+51\s?)?(\d{3}[\s\-]?\d{3}[\s\-]?\d{3})',  # +51 999 123 456 o 999123456
            r'(\d{9})',  # 9 dígitos consecutivos
            r'(\d{3}[\s\-]?\d{3}[\s\-]?\d{3})',  # 999 123 456
        ]
        
        # Buscar teléfono
        for pattern in telefono_patterns:
            telefono_match = re.search(pattern, mensaje_limpio)
            if telefono_match:
                telefono = re.sub(r'[\s\-]', '', telefono_match.group(0))
                break
        
        # Patrones para nombre
        # Buscar patrones como "Mi nombre es", "Me llamo", "Soy", etc.
        nombre_patterns = [
            r'mi nombre es\s+([^,\n]+?)(?:\s+y\s+mi\s+teléfono|\s+y\s+mi\s+teléfono|\s+teléfono|\s+mi\s+celular|\s+mi\s+cel)',
            r'me llamo\s+([^,\n]+?)(?:\s+y\s+mi\s+teléfono|\s+y\s+mi\s+teléfono|\s+teléfono|\s+mi\s+celular|\s+mi\s+cel)',
            r'soy\s+([^,\n]+?)(?:\s+y\s+mi\s+teléfono|\s+y\s+mi\s+teléfono|\s+teléfono|\s+mi\s+celular|\s+mi\s+cel)',
            r'nombre\s+([^,\n]+?)(?:\s+y\s+mi\s+teléfono|\s+y\s+mi\s+teléfono|\s+teléfono|\s+mi\s+celular|\s+mi\s+cel)',
        ]
        
        # Buscar nombre con patrones
        for pattern in nombre_patterns:
            nombre_match = re.search(pattern, mensaje_limpio, re.IGNORECASE)
            if nombre_match:
                nombre = nombre_match.group(1).strip()
                break
        
        # Si no se encontró con patrones, intentar extraer nombre de forma más simple
        if not nombre and telefono:
            # Remover el teléfono del mensaje
            mensaje_sin_telefono = re.sub(r'(\+51\s?)?(\d{3}[\s\-]?\d{3}[\s\-]?\d{3})', '', mensaje_limpio)
            mensaje_sin_telefono = re.sub(r'(\d{9})', '', mensaje_sin_telefono)
            
            # Limpiar palabras comunes
            palabras_comunes = ['mi', 'nombre', 'es', 'y', 'teléfono', 'celular', 'cel', 'número', 'numero']
            palabras = mensaje_sin_telefono.split()
            palabras_filtradas = [palabra for palabra in palabras if palabra.lower() not in palabras_comunes]
            
            if palabras_filtradas:
                nombre = ' '.join(palabras_filtradas).strip()
        
        # Si aún no hay nombre, pero hay palabras que parecen nombres
        if not nombre:
            # Buscar palabras que empiecen con mayúscula (posibles nombres)
            palabras = mensaje_limpio.split()
            nombres_candidatos = []
            for palabra in palabras:
                if palabra[0].isupper() and len(palabra) > 2 and not palabra.isdigit():
                    nombres_candidatos.append(palabra)
            
            if nombres_candidatos:
                nombre = ' '.join(nombres_candidatos)
        
        # Si no hay nombre pero el mensaje parece ser solo un nombre (sin teléfono)
        if not nombre and not telefono:
            # Verificar si el mensaje parece ser un nombre completo
            palabras = mensaje_limpio.split()
            if len(palabras) >= 2:  # Al menos nombre y apellido
                # Verificar que todas las palabras empiecen con mayúscula
                if all(palabra[0].isupper() for palabra in palabras):
                    nombre = mensaje_limpio
            elif len(palabras) == 1 and palabras[0][0].isupper() and len(palabras[0]) > 2:
                # Un solo nombre que empieza con mayúscula
                nombre = mensaje_limpio
        
        # Validar que el nombre no sea muy corto o muy largo
        if nombre and (len(nombre) < 2 or len(nombre) > 50):
            nombre = None
        
        # Validar que el teléfono tenga el formato correcto
        if telefono and (len(telefono) < 9 or len(telefono) > 12):
            telefono = None
        
        return {"nombre": nombre, "telefono": telefono}
    
    def procesar_mensaje(self, mensaje: str, session_id: str = None, archivos: List[Dict] = None) -> Dict[str, Any]:
        """Procesa un mensaje del usuario y retorna la respuesta del chatbot con mejor contexto"""
        
        # Crear sesión si no existe
        if not session_id:
            session_id = self.crear_sesion()
        
        estado_actual = self.obtener_estado_sesion(session_id)
        estado = estado_actual["estado"]
        contexto = estado_actual["datos_contexto"]
        
        # Procesar archivos si se enviaron
        if archivos:
            respuesta = self.procesar_archivos(archivos, session_id, contexto)
            self.guardar_mensaje_historial(session_id, f"[Archivos subidos: {len(archivos)}]", respuesta["mensaje"])
            return respuesta
        
        # Detectar saludos y mensajes iniciales (solo si estamos en estado inicial)
        if self.es_saludo(mensaje) and estado == "inicio":
            respuesta = self.procesar_saludo(session_id)
            self.guardar_mensaje_historial(session_id, mensaje, respuesta["mensaje"])
            return respuesta
        
        # Detectar si es un mensaje sobre matrícula (solo si estamos en estado inicial)
        if self.es_mensaje_matricula(mensaje) and estado == "inicio":
            respuesta = self.iniciar_flujo_matricula(session_id)
            self.guardar_mensaje_historial(session_id, mensaje, respuesta["mensaje"])
            return respuesta
        
        # Manejar saludos en cualquier estado (para mantener contexto)
        if self.es_saludo(mensaje) and estado != "inicio":
            # Si el usuario saluda en medio de una conversación, responder amigablemente
            # pero mantener el contexto actual
            if estado == "opciones_matricula":
                return {
                    "mensaje": "¡Hola! 👋 ¿Te gustaría continuar con el proceso de matrícula?",
                    "opciones": [
                        {"texto": "📋 Ver Requisitos", "valor": "requisitos"},
                        {"texto": "📤 Subir Documentos", "valor": "subir_documentos"},
                        {"texto": "🔍 Verificar Estado de Matrícula", "valor": "verificar"},
                        {"texto": "👨‍💼 Hablar con Asesor", "valor": "asesor"}
                    ],
                    "tipo": "opciones",
                    "session_id": session_id
                }
            elif estado == "conectando_asesor":
                # Verificar si ya tenemos información completa
                estado_actual = self.obtener_estado_sesion(session_id)
                nombre_actual = estado_actual.get("nombre_usuario")
                telefono_actual = estado_actual.get("telefono_usuario")
                
                if nombre_actual and telefono_actual:
                    # Ya tenemos toda la información, confirmar
                    return {
                        "mensaje": f"¡Hola! 👋 Ya tengo tu información registrada:\n\n👤 Nombre: {nombre_actual}\n📞 Teléfono: {telefono_actual}\n\nUn asesor especializado se pondrá en contacto contigo en los próximos 30 minutos. ¿Hay algo más en lo que pueda ayudarte?",
                        "tipo": "texto",
                        "session_id": session_id
                    }
                else:
                    # Falta información, pedir lo que falta
                    if nombre_actual and not telefono_actual:
                        return {
                            "mensaje": "¡Hola! 👋 Ya tengo tu nombre. ¿Podrías proporcionarme tu número de teléfono para completar la conexión con el asesor?",
                            "tipo": "texto",
                            "session_id": session_id
                        }
                    elif telefono_actual and not nombre_actual:
                        return {
                            "mensaje": f"¡Hola! 👋 Ya tengo tu teléfono: {telefono_actual}. ¿Podrías proporcionarme tu nombre completo para completar la conexión con el asesor?",
                            "tipo": "texto",
                            "session_id": session_id
                        }
                    else:
                        return {
                            "mensaje": "¡Hola! 👋 ¿Podrías proporcionarme tu nombre y teléfono para conectar con el asesor?",
                            "tipo": "texto",
                            "session_id": session_id
                        }
            elif estado == "verificando_matricula":
                return {
                    "mensaje": "¡Hola! 👋 ¿Podrías proporcionarme el código SIAGE para verificar el estado de la matrícula?",
                    "tipo": "texto",
                    "session_id": session_id
                }
            elif estado == "requisitos_grado":
                return {
                    "mensaje": "¡Hola! 👋 ¿Para qué grado necesitas información sobre los requisitos?",
                    "opciones": [
                        {"texto": "1er grado", "valor": "1er_grado"},
                        {"texto": "2do grado", "valor": "2do_grado"},
                        {"texto": "3er grado", "valor": "3er_grado"},
                        {"texto": "4to grado", "valor": "4to_grado"}
                    ],
                    "tipo": "opciones",
                    "session_id": session_id
                }
            elif estado == "subiendo_documentos":
                return {
                    "mensaje": "¡Hola! 👋 ¿Te gustaría continuar subiendo los documentos para tu matrícula?",
                    "tipo": "subida_archivos",
                    "session_id": session_id
                }
            else:
                # Para otros estados, volver al inicio
                self.actualizar_estado_sesion(session_id, "inicio", {})
                respuesta = self.procesar_saludo(session_id)
                self.guardar_mensaje_historial(session_id, mensaje, respuesta["mensaje"])
                return respuesta
        
        # Procesar según el estado actual
        if estado == "inicio":
            respuesta = self.procesar_estado_inicio(mensaje, session_id)
        elif estado == "opciones_matricula":
            respuesta = self.procesar_opciones_matricula(mensaje, session_id, contexto)
        elif estado == "requisitos_grado":
            respuesta = self.procesar_requisitos_grado(mensaje, session_id, contexto)
        elif estado == "subiendo_documentos":
            respuesta = self.procesar_subida_documentos(mensaje, session_id, contexto)
        elif estado == "verificando_matricula":
            respuesta = self.procesar_verificacion_matricula(mensaje, session_id, contexto)
        elif estado == "conectando_asesor":
            respuesta = self.procesar_conexion_asesor(mensaje, session_id, contexto)
        elif estado == "recolectando_datos":
            respuesta = self.procesar_recoleccion_datos(mensaje, session_id, contexto)
        elif estado == "redireccion_presencial":
            respuesta = self.procesar_redireccion_presencial(mensaje, session_id, contexto)
        elif estado == "post_matricula":
            respuesta = self.procesar_opciones_post_matricula(mensaje, session_id, contexto)
        else:
            respuesta = self.respuesta_generica(mensaje, session_id)
        
        # Guardar en historial
        self.guardar_mensaje_historial(session_id, mensaje, respuesta["mensaje"])
        return respuesta
    
    def es_saludo(self, mensaje: str) -> bool:
        """Detecta si el mensaje es un saludo"""
        saludos = [
            "hola", "buenos días", "buenas tardes", "buenas noches", "buen día",
            "hello", "hi", "hey", "saludos", "qué tal", "como estás", "como estas"
        ]
        mensaje_lower = mensaje.lower()
        return any(saludo in mensaje_lower for saludo in saludos)
    
    def es_mensaje_matricula(self, mensaje: str) -> bool:
        """Detecta si el mensaje es sobre matrícula"""
        palabras_clave = [
            "matrícula", "matricula", "inscribir", "inscripción", "inscripcion",
            "pago", "pagar", "estudiante", "hijo", "hija", "alumno", "alumna",
            "registrar", "admisión", "admission", "costo", "precio", "cuota"
        ]
        mensaje_lower = mensaje.lower()
        return any(palabra in mensaje_lower for palabra in palabras_clave)
    
    def no_tiene_codigo_SIAGE(self, mensaje: str) -> bool:
        """Detecta si el usuario menciona que no tiene el código SIAGE"""
        palabras_clave = [
            "no tengo", "no tiene", "no poseo", "no cuento", "no dispongo",
            "no sé", "no se", "no conozco", "no conozco", "no recuerdo",
            "perdí", "perdi", "extravié", "extravié", "olvidé", "olvide",
            "no encuentro", "no encuentro", "no aparece", "no aparece",
            "no lo tengo", "no la tengo", "no lo tiene", "no la tiene",
            "no sé dónde", "no se donde", "no sé donde", "no se donde",
            "no tengo idea", "no tengo idea", "no sé qué", "no se que",
            "no tengo el código", "no tengo el codigo", "no tiene el código", "no tiene el codigo",
            "no tengo código", "no tengo codigo", "no tiene código", "no tiene codigo",
            "no tengo SIAGE", "no tiene SIAGE", "no tengo siage", "no tiene siage",
            "no tengo el SIAGE", "no tengo el siage", "no tiene el SIAGE", "no tiene el siage",
            "no lo encuentro", "no la encuentro", "no los encuentro", "no las encuentro",
            "no puedo encontrar", "no puedo encontrarlo", "no puedo encontrarla",
            "no tengo acceso", "no tengo disponible", "no está disponible",
            "no lo tengo a mano", "no lo tengo aquí", "no lo tengo conmigo",
            "no sé dónde lo dejé", "no se donde lo deje", "no recuerdo dónde",
            "no recuerdo donde", "se me perdió", "se me perdio",
            "no tengo el documento", "no tengo el doc", "no tengo la libreta",
            "no tengo el recibo", "no tengo el comprobante"
        ]
        mensaje_lower = mensaje.lower()
        
        # Verificar si contiene alguna de las palabras clave
        for palabra in palabras_clave:
            if palabra in mensaje_lower:
                return True
        
        # Verificar frases específicas que podrían indicar falta del código
        frases_especificas = [
            "no tengo el código SIAGE", "no tengo el codigo SIAGE",
            "no tengo código SIAGE", "no tengo codigo SIAGE",
            "no tengo el SIAGE", "no tengo SIAGE",
            "no lo tengo", "no la tengo", "no los tengo", "no las tengo",
            "no encuentro el código", "no encuentro el codigo",
            "no encuentro el SIAGE", "no encuentro SIAGE",
            "no lo encuentro", "no la encuentro", "no los encuentro", "no las encuentro",
            "no sé dónde está", "no se donde esta", "no sé donde está", "no se donde esta",
            "no tengo idea dónde", "no tengo idea donde",
            "lo perdí", "lo perdi", "la perdí", "la perdi",
            "se me perdió", "se me perdio", "se me extravió", "se me extravio"
        ]
        
        for frase in frases_especificas:
            if frase in mensaje_lower:
                return True
        
        return False
    
    def procesar_saludo(self, session_id: str) -> Dict[str, Any]:
        """Procesa un saludo inicial"""
        return {
            "mensaje": Config.get_mensaje("saludo"),
            "opciones": [
                {"texto": "📚 Información de Matrícula", "valor": "matricula"},
                {"texto": "📋 Ver Requisitos", "valor": "requisitos"},
                {"texto": "💰 Consultar Pagos", "valor": "pagos"},
                {"texto": "🔍 Verificar Estado de Matrícula", "valor": "verificar"},
                {"texto": "📞 Hablar con Asesor", "valor": "asesor"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }
    
    def iniciar_flujo_matricula(self, session_id: str) -> Dict[str, Any]:
        """Inicia el flujo de matrícula"""
        self.actualizar_estado_sesion(session_id, "opciones_matricula", {})
        
        return {
            "mensaje": Config.get_mensaje("matricula_iniciada"),
            "opciones": [
                {"texto": "📋 Ver requisitos por grado", "valor": "requisitos"},
                {"texto": "📤 Subir documentos", "valor": "subir_documentos"},
                {"texto": "🔍 Verificar estado de matrícula", "valor": "verificar"},
                {"texto": "💰 Información de costos", "valor": "costos"},
                {"texto": "👨‍💼 Hablar con un asesor", "valor": "asesor"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }
    
    def procesar_estado_inicio(self, mensaje: str, session_id: str) -> Dict[str, Any]:
        """Procesa mensajes en el estado inicial"""
        mensaje_lower = mensaje.lower()
        
        # Detectar selección de opciones del saludo
        if "matricula" in mensaje_lower or "1" in mensaje:
            return self.iniciar_flujo_matricula(session_id)
        elif "requisitos" in mensaje_lower or "2" in mensaje:
            self.actualizar_estado_sesion(session_id, "requisitos_grado", {"opcion_seleccionada": "requisitos"})
            return {
                "mensaje": "¡Excelente! 📋 Te ayudo con los requisitos. ¿Para qué grado necesitas la información?",
                "opciones": [
                    {"texto": "1er grado", "valor": "1er_grado"},
                    {"texto": "2do grado", "valor": "2do_grado"},
                    {"texto": "3er grado", "valor": "3er_grado"},
                    {"texto": "4to grado", "valor": "4to_grado"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        elif "subir" in mensaje_lower or "documentos" in mensaje_lower or "3" in mensaje:
            self.actualizar_estado_sesion(session_id, "subiendo_documentos", {"opcion_seleccionada": "subir_documentos"})
            return {
                "mensaje": "¡Perfecto! 📤 Para subir documentos primero necesito saber el grado. ¿Para qué grado vas a matricular?",
                "opciones": [
                    {"texto": "1er grado", "valor": "1er_grado"},
                    {"texto": "2do grado", "valor": "2do_grado"},
                    {"texto": "3er grado", "valor": "3er_grado"},
                    {"texto": "4to grado", "valor": "4to_grado"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        elif "verificar" in mensaje_lower or "estado" in mensaje_lower or "4" in mensaje:
            self.actualizar_estado_sesion(session_id, "verificando_matricula", {"opcion_seleccionada": "verificar"})
            return {
                "mensaje": "🔍 Para verificar el estado de tu matrícula, necesito el código SIAGE del estudiante. ¿Podrías proporcionármelo?",
                "tipo": "texto",
                "session_id": session_id
            }
        elif "asesor" in mensaje_lower or "hablar" in mensaje_lower or "5" in mensaje:
            self.actualizar_estado_sesion(session_id, "conectando_asesor", {"opcion_seleccionada": "asesor"})
            return {
                "mensaje": "👨‍💼 Te voy a conectar con un asesor especializado. Para agilizar el proceso, ¿podrías proporcionarme tu nombre y número de teléfono?",
                "tipo": "texto",
                "session_id": session_id
            }
        elif self.es_mensaje_matricula(mensaje):
            return self.iniciar_flujo_matricula(session_id)
        
        return {
            "mensaje": "Entiendo tu consulta. ¿Te gustaría información sobre el proceso de matrícula o hay algo específico en lo que pueda ayudarte?",
            "opciones": [
                {"texto": "📚 Información de Matrícula", "valor": "matricula"},
                {"texto": "📋 Ver Requisitos", "valor": "requisitos"},
                {"texto": "📤 Subir Documentos", "valor": "subir_documentos"},
                {"texto": "🔍 Verificar Estado de Matrícula", "valor": "verificar"},
                {"texto": "👨‍💼 Hablar con Asesor", "valor": "asesor"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }
    
    def procesar_opciones_matricula(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la selección de opciones de matrícula"""
        mensaje_lower = mensaje.lower()
        costos = Config.get_costos()
        
        if "requisitos" in mensaje_lower or "1" in mensaje:
            self.actualizar_estado_sesion(session_id, "requisitos_grado", {"opcion_seleccionada": "requisitos"})
            return {
                "mensaje": "¡Excelente! 📋 Te ayudo con los requisitos. ¿Para qué grado necesitas la información?",
                "opciones": [
                    {"texto": "1er grado", "valor": "1er_grado"},
                    {"texto": "2do grado", "valor": "2do_grado"},
                    {"texto": "3er grado", "valor": "3er_grado"},
                    {"texto": "4to grado", "valor": "4to_grado"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        elif "subir" in mensaje_lower or "documentos" in mensaje_lower or "2" in mensaje:
            self.actualizar_estado_sesion(session_id, "subiendo_documentos", {"opcion_seleccionada": "subir_documentos"})
            return {
                "mensaje": "¡Perfecto! 📤 Para subir documentos primero necesito saber el grado. ¿Para qué grado vas a matricular?",
                "opciones": [
                    {"texto": "1er grado", "valor": "1er_grado"},
                    {"texto": "2do grado", "valor": "2do_grado"},
                    {"texto": "3er grado", "valor": "3er_grado"},
                    {"texto": "4to grado", "valor": "4to_grado"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        elif "verificar" in mensaje_lower or "estado" in mensaje_lower or "3" in mensaje:
            self.actualizar_estado_sesion(session_id, "verificando_matricula", {"opcion_seleccionada": "verificar"})
            return {
                "mensaje": "🔍 Para verificar el estado de tu matrícula, necesito el código SIAGE del estudiante. ¿Podrías proporcionármelo?",
                "tipo": "texto",
                "session_id": session_id
            }
        elif "costos" in mensaje_lower or "precio" in mensaje_lower or "4" in mensaje:
            return {
                "mensaje": f"💰 Los costos de matrícula para el 2024 son:\n\n• Matrícula: S/ {costos['matricula']}\n• Pensión mensual: S/ {costos['pension_mensual']}\n\n¿Te gustaría proceder con la matrícula o tienes alguna pregunta sobre los costos?",
                "opciones": [
                    {"texto": "📋 Ver requisitos", "valor": "requisitos"},
                    {"texto": "📤 Subir documentos", "valor": "subir_documentos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        elif "asesor" in mensaje_lower or "hablar" in mensaje_lower or "5" in mensaje:
            self.actualizar_estado_sesion(session_id, "conectando_asesor", {"opcion_seleccionada": "asesor"})
            return {
                "mensaje": "👨‍💼 Te voy a conectar con un asesor especializado. Para agilizar el proceso, ¿podrías proporcionarme tu nombre y número de teléfono?",
                "tipo": "texto",
                "session_id": session_id
            }
        
        return {
            "mensaje": "No entendí tu selección. Por favor, elige una de las opciones disponibles:",
            "opciones": [
                {"texto": "📋 Ver requisitos por grado", "valor": "requisitos"},
                {"texto": "📤 Subir documentos", "valor": "subir_documentos"},
                {"texto": "🔍 Verificar estado de matrícula", "valor": "verificar"},
                {"texto": "💰 Información de costos", "valor": "costos"},
                {"texto": "👨‍💼 Hablar con un asesor", "valor": "asesor"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }
    
    def procesar_requisitos_grado(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la selección de grado para requisitos"""
        grado_seleccionado = None
        
        # Verificar si el usuario ya seleccionó un grado y ahora está respondiendo "Sí" o "No"
        if "grado_seleccionado" in contexto:
            if "sí" in mensaje.lower() or "si" in mensaje.lower() or "yes" in mensaje.lower() or "ok" in mensaje.lower():
                # Usuario quiere subir documentos
                self.actualizar_estado_sesion(session_id, "subiendo_documentos", contexto)
                return {
                    "mensaje": "¡Perfecto! 📤 Ahora puedes enviarme una foto clara de cada documento. Te confirmaré si están correctos y te guiaré en el proceso 😊",
                    "tipo": "subida_archivos",
                    "session_id": session_id
                }
            elif "no" in mensaje.lower() or "gracias" in mensaje.lower():
                # Usuario no quiere subir documentos
                self.actualizar_estado_sesion(session_id, "inicio", {})
                return {
                    "mensaje": "Entendido. Si necesitas ayuda en otro momento, no dudes en preguntarme. ¿Hay algo más en lo que pueda ayudarte?",
                    "tipo": "texto",
                    "session_id": session_id
                }
        
        # Procesar selección de grado
        if "1er" in mensaje or "primero" in mensaje or "1" in mensaje:
            grado_seleccionado = "1er grado"
        elif "2do" in mensaje or "segundo" in mensaje or "2" in mensaje:
            grado_seleccionado = "2do grado"
        elif "3er" in mensaje or "tercero" in mensaje or "3" in mensaje:
            grado_seleccionado = "3er grado"
        elif "4to" in mensaje or "cuarto" in mensaje or "4" in mensaje:
            grado_seleccionado = "4to grado"
        
        if grado_seleccionado:
            requisitos = self.obtener_requisitos_grado(grado_seleccionado)
            if requisitos:
                contexto["grado_seleccionado"] = grado_seleccionado
                self.actualizar_estado_sesion(session_id, "requisitos_grado", contexto)
                
                return {
                    "mensaje": f"📋 Para {grado_seleccionado} necesitas los siguientes documentos:\n\n• {requisitos}\n\n¿Te gustaría subirlos ahora para que los revise?",
                    "opciones": [
                        {"texto": "✅ Sí, subir documentos", "valor": "subir_ahora"},
                        {"texto": "❌ No, gracias", "valor": "no_subir"}
                    ],
                    "tipo": "opciones",
                    "session_id": session_id
                }
        
        return {
            "mensaje": "No entendí el grado. Por favor, selecciona uno de los grados disponibles:",
            "opciones": [
                {"texto": "1er grado", "valor": "1er_grado"},
                {"texto": "2do grado", "valor": "2do_grado"},
                {"texto": "3er grado", "valor": "3er_grado"},
                {"texto": "4to grado", "valor": "4to_grado"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }
    
    def procesar_subida_documentos(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la subida de documentos"""
        mensaje_lower = mensaje.lower()
        
        # Detectar si el usuario menciona que no tiene el código SIAGE
        if self.no_tiene_codigo_SIAGE(mensaje):
            self.actualizar_estado_sesion(session_id, "redireccion_presencial", contexto)
            return {
                "mensaje": "📋 Entiendo que no tienes el código SIAGE. En este caso, lo más recomendable es que te atiendas de manera presencial con la secretaria para obtener tu código SIAGE y completar el proceso de matrícula.\n\n" +
                          f"🏫 Dirección: Calle 13B 138, Comas 15311\n" +
                          f"📞 Teléfono: (01) 551 8239\n" +
                          f"🕒 Horario de atención: Lunes a Viernes de 8:00 AM a 4:00 PM\n\n" +
                          f"En la secretaría podrás:\n" +
                          f"• 📋 Obtener tu código SIAGE\n" +
                          f"• 📝 Completar el proceso de matrícula\n" +
                          f"• 💰 Realizar los pagos correspondientes\n" +
                          f"• 📚 Recibir información sobre horarios y materiales\n\n" +
                          f"¿Te gustaría que te ayude con algo más mientras tanto?",
                "opciones": [
                    {"texto": "📋 Ver requisitos de matrícula", "valor": "requisitos"},
                    {"texto": "💰 Consultar costos", "valor": "costos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏫 Información de la institución", "valor": "institucion"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Detectar selección de grado
        grados = ["1er grado", "2do grado", "3er grado", "4to grado"]
        grado_seleccionado = None
        
        for grado in grados:
            if grado.lower() in mensaje_lower:
                grado_seleccionado = grado
                break
        
        # Si se seleccionó un grado, actualizar contexto y pedir documentos
        if grado_seleccionado:
            self.actualizar_estado_sesion(session_id, "subiendo_documentos", {
                "grado_seleccionado": grado_seleccionado,
                "opcion_seleccionada": "subir_documentos"
            })
            
            requisitos = self.obtener_requisitos_grado(grado_seleccionado)
            return {
                "mensaje": f"📋 Para {grado_seleccionado} necesitas los siguientes documentos:\n\n{requisitos}\n\n¿Te gustaría subirlos ahora?",
                "opciones": [
                    {"texto": "✅ Sí, subir documentos", "valor": "confirmar_subida"},
                    {"texto": "❌ No, más tarde", "valor": "cancelar"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Si se confirma la subida de documentos
        if "sí" in mensaje_lower or "si" in mensaje_lower or "yes" in mensaje_lower or "confirmar" in mensaje_lower:
            return {
                "mensaje": "¡Perfecto! 📤 Ahora puedes enviarme una foto clara de cada documento. Te confirmaré si están correctos y te guiaré en el proceso 😊\n\nRecuerda: Necesitas el DNI del menor, código de SIAGE, libreta de notas del año anterior y recibo de agua/luz.",
                "tipo": "subida_archivos",
                "session_id": session_id
            }
        
        # Si se cancela
        if "no" in mensaje_lower or "cancelar" in mensaje_lower:
            self.actualizar_estado_sesion(session_id, "inicio", {})
            return {
                "mensaje": "Entendido. Si necesitas ayuda en otro momento, no dudes en preguntarme. ¿Hay algo más en lo que pueda ayudarte?",
                "opciones": [
                    {"texto": "📚 Información de Matrícula", "valor": "matricula"},
                    {"texto": "📋 Ver Requisitos", "valor": "requisitos"},
                    {"texto": "📤 Subir Documentos", "valor": "subir_documentos"},
                    {"texto": "🔍 Verificar Estado de Matrícula", "valor": "verificar"},
                    {"texto": "👨‍💼 Hablar con Asesor", "valor": "asesor"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Si no se entiende el mensaje
        return {
            "mensaje": "No entendí tu respuesta. ¿Podrías seleccionar una de las opciones disponibles?",
            "opciones": [
                {"texto": "1er grado", "valor": "1er_grado"},
                {"texto": "2do grado", "valor": "2do_grado"},
                {"texto": "3er grado", "valor": "3er_grado"},
                {"texto": "4to grado", "valor": "4to_grado"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }
    
    def procesar_archivos(self, archivos: List[Dict], session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa los archivos subidos por el usuario - versión simplificada"""
        import time
        
        documentos_guardados = []
        
        # Guardar archivos
        for archivo in archivos:
            try:
                doc_id = self.guardar_documento(
                    session_id,
                    archivo.get("tipo", "documento"),
                    archivo.get("nombre", "archivo"),
                    archivo.get("contenido", b"")
                )
                documentos_guardados.append(doc_id)
            except ValueError as e:
                return {
                    "mensaje": f"❌ Error: {str(e)}",
                    "tipo": "texto",
                    "session_id": session_id
                }
        
        # Obtener el grado seleccionado del contexto
        grado_seleccionado = contexto.get("grado_seleccionado", "el grado seleccionado")
        
        # Si se subieron archivos, aceptarlos automáticamente
        if len(documentos_guardados) > 0:
            # Cambiar estado a post_matricula
            self.actualizar_estado_sesion(session_id, "post_matricula", contexto)
            
            # Mensaje de confirmación
            return {
                "mensaje": f"🎉 ¡FELICITACIONES! Tu matrícula para {grado_seleccionado} ha sido APROBADA exitosamente.\n\n" +
                          f"✅ Documentos recibidos: {len(documentos_guardados)} archivo(s)\n\n" +
                          f"📋 Próximos pasos:\n" +
                          f"• Recibirás un correo de confirmación en las próximas 24 horas\n" +
                          f"• Tu matrícula será procesada en 2-3 días hábiles\n" +
                          f"• Te contactaremos para coordinar el pago de la matrícula\n\n" +
                          f"🏫 Bienvenido al I.E.P. Barton! 🎓\n\n" +
                          f"¿Hay algo más en lo que pueda ayudarte?",
                "opciones": [
                    {"texto": "💰 Consultar costos de matrícula", "valor": "costos"},
                    {"texto": "📅 Información del calendario escolar", "valor": "calendario"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏠 Finalizar conversación", "valor": "finalizar"}
                ],
                "tipo": "opciones",
                "session_id": session_id,
                "matricula_aprobada": True,
                "grado": grado_seleccionado,
                "documentos_recibidos": len(documentos_guardados)
            }
        
        return {
            "mensaje": "❌ No se recibieron documentos válidos. Por favor, intenta subir los documentos nuevamente.",
            "tipo": "texto",
            "session_id": session_id
        }
    
    def procesar_verificacion_matricula(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la verificación de estado de matrícula"""
        # Verificar si el usuario menciona que no tiene el código SIAGE
        if self.no_tiene_codigo_SIAGE(mensaje):
            self.actualizar_estado_sesion(session_id, "redireccion_presencial", contexto)
            return {
                "mensaje": Config.get_mensaje("sin_codigo_SIAGE"),
                "opciones": [
                    {"texto": "📋 Ver requisitos de matrícula", "valor": "requisitos"},
                    {"texto": "💰 Consultar costos", "valor": "costos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏫 Información de la institución", "valor": "institucion"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Si tiene el código, proceder con la verificación normal
        # Aquí se integraría con el sistema existente de búsqueda de alumnos
        return {
            "mensaje": f"🔍 Estoy verificando el estado de la matrícula con el código: {mensaje}. Un momento por favor...",
            "tipo": "texto",
            "session_id": session_id
        }
    
    def procesar_conexion_asesor(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la conexión con un asesor con mejor manejo de contexto"""
        
        # Obtener datos actuales de la sesión
        estado_actual = self.obtener_estado_sesion(session_id)
        nombre_actual = estado_actual.get("nombre_usuario")
        telefono_actual = estado_actual.get("telefono_usuario")
        
        # Extraer datos del mensaje actual
        datos_contacto = self.extraer_nombre_telefono(mensaje)
        nombre_nuevo = datos_contacto["nombre"]
        telefono_nuevo = datos_contacto["telefono"]
        
        # Verificar si ya tenemos información completa
        if nombre_actual and telefono_actual:
            # Ya tenemos toda la información, confirmar
            return {
                "mensaje": f"¡Perfecto! 👨‍💼 Ya tengo tu información registrada:\n\n👤 Nombre: {nombre_actual}\n📞 Teléfono: {telefono_actual}\n\nUn asesor especializado se pondrá en contacto contigo en los próximos 30 minutos. Tu solicitud ha sido registrada con prioridad.",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Verificar si tenemos información parcial y completarla
        if nombre_actual and telefono_nuevo:
            # Tenemos nombre pero no teléfono, ahora tenemos teléfono
            self.actualizar_datos_contacto(session_id, nombre_actual, telefono_nuevo)
            return {
                "mensaje": f"¡Perfecto! 👨‍💼 Gracias {nombre_actual}. Un asesor especializado se pondrá en contacto contigo al {telefono_nuevo} en los próximos 30 minutos. Tu solicitud ha sido registrada con prioridad.",
                "tipo": "texto",
                "session_id": session_id
            }
        
        if telefono_actual and nombre_nuevo:
            # Tenemos teléfono pero no nombre, ahora tenemos nombre
            self.actualizar_datos_contacto(session_id, nombre_nuevo, telefono_actual)
            return {
                "mensaje": f"¡Perfecto! 👨‍💼 Gracias {nombre_nuevo}. Un asesor especializado se pondrá en contacto contigo al {telefono_actual} en los próximos 30 minutos. Tu solicitud ha sido registrada con prioridad.",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Verificar si el mensaje actual contiene información completa
        if nombre_nuevo and telefono_nuevo:
            # Tenemos información completa en este mensaje
            self.actualizar_datos_contacto(session_id, nombre_nuevo, telefono_nuevo)
            return {
                "mensaje": f"¡Perfecto! 👨‍💼 Gracias {nombre_nuevo}. Un asesor especializado se pondrá en contacto contigo al {telefono_nuevo} en los próximos 30 minutos. Tu solicitud ha sido registrada con prioridad.",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Verificar si tenemos información parcial
        if nombre_nuevo and not telefono_nuevo:
            # Solo tenemos nombre, pedir teléfono
            self.actualizar_datos_contacto(session_id, nombre_nuevo, None)
            return {
                "mensaje": f"¡Gracias {nombre_nuevo}! 👋 Ahora necesito tu número de teléfono para que el asesor pueda contactarte. ¿Podrías proporcionármelo?",
                "tipo": "texto",
                "session_id": session_id
            }
        
        if telefono_nuevo and not nombre_nuevo:
            # Solo tenemos teléfono, pedir nombre
            self.actualizar_datos_contacto(session_id, None, telefono_nuevo)
            return {
                "mensaje": f"¡Gracias! 📞 Ya tengo tu teléfono: {telefono_nuevo}. Ahora necesito tu nombre completo para que el asesor pueda contactarte. ¿Podrías proporcionármelo?",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # No tenemos información útil, pedir datos completos
        return {
            "mensaje": "👨‍💼 Te voy a conectar con un asesor especializado. Para agilizar el proceso, ¿podrías proporcionarme tu nombre completo y número de teléfono?\n\nPor ejemplo: 'Mi nombre es Juan Pérez y mi teléfono es 999123456'",
            "tipo": "texto",
            "session_id": session_id
        }
    
    def actualizar_datos_contacto(self, session_id: str, nombre: str = None, telefono: str = None):
        """Actualiza los datos de contacto en la sesión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener datos actuales
        cursor.execute('SELECT nombre_usuario, telefono_usuario FROM sesiones WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        nombre_actual = result[0] if result else None
        telefono_actual = result[1] if result else None
        
        # Actualizar solo los campos que se proporcionan
        nombre_final = nombre if nombre else nombre_actual
        telefono_final = telefono if telefono else telefono_actual
        
        cursor.execute('''
            UPDATE sesiones 
            SET nombre_usuario = ?, telefono_usuario = ?
            WHERE id = ?
        ''', (nombre_final, telefono_final, session_id))
        
        conn.commit()
        conn.close()
    
    def procesar_recoleccion_datos(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la recolección de datos del usuario"""
        # Implementar recolección de datos adicionales si es necesario
        return {
            "mensaje": "Gracias por la información. ¿Hay algo más en lo que pueda ayudarte?",
            "tipo": "texto",
            "session_id": session_id
        }
    
    def procesar_redireccion_presencial(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa la redirección a atención presencial"""
        mensaje_lower = mensaje.lower()
        
        # Si el usuario selecciona ver requisitos
        if "requisitos" in mensaje_lower or "1" in mensaje:
            self.actualizar_estado_sesion(session_id, "requisitos_grado", {"opcion_seleccionada": "requisitos"})
            return {
                "mensaje": "¡Excelente! 📋 Te ayudo con los requisitos. ¿Para qué grado necesitas la información?",
                "opciones": [
                    {"texto": "1er grado", "valor": "1er_grado"},
                    {"texto": "2do grado", "valor": "2do_grado"},
                    {"texto": "3er grado", "valor": "3er_grado"},
                    {"texto": "4to grado", "valor": "4to_grado"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Si el usuario selecciona consultar costos
        elif "costos" in mensaje_lower or "precio" in mensaje_lower or "2" in mensaje:
            costos = Config.get_costos()
            return {
                "mensaje": f"💰 Los costos de matrícula para el 2024 son:\n\n• Matrícula: S/ {costos['matricula']}\n• Pensión mensual: S/ {costos['pension_mensual']}\n\n¿Te gustaría proceder con la matrícula o tienes alguna pregunta sobre los costos?",
                "opciones": [
                    {"texto": "📋 Ver requisitos", "valor": "requisitos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏫 Información de la institución", "valor": "institucion"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Si el usuario selecciona hablar con asesor
        elif "asesor" in mensaje_lower or "3" in mensaje:
            self.actualizar_estado_sesion(session_id, "conectando_asesor", {"opcion_seleccionada": "asesor"})
            return {
                "mensaje": "👨‍💼 Te voy a conectar con un asesor especializado. Para agilizar el proceso, ¿podrías proporcionarme tu nombre y número de teléfono?",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Si el usuario selecciona información de la institución
        elif "institucion" in mensaje_lower or "4" in mensaje:
            return {
                "mensaje": f"{Config.get_mensaje('redireccion_presencial')}\n\n• 📋 Obtener tu código SIAGE\n• 📝 Completar el proceso de matrícula\n• 💰 Realizar los pagos correspondientes\n• 📚 Recibir información sobre horarios \n\n🏫 Dirección: Calle 13B 138, Comas 15311\n📞 Teléfono: (01) 551-8239\n🕒 Horario de atención: Lunes a Viernes de 8:00 AM a 4:00 PM\n\n¿Te gustaría que te ayude con algo más?",
                "opciones": [
                    {"texto": "📋 Ver requisitos", "valor": "requisitos"},
                    {"texto": "💰 Consultar costos", "valor": "costos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🙏 Agradecer y terminar", "valor": "agradecer"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Si el usuario quiere agradecer y terminar
        elif "agradecer" in mensaje_lower or "gracias" in mensaje_lower or "terminar" in mensaje_lower:
            self.actualizar_estado_sesion(session_id, "inicio", {})
            return {
                "mensaje": Config.get_mensaje("agradecimiento_paciencia"),
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Respuesta por defecto
        else:
            return {
                "mensaje": f"{Config.get_mensaje('redireccion_presencial')}\n\n• 📋 Obtener tu código SIAGE\n• 📝 Completar el proceso de matrícula\n• 💰 Realizar los pagos correspondientes\n• 📚 Recibir información sobre horarios\n\n🏫 Dirección: Calle 13B 138, Comas 15311\n📞 Teléfono: (01) 551-8239\n🕒 Horario de atención: Lunes a Viernes de 8:00 AM a 4:00 PM\n\n¿En qué más puedo ayudarte?",
                "opciones": [
                    {"texto": "📋 Ver requisitos", "valor": "requisitos"},
                    {"texto": "💰 Consultar costos", "valor": "costos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏫 Información de la institución", "valor": "institucion"},
                    {"texto": "🙏 Agradecer y terminar", "valor": "agradecer"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
    
    def respuesta_generica(self, mensaje: str, session_id: str) -> Dict[str, Any]:
        """Respuesta genérica cuando no se entiende el mensaje"""
        return {
            "mensaje": "No entendí tu mensaje. ¿Te gustaría información sobre el proceso de matrícula o hay algo específico en lo que pueda ayudarte?",
            "opciones": [
                {"texto": "📚 Información de Matrícula", "valor": "matricula"},
                {"texto": "📋 Ver Requisitos", "valor": "requisitos"},
                {"texto": "💰 Consultar Pagos", "valor": "pagos"},
                {"texto": "📞 Hablar con Asesor", "valor": "asesor"}
            ],
            "tipo": "opciones",
            "session_id": session_id
        }

    def procesar_opciones_post_matricula(self, mensaje: str, session_id: str, contexto: Dict) -> Dict[str, Any]:
        """Procesa las opciones después de la aprobación de matrícula"""
        mensaje_lower = mensaje.lower()
        costos = Config.get_costos()
        
        # Consultar costos de matrícula
        if "costos" in mensaje_lower or "precio" in mensaje_lower or "pago" in mensaje_lower:
            return {
                "mensaje": f"💰 Costos de matrícula para el 2024:\n\n" +
                          f"• Matrícula: S/ {costos['matricula']}\n" +
                          f"• Pensión mensual: S/ {costos['pension_mensual']}\n"
                          "\n\n" +
                          f"📋 Formas de pago:\n" +
                          f"• Transferencia bancaria\n" +
                          f"• Depósito en efectivo\n" +
                          f"• Tarjeta de crédito/débito\n\n" +
                          f"¿Te gustaría que te ayude con algo más?",
                "opciones": [
                    {"texto": "📅 Información del calendario escolar", "valor": "calendario"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏠 Finalizar conversación", "valor": "finalizar"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Información del calendario escolar
        elif "calendario" in mensaje_lower or "horarios" in mensaje_lower or "fechas" in mensaje_lower:
            return {
                "mensaje": f"📅 Calendario Escolar 2024 - I.E.P. Barton\n\n" +
                          f"📚 Inicio de clases: 1 de marzo de 2024\n" +
                          f"🏫 Horario de clases: 8:00 AM - 2:00 PM\n" +
                          f"🍽️ Recreo: 10:30 AM - 11:00 AM\n\n" +
                          f"📆 Fechas importantes:\n" +
                          f"• Matrícula: Hasta el 28 de febrero\n" +
                          f"• Inicio de clases: 1 de marzo\n" +
                          f"• Vacaciones de julio: 15-31 de julio\n" +
                          f"• Fin de año: 20 de diciembre\n\n" +
                          f"📋 Uniforme escolar:\n" +
                          f"• Polo blanco con logo del colegio\n" +
                          f"• Pantalón azul marino\n" +
                          f"• Zapatos negros\n\n" +
                          f"¿Necesitas información sobre algo más?",
                "opciones": [
                    {"texto": "💰 Consultar costos de matrícula", "valor": "costos"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏠 Finalizar conversación", "valor": "finalizar"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }
        
        # Hablar con asesor
        elif "asesor" in mensaje_lower or "hablar" in mensaje_lower or "contacto" in mensaje_lower:
            self.actualizar_estado_sesion(session_id, "conectando_asesor", contexto)
            return {
                "mensaje": "👨‍💼 Te voy a conectar con un asesor especializado. Para agilizar el proceso, ¿podrías proporcionarme tu nombre y número de teléfono?\n\nPor ejemplo: 'Mi nombre es Juan Pérez y mi teléfono es 999123456'",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Finalizar conversación
        elif "finalizar" in mensaje_lower or "terminar" in mensaje_lower or "gracias" in mensaje_lower or "adiós" in mensaje_lower:
            self.actualizar_estado_sesion(session_id, "inicio", {})
            return {
                "mensaje": "¡Muchas gracias por confiar en el I.E.P. Barton! 🎓\n\n" +
                          f"Tu matrícula ha sido procesada exitosamente. Recuerda:\n" +
                          f"• Revisar tu correo electrónico en las próximas 24 horas\n" +
                          f"• Estar atento a nuestras llamadas para coordinar el pago\n" +
                          f"• Preparar los materiales escolares para el inicio de clases\n\n" +
                          f"🏫 Bienvenido a nuestra familia educativa! 🌟\n\n" +
                          f"Si tienes alguna consulta adicional, no dudes en contactarnos.\n" +
                          f"¡Que tengas un excelente día! 👋",
                "tipo": "texto",
                "session_id": session_id
            }
        
        # Si no se entiende la opción
        else:
            return {
                "mensaje": "No entendí tu selección. Por favor, elige una de las opciones disponibles:",
                "opciones": [
                    {"texto": "💰 Consultar costos de matrícula", "valor": "costos"},
                    {"texto": "📅 Información del calendario escolar", "valor": "calendario"},
                    {"texto": "👨‍💼 Hablar con asesor", "valor": "asesor"},
                    {"texto": "🏠 Finalizar conversación", "valor": "finalizar"}
                ],
                "tipo": "opciones",
                "session_id": session_id
            }

# Instancia global del chatbot
chatbot = ChatbotInteligente() 