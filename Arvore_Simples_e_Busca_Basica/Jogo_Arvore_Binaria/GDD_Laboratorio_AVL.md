# Game Design Document Briefing — Laboratório AVL

**Disciplina:** Estruturas de Dados II • Ciência da Computação
**Tema:** Design de Jogos Educativos sobre Árvores Avançadas por meio da Engenharia Reversa e Reuso de Modelos

## 1. Identificação do Grupo

**Integrantes do Grupo:** _(preencher)_
**Data:** ____ / ____ / 2026  **Turma:** Ciência da Computação

---

## 4.1 Diagnóstico do Modelo Reutilizado

**Nome do Jogo/Ferramenta Base:** *graphical-binary-trees* (jrenner), visualizador de Árvore Binária de Busca em Python/pygame
— <https://github.com/jrenner/graphical-binary-trees>

**Como o modelo original funciona (análise do código-fonte):** gera uma ABB aleatória de 100 nós, desenha a árvore na tela e permite apenas navegar pelos nós com as setas (filho esquerdo, filho direito, pai), mover a câmera com as teclas WASD e gerar outra árvore aleatória com a tecla R. Mostra somente o valor e a profundidade do nó selecionado.

**Limitações didáticas e técnicas identificadas:**

1. **Usuário passivo.** Ele só observa e navega; não toma nenhuma decisão nem executa operações sobre a árvore.
2. **Não há inserção pelo usuário.** A árvore só muda quando é descartada e regenerada aleatoriamente (tecla R), então não se vê o efeito de uma inserção específica.
3. **Sem balanceamento.** É uma ABB comum: não calcula Fator de Balanceamento, não tem rotações e não há nenhuma noção de árvore "boa" ou "ruim". A ordem de inserção pode degenerar a estrutura em lista (O(n)) sem qualquer consequência.
4. **Sem objetivo, feedback ou derrota.** Nada indica se a árvore está em um bom ou mau estado, nem que o pior caso da busca foi atingido.
5. **Navegação pouco prática.** A câmera só se move com teclado, não há zoom, e a posição dos nós é calculada uma única vez (layout não reage a mudanças de estrutura).
6. **Código em Python 2**, incompatível com as versões atuais sem adaptação.

## 4.2 Seleção da Estrutura de ED II para o Upgrade

- [x] **Árvore AVL:** Foco no Fator de Balanceamento FB em {-1, 0, 1} e execução de Rotações Simples/Duplas.
- [ ] Árvore Rubro-Negra
- [ ] Árvore B / B+

## 4.3 Mapeamento de Conceitos em Mecânicas de Gameplay

| Conceito Teórico de ED II | Elemento / Mecânica Correspondente no Jogo |
| --- | --- |
| **Nó da Árvore / Chave** | Cada chave é um círculo numerado. No modo jogo, as chaves chegam por uma **fila** ("próxima" em destaque) e são inseridas pelas regras da ABB (menor à esquerda, maior à direita, sem duplicados). |
| **Altura da Árvore (h)** | Mostrada no painel junto com o **custo da busca no pior caso (h + 1 comparações)** e o valor ideal (⌈log₂(n+1)⌉). No modo jogo existe um **teto do cenário** (linha tracejada): a altura máxima possível de uma AVL com *n* nós, mais 1 nível de tolerância. Convenção da apostila: folha = 0, árvore vazia = -1. |
| **Fator de Balanceamento** | Número acima de cada nó, **FB = altura(esq) − altura(dir)**. Verde quando \|FB\| ≤ 1; nó vermelho pulsante quando \|FB\| ≥ 2. Há também a **barra de Estabilidade** (3 pontos) do jogador. |
| **Operação de Correção (Rotação)** | Habilidades do jogador no nó selecionado: **A** = rotação à esquerda, **D** = rotação à direita. A rotação **simples** usa 1 habilidade e a **dupla** (casos Esquerda-Direita e Direita-Esquerda) usa 2 em sequência. A escolha do nó e do tipo de rotação é do jogador. |

**Regra de decisão ensinada (convenção FB = h(esq) − h(dir)):**

| Nó crítico | Filho | Caso | Correção |
| --- | --- | --- | --- |
| FB = +2 | filho esquerdo com FB ≥ 0 | Esquerda-Esquerda | rotação simples à direita no nó |
| FB = +2 | filho esquerdo com FB = −1 | Esquerda-Direita | rotação à esquerda no filho, depois à direita no nó |
| FB = −2 | filho direito com FB ≤ 0 | Direita-Direita | rotação simples à esquerda no nó |
| FB = −2 | filho direito com FB = +1 | Direita-Esquerda | rotação à direita no filho, depois à esquerda no nó |

## 4.4 Regras do Core Loop e Condições do Jogo

**Core Loop (o que o jogador faz repetidamente):**

1. Recebe a próxima chave *k* da fila e a insere na árvore (**Enter**); a inserção de ABB é feita pelo jogo.
2. A árvore se redistribui automaticamente na tela e o FB de todos os nós é recalculado.
3. O jogador avalia o FB e localiza o **nó crítico** (o mais fundo com \|FB\| = 2).
4. Classifica o caso (EE, DD, ED ou DE) e escolhe a(s) rotação(ões) (**A** / **D**) no nó certo.
5. Recebe **feedback imediato** ("Correto!", "Piorou", "falta a 2ª rotação") e repete até a árvore ficar válida.
6. Só então insere a próxima chave.

**Condição de Vitória:** inserir toda a fila (15 chaves) e terminar com **todos os nós com \|FB\| ≤ 1** (AVL válida), com estabilidade maior que zero. Menos rotações = melhor pontuação.

**Condição de Derrota (falha associada à degradação algorítmica):**

- **Estabilidade zero:** inserir uma nova chave com a árvore ainda desbalanceada custa 1 dos 3 pontos de estabilidade; ao zerar, a árvore desmorona.
- **Teto ultrapassado:** se a altura da árvore passar do teto (altura máxima de uma AVL com *n* nós + 1), a estrutura virou praticamente uma **lista encadeada** e a busca degradou para **O(n)**: o cenário desmorona. (A tolerância de +1 existe porque uma única inserção em uma AVL válida pode elevar a altura em 1 nível antes da correção.)

**Modos disponíveis no protótipo:**

- **Modo Livre** (evolução direta do modelo base): árvore aleatória (tecla R), campo de texto para inserir qualquer número, rotações manuais e dicas. Existe também a opção **AVL automática**, desligada por padrão, que serve só como *demonstração* para comparar o resultado correto; ela não é usada no jogo para não tornar o jogador passivo.
- **Modo Jogo:** fila de chaves, estabilidade, teto do cenário, vitória e derrota.

## Melhorias de usabilidade (além da mecânica)

- **Mouse:** arrastar para mover a tela, *scroll* para zoom (centrado no cursor) e clique para selecionar nós, em vez de WASD.
- **Campo de texto no topo** para inserir números.
- **Distribuição automática:** os nós se reposicionam sozinhos, com animação, a cada inserção ou rotação (posição horizontal pela ordem simétrica e vertical pela profundidade), sem sobreposição.
- **Dica (H)** que indica o caso e a rotação correta, e **enquadrar (F)** para ver a árvore inteira.

## 5. Checklist de Autoavaliação do Grupo

- [x] Identificamos e citamos o jogo/modelo base existente (*graphical-binary-trees*, jrenner).
- [x] O upgrade exige a aplicação prática de conceitos de ED II (AVL: FB, rotações simples e duplas).
- [x] As propriedades algorítmicas (FB) estão traduzidas em mecânicas ativas de jogo (nó em alerta, rotação pelo jogador, estabilidade).
- [x] A condição de derrota está associada ao pior caso de complexidade (árvore degenerando em lista, O(n)).
- [ ] O grupo está preparado para realizar a defesa do projeto em um Pitch de 3 minutos.

## Roteiro do Pitch (3 minutos)

1. **Problema (40 s):** o *graphical-binary-trees* mostra uma ABB, mas o aluno só assiste; não há inserção, balanceamento nem consequência para uma árvore ruim.
2. **Como a AVL aparece (60 s):** FB em cada nó, vermelho quando chega a ±2, e o jogador aplica as rotações; explicar os 4 casos.
3. **Demonstração (60 s):** inserir 10, 20, 30 em ordem, mostrar o caso Direita-Direita e corrigir com uma rotação à esquerda; depois mostrar a derrota ao ignorar o desbalanceamento.
4. **Aprendizado (20 s):** o jogador enxerga por que a árvore precisa ser balanceada: O(log n) contra O(n).

## Como executar o protótipo

```
python btree_avl.py
```

Requisitos: Python 3 e `pygame` (`pip install pygame`).
**Mouse:** arrastar = mover • scroll = zoom • clique = selecionar. **Teclado:** setas = navegar • A/D = rotação à esquerda/direita • Enter = inserir • H = dica • F = enquadrar • R = aleatória/reiniciar • C = limpar • G = modo jogo/livre • T = AVL automática • Q/Esc = sair.

## Créditos e alterações sobre o modelo base

**Autor do modelo base:** jrenner — <https://github.com/jrenner/graphical-binary-trees>.
A ideia original (visualizar uma ABB em pygame e navegar por seus nós) e o código do arquivo `btree.py` original são dele; este projeto reaproveita essa proposta e a estende.

**Arquivos deste repositório:**

| Arquivo | O que é |
| --- | --- |
| `btree.py` | Código **original do jrenner**, apenas **portado de Python 2 para Python 3** (sem mudar o comportamento). Cada alteração está marcada com `# CORRIGIDO`. |
| `btree_avl.py` | **Upgrade do grupo (Laboratório AVL).** É uma nova implementação que parte da proposta do original e acrescenta a AVL e o modo jogo. |
| `GDD_Laboratorio_AVL.md` | Este documento. |

**Ajustes feitos no `btree.py` para rodar em Python 3:**

- `print "texto"` trocado por `print("texto")` (em Python 3 o `print` é função).
- Divisões `/` trocadas por `//` (a raiz valia 50.0, um decimal, em vez de 50).
- Bug corrigido: o valor 0 era tratado como "nó vazio" (`if not leaf.cargo` passou a ser `if leaf.cargo is None`), o que podia sobrescrever o nó de valor 0.
- O valor da raiz (50) deixou de entrar no sorteio, eliminando o aviso de "duplicate cargo".
- Programa principal colocado dentro de `if __name__ == "__main__":`.

**O que o upgrade (`btree_avl.py`) mantém do original:**

- ABB desenhada na tela, com a regra "menor à esquerda, maior à direita" e sem duplicados.
- Navegação pelas setas (filho esquerdo, filho direito e pai) e nó selecionado com destaque.
- Informações do nó selecionado (valor e profundidade).
- Tecla **R** para gerar uma árvore aleatória.

**O que foi alterado em relação ao original:**

| Original (jrenner) | Upgrade |
| --- | --- |
| Árvore aleatória de 100 nós | 40 nós por padrão (constante `NUM_OF_NODES`) |
| Mover a câmera com as teclas WASD | Arrastar com o mouse e zoom com o scroll |
| Posição dos nós calculada uma única vez, ao criar a árvore | Distribuição automática: recalculada a cada inserção e rotação, com animação |
| Nós desenhados como caixas | Nós como círculos, com o Fator de Balanceamento acima de cada um |

**O que foi acrescentado (não existia no original):**

- Campo de texto no topo para inserir números.
- Cálculo e exibição do Fator de Balanceamento e da altura de cada nó.
- Rotações simples e duplas executadas pelo jogador (teclas A e D).
- Dica (caso EE, DD, ED ou DE) e feedback após cada rotação.
- Custo da busca no pior caso (h + 1) comparado ao ideal.
- **Modo Jogo:** fila de chaves, estabilidade, teto de altura, vitória e derrota.
- **AVL automática** (opcional, desligada por padrão) apenas para demonstração.

## Referências

- JRENNER. *graphical-binary-trees*. GitHub. <https://github.com/jrenner/graphical-binary-trees> (modelo base reutilizado).
- CELES, W.; RANGEL, J. L. *Árvores* (cap. 13). Estruturas de Dados — PUC-Rio (definição de altura, percursos).
- Material das aulas de Estruturas de Dados II (plano de aula de 11/09 e aula de 14/09).
