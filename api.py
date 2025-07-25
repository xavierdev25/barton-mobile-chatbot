from flask import Flask, request, jsonify
from chatbot_matricula import cargar_datos_varios_csv, responder_pregunta, buscar_por_codigo, ARCHIVOS_GRADOS
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde el frontend

alumnos = cargar_datos_varios_csv(ARCHIVOS_GRADOS)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    pregunta = data.get('pregunta', '')
    if not pregunta:
        return jsonify({'error': 'Falta la pregunta'}), 400
    respuesta = responder_pregunta(pregunta, alumnos)
    if respuesta:
        return jsonify({'respuesta': respuesta})
    return jsonify({'respuesta': 'No entendí la pregunta o no encontré información.'})

@app.route('/pagos', methods=['GET'])
def pagos():
    codigo = request.args.get('codigo')
    if not codigo:
        return jsonify({'error': 'Falta el código modular'}), 400
    alumno = buscar_por_codigo(alumnos, codigo)
    if not alumno:
        return jsonify({'error': 'No se encontró ningún alumno con ese código modular.'}), 404
    pagos = []
    detalle = []
    total = 0
    if 'Matrícula pendiente' in alumno and alumno.get('Matrícula pendiente', '').strip().lower() == 'sí':
        pagos.append('Matrícula')
        detalle.append('Matrícula: 300 soles')
        total += 300
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
        detalle.append(f"Pensiones: {pensiones_pendientes} x 150 soles = {pensiones_pendientes*150} soles")
        total += pensiones_pendientes * 150
    return jsonify({
        'grado': alumno.get('Grado', 'Desconocido'),
        'nombre': alumno.get('APELLIDOS Y NOMBRES', 'Desconocido'),
        'codigo': alumno.get('Código modular (SIAGE)') or alumno.get('codigo modular (SIAGE)'),
        'pagos': pagos,
        'detalle': detalle,
        'total': total
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 