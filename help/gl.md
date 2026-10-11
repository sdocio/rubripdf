## Que é RubriPDF

RubriPDF axúdache a avaliar con rúbricas de principio a fin. A partir dunha rúbrica e da lista de alumnado xera, para cada estudante, unha folla de avaliación en PDF que corriges cómodamente no ordenador; ao rematar, a aplicación recolle todas as notas nun único ficheiro.

As seccións desta axuda seguen a orde habitual de traballo: configurar o documento, definir os criterios, engadir o alumnado, xerar o PDF, corrixir e, por último, extraer as notas.

## Configurar o documento

Nesta primeira parte defines a cabeceira das follas. A **Materia** é o título grande da portada, e o **Curso académico** e o **Título da proba** forman o subtítulo.

Coa **Lingua** eliximos o idioma no que se imprime o PDF, que non ten por que coincidir co da interface (este cámbiase arriba á esquerda). A **Cor da cabeceira**, en formato R,G,B de 0 a 255, é o fondo sobre o que aparece o nome de cada alumno.

## Definir os criterios

Engade tantos criterios como precises, cada un cunha descrición e a súa puntuación máxima. Cos botóns podes engadir ou eliminar filas, e arrastrándoas pola esquerda cámbiaslles a orde. A puntuación total actualízase soa a medida que editas.

## Engadir o alumnado

Podes escribir os nomes a man ou importalos dun ficheiro. RubriPDF recoñece tres orixes e detecta soa cal é:

- a lista da **Secretaría Virtual** (.xls),
- a exportación de participantes de **Moodle** (.xlsx),
- calquera **lista simple** (un .txt ou un CSV dunha columna, cun nome por liña).

Se algo non encaixa —columnas que houbo que deducir, nomes repetidos ou un ficheiro con varias columnas— avísache no momento. Os nomes gárdanse exactamente como veñen, sen retocalos, para que coincidan cos doutros sistemas. Tamén podes arrastralos para ordenalos.

## Opcións de saída

Antes de xerar, podes engadir páxinas extra de notas por alumno (follas en branco adicionais para observacións) e activar **«Guiar as observacións coa rúbrica»**, que pre-enche o cadro de observacións de cada alumno cos criterios numerados, para comentar punto por punto.

## Xerar o PDF

Ao premer **«Xerar PDF»** obtés un documento cunha folla por alumno. Cada folla leva a táboa de criterios, o campo da nota final, unha marca de «Non presentado» e un espazo para observacións, todo en campos de formulario que se cobren directamente no ordenador (comprobado en Firefox e Chrome).

## Corrixir e extraer as notas

Corrixe o PDF nun lector de PDF, marcando os criterios e escribindo as notas. Cando remates, vólveo cargar na sección de extracción e descarga o CSV coas notas.

Durante a extracción faise unha comprobación de calidade que che avisa de posibles erros: criterios sen puntuar, notas que non son números, sumas que non cadran, valores por riba do máximo ou alumnos marcados como «Non presentado» que aínda así teñen notas. Se deixaches a nota final en branco pero puntuaches os criterios, complétase soa coa suma.

O separador decimal e o do CSV adáptanse ao idioma (coma e «;» en galego, español e portugués; punto e «,» en inglés). Se marcas **«CSV detallado»**, o ficheiro inclúe ademais unha columna por cada criterio.

## Gardar e reutilizar a configuración

Cos botóns de gardar e cargar podes exportar toda a configuración —materia, criterios e opcións— a un ficheiro JSON e recuperala cando queiras, por exemplo para outra proba da mesma materia. Ademais, o traballo en curso consérvase no navegador aínda que peches ou recargues a páxina.

## Privacidade

RubriPDF funciona por completo no teu ordenador: nin os nomes do alumnado nin as notas se envían a ningún servidor externo.
