# -*- coding: utf-8 -*-
"""
LABORATÓRIO AVL  -  upgrade do visualizador "graphical-binary-trees" (jrenner)

Modelo base (reuso): https://github.com/jrenner/graphical-binary-trees
  - O original só mostrava uma ABB aleatória: o usuário apenas navegava (passivo),
    não havia inserção, balanceamento, feedback, objetivo nem derrota.

O que este upgrade MANTÉM do original:
  - a árvore binária de busca desenhada na tela, navegação pelas setas,
    tecla R para gerar uma árvore aleatória e as informações do nó selecionado.

O que este upgrade ACRESCENTA (conceitos de ED II - Árvore AVL):
  1. Mouse: arrastar = mover a tela, scroll = zoom, clique = selecionar nó.
  2. Campo de texto no topo para inserir números (Enter ou botão "Inserir").
  3. Distribuição automática: os nós se reposicionam sozinhos (com animação)
     a cada inserção ou rotação.
  4. Fator de Balanceamento (FB) em cada nó:  FB = altura(esq) - altura(dir).
     Numa AVL todo nó deve ter FB em {-1, 0, 1}. Nós com |FB| >= 2 brilham em vermelho.
  5. Rotações feitas PELO JOGADOR (A = esquerda, D = direita) - aprendizagem ativa.
  6. MODO JOGO: fila de chaves, estabilidade, teto de altura, vitória e derrota
     ligadas ao pior caso O(n) (árvore degenerando em lista).
  7. Dica (H) que diz qual é o caso (EE, DD, ED, DE) e qual rotação resolve.
  8. "AVL automática" (T), só como DEMONSTRAÇÃO no modo livre: mostra o resultado
     correto para comparar com o que você fez.

Convenções (iguais às da apostila): altura de folha = 0, altura de árvore vazia = -1.

Teclas e mouse: veja a linha de ajuda na parte de baixo da janela.
"""
import sys
import math
import random
import pygame

sys.setrecursionlimit(5000)

# ----------------------------------------------------------------------------
# CONFIGURAÇÕES (pode mudar à vontade)
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 800
TOP_H = 72                 # altura da barra superior
GAME_STRIP_H = 58          # faixa do modo jogo (fila + estabilidade)
BOTTOM_H = 132             # painel de informações embaixo
NUM_OF_NODES = 40          # tamanho da árvore aleatória (tecla R). O original usava 100.
MAX_KEY = 99               # valores aleatórios vão de 0 até MAX_KEY
MAX_NODES = 250            # limite de nós (evita travar)
X_SPACING = 52             # distância horizontal entre nós (no zoom 1.0)
Y_STEP = 90                # distância vertical entre níveis
NODE_R = 20                # raio do nó
MIN_ZOOM, MAX_ZOOM = 0.12, 3.0
START_STABILITY = 3        # pontos de estabilidade no modo jogo

# Sequência inicial da fila do modo jogo. Com jogo correto ela passa pelos 4 casos
# de rotação (DD, EE, ED, DE). Depois vêm chaves aleatórias.
SCRIPTED_QUEUE = [20, 35, 90, 80, 10, 75, 55, 45, 65, 60]
RANDOM_TAIL = 5

# Cores
C_BG = (12, 14, 20)
C_BAR = (24, 27, 38)
C_TEXT = (235, 235, 240)
C_DIM = (150, 155, 170)
C_EDGE = (70, 200, 110)
C_NODE = (24, 60, 120)
C_NODE_BORDER = (70, 130, 255)
C_CRIT_FILL = (120, 25, 35)
C_OK = (90, 220, 120)
C_WARN = (255, 200, 60)
C_BAD = (255, 80, 80)
C_SEL = (255, 230, 80)
C_BTN = (45, 52, 75)
C_BTN_ON = (40, 110, 70)


# ----------------------------------------------------------------------------
# TEXTO (com cache para não renderizar toda hora)
# ----------------------------------------------------------------------------
_fonts = {}
_texts = {}


def get_font(size):
    size = max(6, int(size))
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont("dejavusans,verdana,arial", size)
    return _fonts[size]


def render(text, size, color):
    key = (text, int(size), color)
    surf = _texts.get(key)
    if surf is None:
        if len(_texts) > 3000:
            _texts.clear()
        surf = get_font(size).render(text, True, color)
        _texts[key] = surf
    return surf


def blit_text(surface, text, size, color, pos, anchor="topleft"):
    surf = render(text, size, color)
    rect = surf.get_rect(**{anchor: pos})
    surface.blit(surf, rect)
    return rect


def wrap_text(text, size, max_width):
    """Quebra o texto em linhas que caibam na largura dada."""
    words = text.split(" ")
    lines, current = [], ""
    for w in words:
        test = (current + " " + w).strip()
        if get_font(size).size(test)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


# ----------------------------------------------------------------------------
# ESTRUTURA DE DADOS: nó e árvore
# ----------------------------------------------------------------------------
class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.parent = None
        self.height = 0      # altura do nó (folha = 0)
        self.fb = 0          # fator de balanceamento = altura(esq) - altura(dir)
        self.depth = 0       # profundidade (raiz = 0)
        self.tx = 0.0        # posição-alvo (mundo) calculada pela distribuição automática
        self.ty = 0.0
        self.x = 0.0         # posição atual (animada)
        self.y = 0.0
        self.placed = False


class Tree:
    def __init__(self):
        self.root = None
        self.count = 0
        self.height = -1     # altura da árvore vazia = -1 (apostila)

    # ---- consultas ----
    def nodes(self):
        out = []
        stack = [self.root] if self.root else []
        while stack:
            n = stack.pop()
            out.append(n)
            if n.left:
                stack.append(n.left)
            if n.right:
                stack.append(n.right)
        return out

    def critical_nodes(self):
        """Nós com |FB| >= 2, do mais fundo para o mais raso."""
        crit = [n for n in self.nodes() if abs(n.fb) >= 2]
        crit.sort(key=lambda n: -n.depth)
        return crit

    # ---- cálculo de alturas, FB e posições (distribuição automática) ----
    def _measure(self, n, depth):
        if n is None:
            return -1
        n.depth = depth
        hl = self._measure(n.left, depth + 1)
        hr = self._measure(n.right, depth + 1)
        n.height = 1 + max(hl, hr)
        n.fb = hl - hr
        return n.height

    def _inorder(self, n, out):
        if n is None:
            return
        self._inorder(n.left, out)
        out.append(n)
        self._inorder(n.right, out)

    def recompute(self):
        """Recalcula altura/FB e a posição-alvo de todos os nós.
        Distribuição automática: x = posição na ordem simétrica (esq, raiz, dir),
        y = profundidade. Assim nenhum nó sobrepõe outro."""
        self.height = self._measure(self.root, 0)
        order = []
        self._inorder(self.root, order)
        for i, n in enumerate(order):
            n.tx = i * X_SPACING
            n.ty = n.depth * Y_STEP
        if self.root:
            off = self.root.tx            # a raiz fica sempre em x = 0
            for n in order:
                n.tx -= off
        for n in order:
            if not n.placed:              # nó novo nasce na posição do pai e "desliza"
                if n.parent:
                    n.x, n.y = n.parent.x, n.parent.y
                else:
                    n.x, n.y = n.tx, n.ty
                n.placed = True

    def snap(self):
        """Coloca todos os nós direto na posição-alvo (sem animação)."""
        for n in self.nodes():
            n.x, n.y = n.tx, n.ty
            n.placed = True

    # ---- operações ----
    def insert(self, key):
        """Inserção de ABB (menor à esquerda, maior à direita, sem duplicados).
        Devolve o nó novo, ou None se a chave já existe."""
        if self.root is None:
            self.root = Node(key)
            self.count = 1
            self.recompute()
            return self.root
        cur = self.root
        while True:
            if key == cur.key:
                return None
            if key < cur.key:
                if cur.left is None:
                    new = Node(key)
                    new.parent = cur
                    cur.left = new
                    break
                cur = cur.left
            else:
                if cur.right is None:
                    new = Node(key)
                    new.parent = cur
                    cur.right = new
                    break
                cur = cur.right
        self.count += 1
        self.recompute()
        return new

    def rotate_right(self, node):
        """Rotação simples à direita: o filho ESQUERDO sobe. Devolve o novo topo (pivô)."""
        pivot = node.left
        if pivot is None:
            return None
        node.left = pivot.right
        if pivot.right:
            pivot.right.parent = node
        pivot.parent = node.parent
        if node.parent is None:
            self.root = pivot
        elif node.parent.left is node:
            node.parent.left = pivot
        else:
            node.parent.right = pivot
        pivot.right = node
        node.parent = pivot
        self.recompute()
        return pivot

    def rotate_left(self, node):
        """Rotação simples à esquerda: o filho DIREITO sobe. Devolve o novo topo (pivô)."""
        pivot = node.right
        if pivot is None:
            return None
        node.right = pivot.left
        if pivot.left:
            pivot.left.parent = node
        pivot.parent = node.parent
        if node.parent is None:
            self.root = pivot
        elif node.parent.left is node:
            node.parent.left = pivot
        else:
            node.parent.right = pivot
        pivot.left = node
        node.parent = pivot
        self.recompute()
        return pivot


# ----------------------------------------------------------------------------
# REGRAS DA AVL
# ----------------------------------------------------------------------------
def diagnose(node):
    """Para um nó com |FB| >= 2, devolve (nome do caso, passos).
    Cada passo é ("L" ou "R", nó) = rotação à esquerda/direita naquele nó.
    Convenção: FB = altura(esq) - altura(dir)."""
    if node.fb >= 2:                       # pesado à esquerda
        c = node.left
        if c.fb >= 0:
            return "Esquerda-Esquerda", [("R", node)]
        return "Esquerda-Direita", [("L", c), ("R", node)]
    if node.fb <= -2:                      # pesado à direita
        c = node.right
        if c.fb <= 0:
            return "Direita-Direita", [("L", node)]
        return "Direita-Esquerda", [("R", c), ("L", node)]
    return None


def fb_str(fb):
    """FB com sinal (+1, -1, +2...) e '0' sem sinal."""
    return "%+d" % fb if fb != 0 else "0"


def describe_steps(steps):
    parts = []
    for d, n in steps:
        lado = "esquerda (tecla A)" if d == "L" else "direita (tecla D)"
        parts.append("rotação à %s no nó %d" % (lado, n.key))
    return " e depois ".join(parts)


def max_avl_height(n):
    """Maior altura possível de uma AVL com n nós.
    Menor número de nós para altura h: N(h) = N(h-1) + N(h-2) + 1 (N(0)=1, N(1)=2...)."""
    if n <= 0:
        return -1
    a, b, h = 0, 1, 0          # a = N(h-1), b = N(h)
    while True:
        nxt = b + a + 1
        if nxt > n:
            return h
        a, b, h = b, nxt, h + 1


def ideal_comparisons(n):
    """Comparações no pior caso de uma árvore perfeitamente equilibrada: ceil(log2(n+1))."""
    return max(1, math.ceil(math.log2(n + 1))) if n > 0 else 0


class Game:
    """Estado do MODO JOGO."""
    def __init__(self):
        pool = [k for k in range(1, 100) if k not in SCRIPTED_QUEUE]
        tail = random.sample(pool, RANDOM_TAIL)
        self.queue = list(SCRIPTED_QUEUE) + tail
        self.index = 0
        self.stability = START_STABILITY
        self.result = None          # None, "win" ou "lose"
        self.result_text = ""


class Button:
    def __init__(self, label_fn, action, active_fn=None):
        self.label_fn = label_fn
        self.action = action
        self.active_fn = active_fn
        self.rect = pygame.Rect(0, 0, 0, 0)


# ----------------------------------------------------------------------------
# APLICATIVO
# ----------------------------------------------------------------------------
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Laboratório AVL - upgrade do graphical-binary-trees")
        pygame.key.set_repeat(250, 40)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.tree = Tree()
        self.zoom = 1.0
        self.cam = [WIDTH / 2, TOP_H + 110.0]     # onde o ponto (0,0) do mundo aparece na tela
        self.selected = None
        self.text = ""                            # conteúdo do campo de inserção
        self.mode = "livre"                       # "livre" ou "jogo"
        self.auto_avl = False
        self.hint = False
        self.rotations = 0
        self.game = None
        self.message = ""
        self.msg_color = C_TEXT

        self.dragging = False
        self.drag_moved = False
        self.drag_start = (0, 0)

        self.buttons = [
            Button(lambda: "Inserir (Enter)", self.insert_from_field),
            Button(lambda: "Aleatória (R)" if self.mode == "livre" else "Reiniciar (R)", self.new_random_or_restart),
            Button(lambda: "Limpar (C)", self.clear_tree),
            Button(lambda: "Modo: " + ("Livre" if self.mode == "livre" else "Jogo") + " (G)", self.toggle_mode,
                   lambda: self.mode == "jogo"),
            Button(lambda: "AVL auto: " + ("ON" if self.auto_avl else "OFF") + " (T)", self.toggle_auto,
                   lambda: self.auto_avl),
            Button(lambda: "Dica: " + ("ON" if self.hint else "OFF") + " (H)", self.toggle_hint,
                   lambda: self.hint),
        ]

        self.new_random_tree()

    # ---------------- mensagens ----------------
    def say(self, text, kind="info"):
        self.message = text
        self.msg_color = {"info": C_TEXT, "ok": C_OK, "bad": C_BAD, "warn": C_WARN}[kind]

    # ---------------- câmera (mouse) ----------------
    def w2s(self, wx, wy):
        return (wx * self.zoom + self.cam[0], wy * self.zoom + self.cam[1])

    def s2w(self, sx, sy):
        return ((sx - self.cam[0]) / self.zoom, (sy - self.cam[1]) / self.zoom)

    def zoom_at(self, pos, factor):
        """Zoom centrado no cursor: o ponto do mundo sob o mouse fica parado."""
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom * factor))
        factor = new_zoom / self.zoom
        self.cam[0] = pos[0] - (pos[0] - self.cam[0]) * factor
        self.cam[1] = pos[1] - (pos[1] - self.cam[1]) * factor
        self.zoom = new_zoom

    def fit_view(self):
        """Enquadra a árvore inteira na janela (tecla F)."""
        sw, sh = self.screen.get_size()
        nodes = self.tree.nodes()
        top = TOP_H + (GAME_STRIP_H if self.mode == "jogo" else 0) + 10
        avail_w = sw - 40
        avail_h = sh - top - BOTTOM_H
        if not nodes:
            self.zoom = 1.0
            self.cam = [sw / 2, top + 60.0]
            return
        xs = [n.tx for n in nodes]
        ys = [n.ty for n in nodes]
        w = max(xs) - min(xs) + 4 * NODE_R
        h = max(ys) - min(ys) + 4 * NODE_R
        z = min(avail_w / w, avail_h / h, 1.2)
        z = max(MIN_ZOOM, min(MAX_ZOOM, z))
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        self.zoom = z
        self.cam = [sw / 2 - cx * z, top + avail_h / 2 - cy * z]

    def keep_visible(self, node):
        """Se o nó novo ficou fora da tela, enquadra a árvore."""
        sw, sh = self.screen.get_size()
        sx, sy = self.w2s(node.tx, node.ty)
        top = TOP_H + (GAME_STRIP_H if self.mode == "jogo" else 0)
        if sx < 20 or sx > sw - 20 or sy < top + 10 or sy > sh - BOTTOM_H:
            self.fit_view()

    def node_at(self, pos):
        """Nó sob a posição (x, y) da tela, ou None."""
        best, best_d = None, None
        r = max(9, NODE_R * self.zoom)
        for n in self.tree.nodes():
            sx, sy = self.w2s(n.x, n.y)
            d = math.hypot(sx - pos[0], sy - pos[1])
            if d <= r and (best is None or d < best_d):
                best, best_d = n, d
        return best

    # ---------------- ações ----------------
    def toggle_hint(self):
        self.hint = not self.hint

    def toggle_auto(self):
        if self.mode == "jogo":
            self.say("A AVL automática só existe no modo livre (no jogo, as rotações são suas).", "warn")
            return
        self.auto_avl = not self.auto_avl
        if self.auto_avl:
            steps = self.auto_balance()
            self.say("AVL automática LIGADA (demonstração): a árvore se corrige sozinha. %s" %
                     ("Rotações aplicadas agora: %d." % len(steps) if steps else ""), "info")
        else:
            self.say("AVL automática DESLIGADA: agora as rotações são com você.", "info")

    def auto_balance(self, max_iter=600):
        """Aplica rotações (casos EE, DD, ED, DE) até não haver nó com |FB| >= 2."""
        done = []
        for _ in range(max_iter):
            crit = self.tree.critical_nodes()
            if not crit:
                break
            case = diagnose(crit[0])
            for d, n in case[1]:
                if d == "L":
                    self.tree.rotate_left(n)
                else:
                    self.tree.rotate_right(n)
                done.append((d, n.key))
        return done

    def new_random_or_restart(self):
        if self.mode == "jogo":
            self.start_game()
        else:
            self.new_random_tree()

    def new_random_tree(self):
        """Árvore aleatória, como no programa original (tecla R)."""
        self.mode = "livre"
        self.game = None
        self.tree = Tree()
        self.rotations = 0
        for k in random.sample(range(MAX_KEY + 1), min(NUM_OF_NODES, MAX_KEY + 1)):
            self.tree.insert(k)
        if self.auto_avl:
            self.auto_balance()
        self.tree.snap()
        self.selected = self.tree.root
        self.fit_view()
        self.say("Árvore aleatória criada. Digite um número e aperte Enter para inserir.", "info")

    def clear_tree(self):
        if self.mode == "jogo":
            self.start_game()
            return
        self.tree = Tree()
        self.selected = None
        self.rotations = 0
        self.fit_view()
        self.say("Árvore vazia. Insira números com o campo do topo.", "info")

    def toggle_mode(self):
        if self.mode == "livre":
            self.start_game()
        else:
            self.new_random_tree()

    def start_game(self):
        self.mode = "jogo"
        self.auto_avl = False
        self.game = Game()
        self.tree = Tree()
        self.selected = None
        self.rotations = 0
        self.text = ""
        self.fit_view()
        self.say("MODO JOGO: aperte Enter para inserir a próxima chave da fila. Se algum nó chegar a "
                 "|FB| = 2, corrija com rotações ANTES da próxima inserção. Sobreviva à fila inteira!", "info")

    # ---------------- inserção ----------------
    def insert_from_field(self):
        if self.mode == "jogo":
            self.game_insert_next()
            return
        if not self.text:
            self.say("Digite um número (0 a 999) no campo do topo e aperte Enter.", "warn")
            return
        key = int(self.text)
        if self.tree.count >= MAX_NODES:
            self.say("Limite de %d nós atingido." % MAX_NODES, "warn")
            return
        node = self.tree.insert(key)
        if node is None:
            self.say("O valor %d já está na árvore (a ABB da aula não aceita duplicados)." % key, "warn")
            return
        self.text = ""
        self.selected = node
        msg = "Inseriu %d." % key
        if self.auto_avl:
            steps = self.auto_balance()
            if steps:
                msg += " AVL automática aplicou %d rotação(ões)." % len(steps)
        crit = self.tree.critical_nodes()
        if crit:
            msg += " Atenção: %d nó(s) com |FB| >= 2 (em vermelho). Use A/D para rotacionar." % len(crit)
            self.say(msg, "warn")
        else:
            self.say(msg + " Todos os nós com |FB| <= 1.", "ok")
        self.keep_visible(node)

    def game_insert_next(self):
        g = self.game
        if g is None or g.result:
            return
        if g.index >= len(g.queue):
            self.say("A fila acabou. Deixe todos os nós com |FB| <= 1 para vencer.", "warn")
            return
        warn = ""
        if self.tree.critical_nodes():
            g.stability -= 1
            warn = "Você inseriu com a árvore desbalanceada! Estabilidade -1. "
        key = g.queue[g.index]
        g.index += 1
        node = self.tree.insert(key)
        self.selected = node
        crit = self.tree.critical_nodes()
        if crit:
            msg = warn + "Inseriu %d. %d nó(s) desbalanceado(s): corrija com rotações." % (key, len(crit))
            self.say(msg, "bad" if warn else "warn")
        else:
            self.say(warn + "Inseriu %d. A árvore continua balanceada." % key, "bad" if warn else "ok")
        self.check_game()
        self.keep_visible(node)

    def check_game(self):
        g = self.game
        if g is None or g.result:
            return
        n = self.tree.count
        limit = max_avl_height(n) + 1
        if g.stability <= 0:
            g.result = "lose"
            g.result_text = ("A estabilidade chegou a zero: o desbalanceamento foi ignorado e a árvore "
                             "desmoronou.")
        elif self.tree.height > limit:
            g.result = "lose"
            g.result_text = ("A altura (%d) passou do teto (%d): a árvore virou quase uma lista encadeada "
                             "e a busca degradou para O(n)." % (self.tree.height, limit))
        elif g.index >= len(g.queue) and not self.tree.critical_nodes():
            g.result = "win"
            g.result_text = ("Fila concluída com a árvore AVL válida! Rotações usadas: %d. "
                             "Estabilidade restante: %d/%d." % (self.rotations, g.stability, START_STABILITY))

    # ---------------- rotação ----------------
    def rotate(self, direction):
        """direction: 'L' (esquerda) ou 'R' (direita) no nó selecionado."""
        if self.game and self.game.result:
            return
        x = self.selected
        if x is None:
            self.say("Selecione um nó (clique nele ou use as setas) para rotacionar.", "warn")
            return
        before = len(self.tree.critical_nodes())
        nome = "direita" if direction == "R" else "esquerda"
        pivot = self.tree.rotate_right(x) if direction == "R" else self.tree.rotate_left(x)
        if pivot is None:
            filho = "esquerdo" if direction == "R" else "direito"
            self.say("Não dá para rotacionar à %s no nó %d: ele não tem filho %s." % (nome, x.key, filho), "warn")
            return
        self.rotations += 1
        self.selected = pivot                   # a seleção acompanha o nó que subiu
        after = len(self.tree.critical_nodes())
        msg = "Rotação à %s no nó %d. " % (nome, x.key)
        if after < before:
            self.say(msg + "Nós desbalanceados: %d -> %d. Correto!" % (before, after), "ok")
        elif after > before:
            self.say(msg + "Nós desbalanceados: %d -> %d. Piorou: essa não era a rotação indicada." %
                     (before, after), "bad")
        elif before == 0:
            self.say(msg + "A árvore já estava balanceada: rotação desnecessária.", "info")
        else:
            self.say(msg + "Ainda há %d nó(s) desbalanceado(s). Em casos duplos é normal: falta a 2ª rotação." %
                     after, "warn")
        self.check_game()

    # ---------------- entrada (teclado e mouse) ----------------
    def on_key(self, e):
        k = e.key
        if k in (pygame.K_ESCAPE, pygame.K_q):
            return False
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.game and self.game.result:
                self.start_game()
            else:
                self.insert_from_field()
        elif k == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif k == pygame.K_r:
            self.new_random_or_restart()
        elif k == pygame.K_c:
            self.clear_tree()
        elif k == pygame.K_g:
            self.toggle_mode()
        elif k == pygame.K_t:
            self.toggle_auto()
        elif k == pygame.K_h:
            self.toggle_hint()
        elif k in (pygame.K_f, pygame.K_HOME):
            self.fit_view()
        elif k == pygame.K_a:
            self.rotate("L")
        elif k == pygame.K_d:
            self.rotate("R")
        elif k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP):
            self.navigate(k)
        elif self.mode == "livre" and e.unicode and e.unicode.isdigit() and len(self.text) < 3:
            self.text += e.unicode
        return True

    def navigate(self, k):
        """Navegação pelas setas (como no programa original)."""
        if self.selected is None:
            self.selected = self.tree.root
            return
        s = self.selected
        if k == pygame.K_LEFT and s.left:
            self.selected = s.left
        elif k == pygame.K_RIGHT and s.right:
            self.selected = s.right
        elif k == pygame.K_UP and s.parent:
            self.selected = s.parent

    def handle_event(self, e):
        """Devolve False quando o programa deve fechar."""
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.KEYDOWN:
            return self.on_key(e)
        if e.type == pygame.MOUSEWHEEL:
            self.zoom_at(pygame.mouse.get_pos(), 1.15 ** e.y)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if e.pos[1] < TOP_H:
                for b in self.buttons:
                    if b.rect.collidepoint(e.pos):
                        b.action()
                        break
            else:
                self.dragging = True
                self.drag_moved = False
                self.drag_start = e.pos
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            if math.hypot(e.pos[0] - self.drag_start[0], e.pos[1] - self.drag_start[1]) > 4:
                self.drag_moved = True
            if self.drag_moved:
                self.cam[0] += e.rel[0]
                self.cam[1] += e.rel[1]
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.dragging and not self.drag_moved:
                n = self.node_at(e.pos)
                if n:
                    self.selected = n
            self.dragging = False
        return True

    # ---------------- atualização ----------------
    def update(self):
        for n in self.tree.nodes():
            dx, dy = n.tx - n.x, n.ty - n.y
            if abs(dx) < 0.5 and abs(dy) < 0.5:
                n.x, n.y = n.tx, n.ty
            else:
                n.x += dx * 0.22
                n.y += dy * 0.22

    # ---------------- desenho ----------------
    def draw(self):
        s = self.screen
        s.fill(C_BG)
        if self.mode == "jogo":
            self.draw_ceiling()
        self.draw_tree()
        self.draw_topbar()
        if self.mode == "jogo":
            self.draw_game_strip()
        self.draw_bottom()
        if self.game and self.game.result:
            self.draw_result()

    def draw_tree(self):
        s = self.screen
        sw, sh = s.get_size()
        z = self.zoom
        nodes = self.tree.nodes()
        if not nodes:
            blit_text(s, "Árvore vazia - digite um número no campo do topo e aperte Enter",
                      20, C_DIM, (sw // 2, sh // 2 - 40), "center")
            return
        # arestas
        for n in nodes:
            if n.parent:
                a = self.w2s(n.parent.x, n.parent.y)
                b = self.w2s(n.x, n.y)
                pygame.draw.line(s, C_EDGE, a, b, max(1, int(2 * z)))
        # nós
        r = max(4, int(NODE_R * z))
        pulse = 3 + int(3 * abs(math.sin(pygame.time.get_ticks() / 250.0)))
        for n in nodes:
            sx, sy = self.w2s(n.x, n.y)
            if sx < -2 * r or sx > sw + 2 * r or sy < -2 * r or sy > sh + 2 * r:
                continue
            sx, sy = int(sx), int(sy)
            crit = abs(n.fb) >= 2
            if crit:
                pygame.draw.circle(s, C_BAD, (sx, sy), r + int(pulse * z) + 1, max(1, int(2 * z)))
            pygame.draw.circle(s, C_CRIT_FILL if crit else C_NODE, (sx, sy), r)
            pygame.draw.circle(s, C_BAD if crit else C_NODE_BORDER, (sx, sy), r, max(1, int(2 * z)))
            if n is self.selected:
                pygame.draw.circle(s, C_SEL, (sx, sy), r + max(3, int(5 * z)), max(2, int(3 * z)))
            if z >= 0.45:
                blit_text(s, str(n.key), int(16 * z), C_TEXT, (sx, sy), "center")
                fb_color = C_BAD if crit else C_OK
                fb_text = fb_str(n.fb)
                blit_text(s, fb_text, int(14 * z), fb_color, (sx, sy - r - int(9 * z)), "center")
            elif crit:
                pass

    def draw_ceiling(self):
        """Teto do cenário: altura máxima que uma AVL com n nós poderia ter (+1 de tolerância)."""
        s = self.screen
        sw, sh = s.get_size()
        n = self.tree.count
        if n < 2:
            return
        limit = max_avl_height(n) + 1
        y = int(self.w2s(0, (limit + 0.5) * Y_STEP)[1])
        if TOP_H + GAME_STRIP_H < y < sh - BOTTOM_H:
            for x in range(0, sw, 26):
                pygame.draw.line(s, C_BAD, (x, y), (x + 13, y), 2)
            blit_text(s, "TETO do cenário (altura máxima = %d). Se a árvore passar daqui, ela desmorona." % limit,
                      14, C_BAD, (10, y - 18))

    def draw_topbar(self):
        s = self.screen
        sw = s.get_width()
        pygame.draw.rect(s, C_BAR, (0, 0, sw, TOP_H))
        blit_text(s, "Valor:", 18, C_TEXT, (14, TOP_H // 2), "midleft")
        field = pygame.Rect(76, 14, 110, 44)
        active = self.mode == "livre"
        pygame.draw.rect(s, (8, 9, 14) if active else (30, 32, 40), field, border_radius=6)
        pygame.draw.rect(s, C_NODE_BORDER if active else C_DIM, field, 2, border_radius=6)
        if active:
            shown = self.text
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                shown += "|"
            blit_text(s, shown, 24, C_TEXT, (field.left + 10, field.centery), "midleft")
        else:
            blit_text(s, "fila", 18, C_DIM, (field.left + 10, field.centery), "midleft")
        x = field.right + 12
        for b in self.buttons:
            label = b.label_fn()
            tw = get_font(16).size(label)[0]
            b.rect = pygame.Rect(x, 14, tw + 22, 44)
            on = b.active_fn() if b.active_fn else False
            pygame.draw.rect(s, C_BTN_ON if on else C_BTN, b.rect, border_radius=6)
            blit_text(s, label, 16, C_TEXT, b.rect.center, "center")
            x = b.rect.right + 8

    def draw_game_strip(self):
        s = self.screen
        sw = s.get_width()
        g = self.game
        y0 = TOP_H
        pygame.draw.rect(s, (18, 20, 30), (0, y0, sw, GAME_STRIP_H))
        blit_text(s, "FILA:", 15, C_DIM, (14, y0 + 14))
        upcoming = g.queue[g.index:g.index + 10]
        x = 70
        for i, k in enumerate(upcoming):
            box = pygame.Rect(x, y0 + 6, 40, 40)
            pygame.draw.rect(s, (40, 110, 70) if i == 0 else C_BTN, box, border_radius=6)
            blit_text(s, str(k), 18, C_TEXT, box.center, "center")
            if i == 0:
                blit_text(s, "PRÓXIMA", 11, C_OK, (box.centerx, box.bottom + 5), "center")
            x += 46
        rest = len(g.queue) - g.index - len(upcoming)
        if rest > 0:
            blit_text(s, "+%d" % rest, 15, C_DIM, (x + 4, y0 + 26), "midleft")
        # estabilidade
        bx = 640
        blit_text(s, "ESTABILIDADE:", 15, C_DIM, (bx, y0 + 14))
        for i in range(START_STABILITY):
            seg = pygame.Rect(bx + 120 + i * 40, y0 + 10, 34, 18)
            ok = i < g.stability
            pygame.draw.rect(s, C_OK if ok else (70, 30, 35), seg, border_radius=4)
        blit_text(s, "Rotações: %d" % self.rotations, 16, C_TEXT, (bx + 270, y0 + 13))
        blit_text(s, "Inseridas: %d/%d" % (g.index, len(g.queue)), 16, C_TEXT, (bx + 400, y0 + 13))

    def draw_bottom(self):
        s = self.screen
        sw, sh = s.get_size()
        y0 = sh - BOTTOM_H
        pygame.draw.rect(s, C_BAR, (0, y0, sw, BOTTOM_H))
        t = self.tree
        n = t.count
        blit_text(s, "Nós: %d    Altura: %d    Busca no pior caso: %d comparações (ideal: %d)" %
                  (n, t.height, t.height + 1 if n else 0, ideal_comparisons(n)), 16, C_TEXT, (14, y0 + 8))
        sel = self.selected
        if sel:
            line = ("Selecionado: %d    FB = altura(esq) - altura(dir) = %s    altura do nó: %d    "
                    "profundidade: %d" % (sel.key, fb_str(sel.fb), sel.height, sel.depth))
            blit_text(s, line, 16, C_SEL, (14, y0 + 30))
        else:
            blit_text(s, "Clique num nó (ou use as setas) para selecioná-lo.", 16, C_DIM, (14, y0 + 30))
        # dica ou mensagem
        y = y0 + 52
        if self.hint:
            blit_text(s, self.hint_text(), 15, C_WARN, (14, y))
            y += 20
        for line in wrap_text(self.message, 15, sw - 28)[:2]:
            blit_text(s, line, 15, self.msg_color, (14, y))
            y += 19
        blit_text(s, "Mouse: arrastar = mover | scroll = zoom | clique = selecionar    Setas = navegar    "
                     "A/D = rotação esq./dir.    Enter = inserir", 13, C_DIM, (14, sh - 36))
        blit_text(s, "H = dica    F = enquadrar    R = aleatória/reiniciar    C = limpar    G = modo jogo/livre    "
                     "T = AVL automática    Q/Esc = sair", 13, C_DIM, (14, sh - 18))

    def hint_text(self):
        t = self.tree
        crit = t.critical_nodes()
        if not crit:
            return "Dica: nenhum nó com |FB| >= 2. A árvore já é uma AVL válida."
        x = self.selected if (self.selected and abs(self.selected.fb) >= 2) else crit[0]
        case, steps = diagnose(x)
        return "Dica: nó %d tem FB=%s -> caso %s -> %s." % (x.key, fb_str(x.fb), case, describe_steps(steps))

    def draw_result(self):
        s = self.screen
        sw, sh = s.get_size()
        g = self.game
        panel = pygame.Rect(sw // 2 - 380, sh // 2 - 130, 760, 230)
        pygame.draw.rect(s, (10, 10, 16), panel, border_radius=12)
        color = C_OK if g.result == "win" else C_BAD
        pygame.draw.rect(s, color, panel, 4, border_radius=12)
        title = "VITÓRIA!" if g.result == "win" else "DERROTA"
        blit_text(s, title, 48, color, (panel.centerx, panel.top + 50), "center")
        y = panel.top + 100
        for line in wrap_text(g.result_text, 18, panel.width - 60):
            blit_text(s, line, 18, C_TEXT, (panel.centerx, y), "center")
            y += 26
        blit_text(s, "Enter ou R = jogar de novo    G = modo livre", 16, C_DIM,
                  (panel.centerx, panel.bottom - 24), "center")

    # ---------------- laço principal ----------------
    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                if self.handle_event(e) is False:
                    running = False
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    App().run()
