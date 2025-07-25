# Chatbot de Matrícula y Pensión (Terminal)

## Descripción

Este chatbot te permite consultar, desde la terminal, la información de matrícula y pensiones pendientes de alumnos de 1ro, 2do, 3ro y 4to grado de primaria. Utiliza archivos CSV locales para cada grado y no requiere conexión a internet ni dependencias externas.

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
3. Puedes ingresar el **código modular (SIAGE)** del alumno, o hacer preguntas por **nombre**.
4. Escribe `salir` para terminar.

## Funcionalidades principales

- Consulta por **código modular**: muestra la información y pagos pendientes del alumno.
- Consulta por **nombre**: puedes preguntar por el código, matrícula o pensión de un alumno usando su nombre o apellidos.
- Manejo de **nombres repetidos**: si hay varios alumnos con el mismo nombre, el bot mostrará la lista de coincidencias y te pedirá que indiques el código modular para continuar.
- Respuestas automáticas para preguntas como:
  - ¿Cuál es el código de Diaz Cuya?
  - ¿Cuánta pensión debe Mendoza Valladares?
  - ¿Debe matrícula Pariona Castillo?

## Ejemplos de uso

```
Haz tu pregunta o introduce el código modular (SIAGE) del alumno: ¿Cuál es el código de Diaz Cuya?
El código de DIAZ CUYA, Masiell Khaleesi es 10799450104279.

Haz tu pregunta o introduce el código modular (SIAGE) del alumno: ¿Cuánta pensión debe Mendoza Valladares?
Por favor, introduzca su código en la sección de pagos para ver el detalle de su deuda.

Haz tu pregunta o introduce el código modular (SIAGE) del alumno: ¿Cuál es el código de Juan Perez?
He encontrado varios alumnos con ese nombre. Por favor, indique el código modular (SIAGE) para continuar.
Coincidencias:
- PEREZ GARCIA, Juan (código: 111)
- PEREZ GARCIA, Juan (código: 222)
- PEREZ GARCIA, Juan Carlos (código: 333)

Haz tu pregunta o introduce el código modular (SIAGE) del alumno: 111

==============================
      INFORMACIÓN DEL ALUMNO
==============================
Grado:                1er grado
Nombre:               PEREZ GARCIA, Juan
Código modular:       111
------------------------------
Pagos pendientes:
- Matrícula
- Pensiones (2)

Detalle de pagos:
  Matrícula: 300 soles
  Pensiones: 2 x 150 soles = 300 soles

TOTAL A PAGAR: 650 soles
==============================
```

## Recomendaciones y advertencias

- Si hay varios alumnos con el mismo nombre, deberás especificar el código modular para obtener información detallada.
- Para mejores resultados, usa el nombre completo o apellidos completos.
- El bot ignora preguntas ambiguas o palabras sueltas como "matricula", "pension", etc.
- Si no encuentra coincidencias, responderá "No encontré ese alumno."

## Notas

- No necesitas instalar nada extra, solo Python 3.x.
- El sistema buscará en los cuatro grados y mostrará el grado correspondiente en la respuesta.
- Si no existen datos de pagos para un alumno, solo mostrará los datos personales.
