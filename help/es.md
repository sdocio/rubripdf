## Qué es RubriPDF

RubriPDF te ayuda a evaluar con rúbricas de principio a fin. A partir de una rúbrica y de la lista de alumnado genera, para cada estudante, una hoja de evaluación en PDF que corriges cómodamente en el ordenador; al terminar, la aplicación recoge todas las notas en un único archivo.

Las secciones de esta ayuda siguen el orden habitual de trabajo: configurar el documento, definir los criterios, añadir el alumnado, generar el PDF, corregir y, por último, extraer las notas.

## Configurar el documento

En esta primera parte defines la cabecera de las hojas. La **Materia** es el título grande de la portada, y el **Curso académico** y el **Título de la prueba** forman el subtítulo.

Con el **Idioma** elegimos la lengua en la que se imprime el PDF, que no tiene por qué coincidir con la de la interfaz (esta se cambia arriba a la izquierda). El **Color de la cabecera**, en formato R,G,B de 0 a 255, es el fondo sobre el que aparece el nombre de cada alumno.

## Definir los criterios

Añade tantos criterios como necesites, cada uno con una descripción y su puntuación máxima. Con los botones puedes añadir o eliminar filas, y arrastrándolas por la izquierda les cambias el orden. La puntuación total se actualiza sola a medida que editas.

## Añadir el alumnado

Puedes escribir los nombres a mano o importarlos de un archivo. RubriPDF reconoce tres orígenes y detecta solo cuál es:

- la lista de la **Secretaría Virtual** (.xls),
- la exportación de participantes de **Moodle** (.xlsx),
- cualquier **lista simple** (un .txt o un CSV de una columna, con un nombre por línea).

Si algo no encaja —columnas que hubo que deducir, nombres repetidos o un archivo con varias columnas— te avisa en el momento. Los nombres se guardan exactamente como vienen, sin retocarlos, para que coincidan con los de otros sistemas. También puedes arrastrarlos para ordenarlos.

## Opciones de salida

Antes de generar, puedes añadir páginas extra de notas por alumno (hojas en blanco adicionales para observaciones) y activar **«Guiar las observaciones con la rúbrica»**, que rellena el cuadro de observaciones de cada alumno con los criterios numerados, para comentar punto por punto.

## Generar el PDF

Al pulsar **«Generar PDF»** obtienes un documento con una hoja por alumno. Cada hoja lleva la tabla de criterios, el campo de la nota final, una marca de «No presentado» y un espacio para observaciones, todo en campos de formulario que se rellenan directamente en el ordenador (comprobado en Firefox y Chrome).

## Corregir y extraer las notas

Corrige el PDF en un lector de PDF, marcando los criterios y escribiendo las notas. Cuando termines, vuelve a cargarlo en la sección de extracción y descarga el CSV con las notas.

Durante la extracción se hace una comprobación de calidad que te avisa de posibles errores: criterios sin puntuar, notas que no son números, sumas que no cuadran, valores por encima del máximo o alumnos marcados como «No presentado» que aun así tienen notas. Si dejaste la nota final en blanco pero puntuaste los criterios, se completa sola con la suma.

El separador decimal y el del CSV se adaptan al idioma (coma y «;» en gallego, español y portugués; punto y «,» en inglés). Si marcas **«CSV detallado»**, el archivo incluye además una columna por cada criterio.

## Guardar y reutilizar la configuración

Con los botones de guardar y cargar puedes exportar toda la configuración —materia, criterios y opciones— a un archivo JSON y recuperarla cuando quieras, por ejemplo para otra prueba de la misma materia. Además, el trabajo en curso se conserva en el navegador aunque cierres o recargues la página.

## Privacidad

RubriPDF funciona por completo en tu ordenador: ni los nombres del alumnado ni las notas se envían a ningún servidor externo.
