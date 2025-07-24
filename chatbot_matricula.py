import csv
import os

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

def main():
    print("Bienvenido al Chatbot de Matrícula y Pensión.")
    print("Escribe 'salir' para terminar.\n")
    alumnos = cargar_datos_varios_csv(ARCHIVOS_GRADOS)
    if not alumnos:
        print("[ERROR] No se encontraron datos de alumnos en los archivos CSV.")
        return
    while True:
        codigo = input("Introduce el código modular (SIAGE) del alumno: ").strip()
        if codigo.lower() == 'salir':
            print("¡Hasta luego!")
            break
        alumno = buscar_por_codigo(alumnos, codigo)
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