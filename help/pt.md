## O que é o RubriPDF

O RubriPDF ajuda-te a avaliar com rúbricas de princípio a fim. A partir de uma rúbrica e da lista de alunado gera, para cada estudante, uma folha de avaliação em PDF que corriges comodamente no computador; ao terminar, a aplicação recolhe todas as notas num único ficheiro.

As secções desta ajuda seguem a ordem habitual de trabalho: configurar o documento, definir os critérios, adicionar o alunado, gerar o PDF, corrigir e, por último, extrair as notas.

## Configurar o documento

Nesta primeira parte defines o cabeçalho das folhas. A **Disciplina** é o título grande da capa, e o **Ano letivo** e o **Título da prova** formam o subtítulo.

Com o **Idioma** escolhemos a língua em que se imprime o PDF, que não tem de coincidir com a da interface (esta muda-se no canto superior esquerdo). A **Cor do cabeçalho**, em formato R,G,B de 0 a 255, é o fundo sobre o qual aparece o nome de cada aluno.

## Definir os critérios

Adiciona tantos critérios quantos precises, cada um com uma descrição e a sua pontuação máxima. Com os botões podes adicionar ou remover linhas, e arrastando-as pela esquerda mudas-lhes a ordem. A pontuação total atualiza-se sozinha à medida que editas.

## Adicionar o alunado

Podes escrever os nomes à mão ou importá-los de um ficheiro. O RubriPDF reconhece três origens e deteta sozinho qual é:

- a lista da **Secretaría Virtual** (.xls),
- a exportação de participantes do **Moodle** (.xlsx),
- qualquer **lista simples** (um .txt ou um CSV de uma coluna, com um nome por linha).

Se algo não encaixa —colunas que teve de deduzir, nomes repetidos ou um ficheiro com várias colunas— avisa-te no momento. Os nomes são guardados exatamente como vêm, sem os retocar, para que coincidam com os de outros sistemas. Também podes arrastá-los para os ordenar.

## Opções de saída

Antes de gerar, podes adicionar páginas extra de notas por aluno (folhas em branco adicionais para observações) e ativar **«Guiar as observações com a rúbrica»**, que preenche a caixa de observações de cada aluno com os critérios numerados, para comentar ponto por ponto.

## Gerar o PDF

Ao carregar em **«Gerar PDF»** obténs um documento com uma folha por aluno. Cada folha tem a tabela de critérios, o campo da nota final, uma marca de «Não compareceu» e um espaço para observações, tudo em campos de formulário preenchidos diretamente no computador (testado no Firefox e no Chrome).

## Corrigir e extrair as notas

Corrige o PDF num leitor de PDF, marcando os critérios e escrevendo as notas. Quando terminares, carrega-o de novo na secção de extração e transfere o CSV com as notas.

Durante a extração é feita uma verificação de qualidade que te avisa de possíveis erros: critérios sem pontuação, notas que não são números, somas que não batem, valores acima do máximo ou alunos marcados como «Não compareceu» que mesmo assim têm notas. Se deixaste a nota final em branco mas pontuaste os critérios, é completada sozinha com a soma.

O separador decimal e o do CSV adaptam-se ao idioma (vírgula e «;» em galego, espanhol e português; ponto e «,» em inglês). Se marcares **«CSV detalhado»**, o ficheiro inclui ainda uma coluna por cada critério.

## Guardar e reutilizar a configuração

Com os botões de guardar e carregar podes exportar toda a configuração —disciplina, critérios e opções— para um ficheiro JSON e recuperá-la quando quiseres, por exemplo para outra prova da mesma disciplina. Além disso, o trabalho em curso é mantido no navegador mesmo que feches ou recarregues a página.

## Privacidade

O RubriPDF funciona por completo no teu computador: nem os nomes do alunado nem as notas são enviados a nenhum servidor externo.
