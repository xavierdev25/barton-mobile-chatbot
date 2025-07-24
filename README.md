# Chatbot de Matrícula y Pensión (Terminal)

## Descripción
Este chatbot te permite consultar, desde la terminal, la información de matrícula y pensiones pendientes de alumnos de 1er, 2do, 3er y 4to grado de primaria. Utiliza archivos CSV locales para cada grado y no requiere conexión a internet ni dependencias externas.

## Archivos necesarios
Coloca en la misma carpeta del script los siguientes archivos CSV (ya incluidos y listos para usar):
- `lista primaria 1ro y 2do.xlsx - 1er grado.csv`
- `lista primaria 1ro y 2do.xlsx - 2do grado.csv`
- `lista primaria 1ro y 2do.xlsx - 3er grado.csv`
- `lista primaria 1ro y 2do.xlsx - 4to grado.csv`

Cada archivo debe tener como primera fila los encabezados, por ejemplo:
```
N°,APELLIDOS Y NOMBRES,Código modular (SIAGE),fecha de registro,hora de inicio,hora de fin,Matrícula pendiente,Pensiones pendientes
```
Y luego los datos de los alumnos.

## ¿Cómo agregar o modificar datos?
- Abre el archivo CSV correspondiente con Excel, LibreOffice o un editor de texto.
- Puedes agregar, editar o eliminar alumnos.
- Para que el chatbot calcule pagos, asegúrate de tener las columnas:
  - `Matrícula pendiente` (Sí/No)
  - `Pensiones pendientes` (número entero)

## ¿Cómo ejecutar el chatbot?
1. Abre la terminal en la carpeta del proyecto.
2. Ejecuta:
   ```
   python chatbot_matricula.py
   ```
3. Ingresa el código modular (SIAGE) del alumno cuando se te pida.
4. Escribe `salir` para terminar.

## Notas
- No necesitas instalar nada extra, solo Python 3.x.
- El sistema buscará en los cuatro grados y mostrará el grado correspondiente en la respuesta.
- Si no existen datos de pagos para un alumno, solo mostrará los datos personales.

## Ejemplo de uso
```
Introduce el código modular (SIAGE) del alumno: 10799450091232

==============================
      INFORMACIÓN DEL ALUMNO
==============================
Grado:                1er grado
Nombre:               BERNUY JULCA, Aimee Valentina
Código modular:       10799450091232
------------------------------
Pagos pendientes:
- Matrícula
- Pensiones (2)

Detalle de pagos:
  Matrícula: 350 soles
  Pensiones: 2 x 150 soles = 300 soles

TOTAL A PAGAR: 650 soles
==============================
``` 
