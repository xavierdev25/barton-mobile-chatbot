import csv
import os
import re
from difflib import get_close_matches
import unicodedata

ARCHIVOS_GRADOS = [
    'lista primaria 1ro y 2do.xlsx - 1er grado.csv',
    'lista primaria 1ro y 2do.xlsx - 2do grado.csv',
    'lista primaria 1ro y 2do.xlsx - 3er grado.csv',
    'lista primaria 1ro y 2do.xlsx - 4to grado.csv',
]

def cargar_datos_varios_csv(archivos):
    alumnos = []
    for archivo in archivos:
        if not os.path.exists(archivo):
            continue
        with open(archivo, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for fila in reader:
                fila['Grado'] = os.path.basename(archivo).split(' - ')[-1].replace('.csv','')
                alumnos.append(fila)
    return alumnos

def buscar_por_codigo(alumnos, codigo):
    for alumno in alumnos:
        cod = alumno.get('Código modular (SIAGE)') or alumno.get('codigo modular (SIAGE)')
        if cod and str(cod).strip() == codigo.strip():
            return alumno
    return None

def normalizar(texto):
    texto = texto.lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', '', texto)

def buscar_por_nombre_parcial(alumnos, nombre):
    nombre = normalizar(nombre)
    coincidencias = []
    for alumno in alumnos:
        nombre_alumno = normalizar(alumno.get('APELLIDOS Y NOMBRES', ''))
        # Coincidencia exacta o parcial (palabra completa)
        if nombre in nombre_alumno:
            coincidencias.append(alumno)
        else:
            palabras_nombre = set(nombre.split())
            palabras_alumno = set(nombre_alumno.split())
            interseccion = palabras_nombre & palabras_alumno
            if len(interseccion) >= 2:
                coincidencias.append(alumno)
    if len(coincidencias) == 1:
        return coincidencias[0]
    elif len(coincidencias) > 1:
        return coincidencias
    # Búsqueda difusa solo si hay al menos 2 palabras y cutoff muy alto
    palabras_nombre = nombre.split()
    if len(palabras_nombre) >= 2:
        nombres_lista = [normalizar(a.get('APELLIDOS Y NOMBRES','')) for a in alumnos]
        from difflib import get_close_matches
        coincidencias_difusas = get_close_matches(nombre, nombres_lista, n=5, cutoff=0.99)
        coincidencias_alumnos = [alumnos[nombres_lista.index(c)] for c in coincidencias_difusas]
        # Solo aceptar si todas las palabras del nombre buscado están presentes en el nombre del alumno
        coincidencias_filtradas = []
        for a in coincidencias_alumnos:
            nombre_alumno = normalizar(a.get('APELLIDOS Y NOMBRES',''))
            if all(palabra in nombre_alumno for palabra in palabras_nombre):
                coincidencias_filtradas.append(a)
        if len(coincidencias_filtradas) == 1:
            return coincidencias_filtradas[0]
        elif len(coincidencias_filtradas) > 1:
            return coincidencias_filtradas
    return None

def extraer_nombre_de_pregunta(pregunta, alumnos):
    pregunta = normalizar(pregunta)
    palabras = pregunta.split()
    for n in range(3,0,-1):
        for i in range(len(palabras)-n+1):
            fragmento = ' '.join(palabras[i:i+n])
            resultado = buscar_por_nombre_parcial(alumnos, fragmento)
            if resultado:
                return resultado
    return None

def responder_pregunta(pregunta, alumnos):
    pregunta_limpia = normalizar(pregunta)
    palabras_sueltas = {'matricula','pension','pensiones','deuda','codigo','código'}
    if pregunta_limpia.strip() in palabras_sueltas:
        return None

    # Buscar por código modular directamente en la pregunta
    codigos_encontrados = re.findall(r'\b\d{8,14}\b', pregunta)
    if codigos_encontrados:
        respuestas = []
        for cod in codigos_encontrados:
            alumno = buscar_por_codigo(alumnos, cod)
            if alumno:
                respuestas.append(f"Estudiante: {alumno.get('APELLIDOS Y NOMBRES', 'Desconocido')}\nCódigo: {cod}\nGrado: {alumno.get('Grado', 'Desconocido')}")
        if respuestas:
            return '\n\n'.join(respuestas)
        else:
            return "No se encontró ningún estudiante con ese código."

    # Buscar por nombre en la pregunta
    resultado = extraer_nombre_de_pregunta(pregunta, alumnos)
    if isinstance(resultado, list):
        lista = '\n'.join([
            f"- {a.get('APELLIDOS Y NOMBRES','Desconocido')} (código: {a.get('Código modular (SIAGE)') or a.get('codigo modular (SIAGE)','Desconocido')}, grado: {a.get('Grado','Desconocido')})"
            for a in resultado
        ])
        return f"He encontrado varios estudiantes con ese nombre. Por favor, indique el código modular (SIAGE) para mayor precisión.\nCoincidencias:\n{lista}"
    elif resultado:
        cod = resultado.get('Código modular (SIAGE)') or resultado.get('codigo modular (SIAGE)')
        nombre = resultado.get('APELLIDOS Y NOMBRES', 'Desconocido')
        grado = resultado.get('Grado', 'Desconocido')
        return f"Estudiante: {nombre}\nCódigo: {cod}\nGrado: {grado}"
    else:
        # Si la pregunta contiene palabras clave pero no se encontró coincidencia
        if any(palabra in pregunta_limpia for palabra in ['codigo','código','nombre','alumno','estudiante']):
            return "No se encontró ningún estudiante que coincida con la información proporcionada. Por favor, revise el nombre o código."
        return None

def main():
    print("Bienvenido al Chatbot de Matrícula y Pensión.")
    print("Escribe 'salir' para terminar.\n")
    alumnos = cargar_datos_varios_csv(ARCHIVOS_GRADOS)
    if not alumnos:
        print("[ERROR] No se encontraron datos de alumnos en los archivos CSV.")
        return
    while True:
        entrada = input("Haz tu pregunta o introduce el código modular (SIAGE) del alumno: ").strip()
        if entrada.lower() == 'salir':
            print("¡Hasta luego!")
            break
        # Intentar responder como pregunta
        respuesta = responder_pregunta(entrada, alumnos)
        if respuesta:
            print(respuesta + "\n")
            continue
        # Si no es pregunta, asumir que es código
        alumno = buscar_por_codigo(alumnos, entrada)
        if alumno:
            print("\n==============================")
            print("      INFORMACIÓN DEL ALUMNO")
            print("==============================")
            print(f"Grado:                {alumno.get('Grado', 'Desconocido')}")
            print(f"Nombre:               {alumno.get('APELLIDOS Y NOMBRES', 'Desconocido')}")
            cod = alumno.get('Código modular (SIAGE)') or alumno.get('codigo modular (SIAGE)')
            print(f"Código modular:       {cod if cod else 'Desconocido'}")
            print("------------------------------")
            pagos = []
            detalle = []
            total = 0
            # Matrícula
            if 'Matrícula pendiente' in alumno and alumno.get('Matrícula pendiente', '').strip().lower() == 'sí':
                pagos.append('Matrícula')
                detalle.append('Matrícula: 350 soles')
                total += 350
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
                detalle.append(f"Pensiones: {pensiones_pendientes} x 150 soles = {pensiones_pendientes*150} soles")
                total += pensiones_pendientes * 150
            print("Pagos pendientes:")
            if pagos:
                for p in pagos:
                    print(f"- {p}")
                print("\nDetalle de pagos:")
                for d in detalle:
                    print(f"  {d}")
                print(f"\nTOTAL A PAGAR: {total} soles")
            else:
                print("- No tiene pagos pendientes o no hay información de pagos en la hoja.")
            print("==============================\n")
        else:
            print("No se encontró ningún alumno con ese código modular.\n")

if __name__ == "__main__":
    main() 