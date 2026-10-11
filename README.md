# RubriPDF

Xera follas de avaliación en PDF que é posíbel encher a partir dunha rúbrica de corrección e unha lista de estudantes, permitindo despois extraer as cualificacións de volta a un CSV. Trátase pois dunha aplicación local pensada para axilizar a corrección de exames e prácticas.

A interface está dispoñible en galego, castelán, inglés e portugués, e a aplicación é completamente autocontida (non precisa internet unha vez instalada).

![Interface de RubriPDF](docs/interface.png)

## Funcionalidades

As principais funcionalidades de RubriPDF son:

- **Follas de avaliación con rúbrica analítica** — unha sección por estudante cunha táboa de niveis de logro por criterio (por exemplo: Insuficiente → Escaso → Suficiente → Notable → Excelente), un campo de cualificación final, unha caixa de *non presentado* (NP) e unha zona de observacións. Son campos do documento PDF que se poden cubrir con visores de PDF compatíbeis con formularios. Os puntos poden derivarse opcionalmente do nivel elixido (unha fracción do máximo do criterio), de modo que a nota queda ancorada a un nivel de desempeño descrito e non a un simple número.
- **Páxina de cuberta** co nome da materia como título e un índice de estudantes.
- **Notas guiadas pola rúbrica** — a primeira caixa de observacións pode pre-encherse cos puntos numerados da rúbrica para estruturar os comentarios por ítem (opcional).
- **Extracción de cualificacións** — le un PDF cuberto e descarga `grades.csv`, con comprobacións de calidade que avisan de:
  - criterios que quedaron sen puntuar,
  - unha cualificación final baleira ou que non é un número,
  - unha cualificación final que non coincide coa suma dos criterios,
  - un ítem puntuado por riba do seu máximo,
  - un estudante marcado como *non presentado* que aínda así ten cualificacións.
  Unha cualificación final en branco énchese automaticamente coa suma exacta dos criterios, e a exportación está protexida contra a inxección de fórmulas/CSV.
- **Importación de estudantes** — a aplicación detecta automaticamente o formato ao subir o ficheiro e indica cantos nomes foron incorporados. Os formatos admitidos son:
  - unha exportación de participantes desde **Moodle** (`.xlsx`): as columnas separadas de *nome* e *apelidos* reconstrúense como `Apelidos, Nome`. Neste caso é necesario empregar en Moodle a exportación `.xlsx`, non `.csv`.
  - unha lista procedente da **"Secretaría Virtual" da USC** (`.xls`): os nomes impórtanse tal e como están no ficheiro orixinal.
  - unha **lista simple**: un `.txt` ou un `.csv` cunha soa columna, un nome por liña.

- A configuración almacénase en formato JSON, de maneira que se poida cargar noutro momento.

## Descargar e executar (sen Python)

Hai executables preparados para seren usados en **Windows** e **Linux** anexados a cada
[*release*](../../releases) — sen Python e sen instalación. Descarga o do teu
sistema e logo:

- **Windows** — Executa `RubriPDF-windows.exe`. SmartScreen pode avisar
  dun "editor descoñecido" (o binario non está asinado), polo que é necesario
  escoller *Máis información → Executar de todos os xeitos*.
- **Linux** — faino executable e lánzao:

  ```bash
  chmod +x RubriPDF-linux
  ./RubriPDF-linux
  ```

A aplicación ábrese nun navegador en <http://localhost:5000> e unha pequena
xanela de consola mantena en marcha.

Cada binario conta co seu correspondente `.sha256` que permite verificalo antes de executalo:

```bash
sha256sum -c RubriPDF-linux.sha256
```

> Os executables **non están asinados**, así que o sistema mostra un aviso unha
> soa vez. Isto non afecta ao funcionamento da aplicación. Compilar dende as
> fontes (máis abaixo) evítao por completo.

## Executar dende as fontes

Require **Python 3.8+**.

**Linux / macOS**

```bash
./run.sh
```

**Windows**

```bat
run.bat
```

O lanzador crea unha contorna virtual local a primeira vez, instala as dependencias
e abre a aplicación en <http://localhost:5000>. Se xa hai unha contorna virtual
activa, esta é reutilizada.

Para executalo a man no seu lugar:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

## Uso

1. Encher os campos de materia, curso académico e título da proba.
2. Engadir os criterios de corrección e os seus puntos máximos.
3. Engadir estudantes (ben escritos a man ou importados desde CSV/folla de cálculo).
4. Xerar o PDF e cualificar a cada estudante nun visor de PDF.
5. Desde a aplicación, importar o PDF cuberto en *Extraer cualificacións* para descargar `grades.csv`, revisando os avisos que aparezan.

En `example-config.json` inclúese unha configuración inicial como mostra.

## Normalización da lista de nomes importados

Os nomes dos estudantes poden vir de varias fontes, e cada unha ten o seu propio formato. Porén, a aplicación impórtaos sen ningún tipo de normalización para manter a posibilidade de os usar como chave de emparellamento coa lista orixinal.

No caso de que se desexe unha lista de nomes consistente, é posíbel normalizalos antes de importalos. Para iso, RubriPDF inclúe a ferramenta `normalize_names.py` que permite xerar unha versión limpa da lista de estudantes.

```bash
python tools/normalize_names.py "Listaxe de alumnos.xls" --identical listaxe-normalizada.xls
```

Este comando xera un novo ficheiro `listaxe-normalizada.xls` co mesmo formato que o orixinal pero cos nomes normalizados. Este ficheiro está preparado para ser importado directamente en RubriPDF.

Tamén é posíbel xerar unha táboa plana de 5 columnas en formato CSV ou XLS/XLSX, onde o formato vén dado pola extensión escollida para o ficheiro de saída (`.csv`, `.xls` ou `.xlsx`).

```bash
python tools/normalize_names.py "Listaxe de alumnos.xls" --flat listaxe.csv
```

Esta opción serve para dispor dunha versión limpa da lista de alumnos (`listaxe.csv` no caso do exemplo) que se poida empregar noutros contextos, e cos mesmos criterios de normalización empregados en RubriPDF.

Finalmente, a opción `--dry-run` permite previsualizar o resultado da normalización sen sobrescribir o ficheiro orixinal nin xerar ningún novo ficheiro.

```bash
python tools/normalize_names.py "Listaxe de alumnos.xls" --dry-run
```

## Licenza

RubriPDF é software libre, licenciado baixo a **Licenza Pública Xeral de GNU
v3.0 ou posterior** (GPL-3.0-or-later). Consulta [LICENSE](LICENSE) para o texto
completo.
