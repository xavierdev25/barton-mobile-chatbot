from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
import json
import traceback
from datetime import datetime
from chatbot_inteligente import chatbot
from chatbot_matricula import cargar_datos_varios_csv, buscar_por_codigo, ARCHIVOS_GRADOS
from config import Config

app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

# Cargar datos de alumnos existentes
try:
    alumnos = cargar_datos_varios_csv(ARCHIVOS_GRADOS)
    print(f"✅ Datos de alumnos cargados: {len(alumnos)} registros")
except Exception as e:
    print(f"❌ Error cargando datos de alumnos: {e}")
    alumnos = []

@app.route('/chatbot-inteligente', methods=['POST'])
def chatbot_inteligente():
    """Endpoint principal del chatbot inteligente"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Se requiere un JSON válido'}), 400
        
        mensaje = data.get('mensaje', '')
        session_id = data.get('session_id')
        archivos = data.get('archivos', [])
        
        print(f"📨 Mensaje recibido: '{mensaje}' | Session ID: {session_id}")
        
        if not mensaje and not archivos:
            return jsonify({'error': 'Se requiere un mensaje o archivos'}), 400
        
        # Validar longitud del mensaje
        if mensaje and len(mensaje) > Config.MAX_MESSAGE_LENGTH:
            return jsonify({'error': f'El mensaje es demasiado largo. Máximo {Config.MAX_MESSAGE_LENGTH} caracteres'}), 400
        
        # Procesar archivos si se enviaron
        archivos_procesados = []
        if archivos:
            for archivo in archivos:
                try:
                    # Decodificar el contenido base64
                    contenido = base64.b64decode(archivo.get('contenido', ''))
                    archivos_procesados.append({
                        'tipo': archivo.get('tipo', 'documento'),
                        'nombre': archivo.get('nombre', 'archivo'),
                        'contenido': contenido
                    })
                except Exception as e:
                    return jsonify({'error': f'Error procesando archivo: {str(e)}'}), 400
        
        # Procesar mensaje con el chatbot inteligente
        print(f"🤖 Procesando mensaje con chatbot...")
        respuesta = chatbot.procesar_mensaje(
            mensaje=mensaje,
            session_id=session_id,
            archivos=archivos_procesados if archivos_procesados else None
        )
        
        print(f"✅ Respuesta generada: {respuesta.get('mensaje', '')[:50]}...")
        return jsonify(respuesta)
        
    except Exception as e:
        print(f"❌ Error en chatbot-inteligente: {str(e)}")
        print(f"📋 Traceback completo:")
        traceback.print_exc()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/verificar-matricula', methods=['POST'])
def verificar_matricula():
    """Endpoint para verificar estado de matrícula usando el sistema existente"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Se requiere un JSON válido'}), 400
        
        codigo = data.get('codigo', '')
        
        if not codigo:
            return jsonify({'error': 'Se requiere el código SIAGE'}), 400
        
        # Buscar alumno usando el sistema existente
        alumno = buscar_por_codigo(alumnos, codigo)
        
        if not alumno:
            return jsonify({
                'encontrado': False,
                'mensaje': 'No se encontró ningún alumno con ese código SIAGE. Por favor, verifica el código e intenta nuevamente.'
            })
        
        # Calcular pagos pendientes
        pagos = []
        detalle = []
        total = 0
        costos = Config.get_costos()
        
        # Matrícula
        if 'Matrícula pendiente' in alumno and alumno.get('Matrícula pendiente', '').strip().lower() == 'sí':
            pagos.append('Matrícula')
            detalle.append(f'Matrícula: S/ {costos["matricula"]}')
            total += costos["matricula"]
        
        # Pensiones
        pensiones_pendientes = 0
        if 'Pensiones pendientes' in alumno:
            try:
                pensiones_pendientes = int(alumno['Pensiones pendientes'])
            except (ValueError, TypeError):
                pensiones_pendientes = 0
        elif 'Pensión pendiente' in alumno and alumno.get('Pensión pendiente', '').strip().lower() == 'sí':
            pensiones_pendientes = 1
        
        if pensiones_pendientes > 0:
            pagos.append(f"Pensiones ({pensiones_pendientes})")
            detalle.append(f"Pensiones: {pensiones_pendientes} x S/ {costos['pension_mensual']} = S/ {pensiones_pendientes * costos['pension_mensual']}")
            total += pensiones_pendientes * costos['pension_mensual']
        
        return jsonify({
            'encontrado': True,
            'alumno': {
                'grado': alumno.get('Grado', 'Desconocido'),
                'nombre': alumno.get('APELLIDOS Y NOMBRES', 'Desconocido'),
                'codigo': alumno.get('Código modular (SIAGE)') or alumno.get('codigo modular (SIAGE)'),
            },
            'pagos': pagos,
            'detalle': detalle,
            'total': total,
            'mensaje': f"✅ Estado de matrícula para {alumno.get('APELLIDOS Y NOMBRES', 'Desconocido')}: {'Tiene pagos pendientes' if pagos else 'No tiene pagos pendientes'}"
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/documentos/<session_id>', methods=['GET'])
def obtener_documentos(session_id):
    """Obtiene los documentos subidos en una sesión"""
    try:
        if not session_id:
            return jsonify({'error': 'Se requiere el session_id'}), 400
        
        import sqlite3
        conn = sqlite3.connect(chatbot.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, tipo_documento, nombre_archivo, estado, fecha_subida
            FROM documentos 
            WHERE sesion_id = ?
            ORDER BY fecha_subida DESC
        ''', (session_id,))
        
        documentos = []
        for row in cursor.fetchall():
            documentos.append({
                'id': row[0],
                'tipo': row[1],
                'nombre': row[2],
                'estado': row[3],
                'fecha_subida': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'documentos': documentos,
            'total': len(documentos)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/sesion/<session_id>', methods=['GET'])
def obtener_sesion(session_id):
    """Obtiene información de una sesión específica"""
    try:
        if not session_id:
            return jsonify({'error': 'Se requiere el session_id'}), 400
        
        estado = chatbot.obtener_estado_sesion(session_id)
        return jsonify(estado)
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/historial/<session_id>', methods=['GET'])
def obtener_historial(session_id):
    """Obtiene el historial de conversación de una sesión"""
    try:
        if not session_id:
            return jsonify({'error': 'Se requiere el session_id'}), 400
        
        import sqlite3
        conn = sqlite3.connect(chatbot.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT mensaje_usuario, respuesta_bot, timestamp
            FROM historial_conversacion 
            WHERE sesion_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        historial = []
        for row in cursor.fetchall():
            historial.append({
                'mensaje_usuario': row[0],
                'respuesta_bot': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'historial': historial,
            'total_mensajes': len(historial)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/requisitos/<grado>', methods=['GET'])
def obtener_requisitos(grado):
    """Obtiene los requisitos para un grado específico"""
    try:
        if not grado:
            return jsonify({'error': 'Se requiere el grado'}), 400
        
        requisitos = chatbot.obtener_requisitos_grado(grado)
        if requisitos:
            return jsonify({
                'grado': grado,
                'requisitos': requisitos,
                'mensaje': f'Requisitos para {grado}: {requisitos}'
            })
        else:
            return jsonify({'error': f'No se encontraron requisitos para {grado}'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/nueva-sesion', methods=['POST'])
def crear_nueva_sesion():
    """Crea una nueva sesión de chat"""
    try:
        session_id = chatbot.crear_sesion()
        return jsonify({
            'session_id': session_id,
            'mensaje': 'Nueva sesión creada exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/costos', methods=['GET'])
def obtener_costos():
    """Obtiene los costos de matrícula"""
    try:
        costos = Config.get_costos()
        return jsonify({
            'costos': costos,
            'mensaje': f'Costos de matrícula: Matrícula S/ {costos["matricula"]}, Pensión mensual S/ {costos["pension_mensual"]}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/grados', methods=['GET'])
def obtener_grados():
    """Obtiene los grados disponibles"""
    try:
        grados = Config.get_grados()
        return jsonify({
            'grados': grados,
            'total': len(grados)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas del sistema"""
    try:
        import sqlite3
        conn = sqlite3.connect(chatbot.db_path)
        cursor = conn.cursor()
        
        # Contar sesiones
        cursor.execute('SELECT COUNT(*) FROM sesiones')
        total_sesiones = cursor.fetchone()[0]
        
        # Contar documentos
        cursor.execute('SELECT COUNT(*) FROM documentos')
        total_documentos = cursor.fetchone()[0]
        
        # Contar mensajes
        cursor.execute('SELECT COUNT(*) FROM historial_conversacion')
        total_mensajes = cursor.fetchone()[0]
        
        # Sesiones activas (últimas 24 horas)
        cursor.execute('''
            SELECT COUNT(*) FROM sesiones 
            WHERE fecha_actualizacion > datetime('now', '-1 day')
        ''')
        sesiones_activas = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_sesiones': total_sesiones,
            'total_documentos': total_documentos,
            'total_mensajes': total_mensajes,
            'sesiones_activas_24h': sesiones_activas,
            'alumnos_cargados': len(alumnos) if alumnos else 0,
            'configuracion': {
                'max_file_size_mb': Config.MAX_FILE_SIZE / (1024*1024),
                'max_message_length': Config.MAX_MESSAGE_LENGTH,
                'session_timeout_hours': Config.SESSION_TIMEOUT_HOURS
            }
        })
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud del sistema"""
    try:
        import sqlite3
        conn = sqlite3.connect(chatbot.db_path)
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'Chatbot inteligente funcionando correctamente',
            'tablas_disponibles': tablas,
            'alumnos_cargados': len(alumnos) if alumnos else 0,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error en el sistema: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/limpiar-sesion/<session_id>', methods=['DELETE'])
def limpiar_sesion(session_id):
    """Limpia una sesión específica"""
    try:
        if not session_id:
            return jsonify({'error': 'Se requiere el session_id'}), 400
        
        import sqlite3
        conn = sqlite3.connect(chatbot.db_path)
        cursor = conn.cursor()
        
        # Eliminar documentos de la sesión
        cursor.execute('DELETE FROM documentos WHERE sesion_id = ?', (session_id,))
        
        # Eliminar historial de la sesión
        cursor.execute('DELETE FROM historial_conversacion WHERE sesion_id = ?', (session_id,))
        
        # Eliminar la sesión
        cursor.execute('DELETE FROM sesiones WHERE id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'mensaje': 'Sesión limpiada exitosamente',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

if __name__ == '__main__':
    server_config = Config.get_server_config()
    app.run(
        host=server_config['host'], 
        port=server_config['port'], 
        debug=server_config['debug']
    ) 