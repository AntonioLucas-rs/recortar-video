"""
Recorta a area dos videos ao lado deste script, um por um, e salva na pasta
"videos_prontos".

Uso:
    python recortar_video.py

Escolha Recorte livre ou uma proporcao na parte inferior. Arraste o mouse
para selecionar a area que fica e clique em Salvar (ou numa pasta).
Arraste dentro da selecao para reposiciona-la. Sem selecao, o video sai do tamanho
original. Pular passa ao próximo vídeo sem alterar o arquivo.

Para ver o video: clique ou arraste na linha do tempo, clique numa das
miniaturas, ou use as setas (1 segundo) e as teclas , e . (1 quadro).

O campo Titulo vira o nome do arquivo e o titulo gravado no video. Os outros
metadados (data de gravacao, aparelho, localizacao...) sao apagados.

O corte e feito em segundo plano: pode ir para o proximo video sem esperar.
Ao fechar a janela, o script termina os cortes que faltam antes de sair.
"""

import shutil
import subprocess
import sys
from math import gcd
import tkinter as tk
from tkinter import simpledialog
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import cv2
    from PIL import Image, ImageTk
except ImportError as erro:
    raise SystemExit("Faltam bibliotecas do programa. Abra o terminal e execute: "
                     "python -m pip install opencv-python Pillow") from erro

PASTA = Path(__file__).resolve().parent
POR_LINHA = 9


def limpar_nome(nome):
    """Normaliza nomes de arquivos e pastas para Windows."""
    nome = "".join(c for c in nome if c not in '\\/:*?"<>|' and ord(c) >= 32).strip(" .")
    reservados = {"CON", "PRN", "AUX", "NUL"} | {f"{p}{i}" for p in ("COM", "LPT") for i in range(1, 10)}
    return "_" + nome if nome.split(".")[0].upper() in reservados else nome

EXTENSOES_VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv"}
ORIGEM = PASTA
DESTINO = PASTA / "videos_prontos"
REGISTRO = ".feitos.txt"   # videos ja processados, mesmo que tenham trocado de nome
MINIATURAS = 10
ALTURA_MINI = 56
FORMATOS = {
    "Recorte livre": None,
    "1:1": (1, 1),
    "4:5": (4, 5),
    "9:16": (9, 16),
    "16:9": (16, 9),
    "4:3": (4, 3),
    "Original": "original",
}


def selecionar_area(inicio, fim, tamanho, proporcao=None):
    """Retângulo em pixels do vídeo, limitado à imagem e à proporção."""
    w, h = tamanho
    ax, ay = (min(max(v, 0), limite) for v, limite in zip(inicio, tamanho))
    bx, by = (min(max(v, 0), limite) for v, limite in zip(fim, tamanho))
    dx, dy = bx - ax, by - ay
    if proporcao:
        pw, ph = proporcao
        sinal_x, sinal_y = (-1 if dx < 0 else 1), (-1 if dy < 0 else 1)
        max_w = ax if sinal_x < 0 else w - ax
        max_h = ay if sinal_y < 0 else h - ay
        escala = min(max(abs(dx) / pw, abs(dy) / ph), max_w / pw, max_h / ph)
        bx, by = ax + sinal_x * pw * escala, ay + sinal_y * ph * escala
        # Evita resíduos de ponto flutuante fora da imagem (ex.: -1e-14).
        bx, by = min(max(bx, 0), w), min(max(by, 0), h)
    return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


def area_para_video(area, tamanho, proporcao=None):
    """Garante dimensões pares e, nos presets, a proporção exata."""
    w, h = tamanho
    x0, y0, x1, y1 = area
    x0, y0 = max(0, round(x0)), max(0, round(y0))
    largura = min(w, round(x1)) - x0
    altura = min(h, round(y1)) - y0
    if proporcao:
        pw, ph = proporcao
        divisor = gcd(pw, ph)
        pw, ph = pw // divisor, ph // divisor
        # Duas unidades da razão reduzida mantêm ambos os lados pares.
        unidades = min(largura // (2 * pw), altura // (2 * ph))
        largura, altura = unidades * 2 * pw, unidades * 2 * ph
    else:
        largura, altura = largura // 2 * 2, altura // 2 * 2
    if largura < 2 or altura < 2:
        raise ValueError("Seleção muito pequena. Arraste uma área maior para este formato.")
    return x0, y0, largura, altura


def caminho_livre(caminho):
    """Se ja existir um arquivo com esse nome, usa "nome (2)", "nome (3)"..."""
    n = 2
    livre = caminho
    while livre.exists():
        livre = caminho.with_name(f"{caminho.stem} ({n}){caminho.suffix}")
        n += 1
    return livre


def cortar(origem, pasta, nome, area, titulo, registro):
    """Grava o video na pasta com o titulo novo e sem os outros metadados.

    Com area (x, y, largura, altura), corta a imagem; sem area, so copia o
    video e o audio sem recomprimir.
    """
    ext = ".mp4" if area else origem.suffix.lower()
    destino = caminho_livre(pasta / (nome + ext))
    parcial = destino.with_name(destino.stem + ".parcial" + ext)

    entrada = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(origem), "-map", "0:v:0", "-map", "0:a?"]
    # -map_metadata -1 apaga data, aparelho, GPS etc.; bitexact tira a marca do ffmpeg
    meta = ["-map_metadata", "-1", "-map_chapters", "-1", "-metadata", f"title={titulo}", "-fflags", "+bitexact",
            "-metadata:s:v:0", "encoder="]
    if ext in (".mp4", ".mov", ".m4v"):
        meta += ["-movflags", "+faststart"]
    if area:
        x, y, w, h = area
        video = ["-vf", f"crop={w}:{h}:{x}:{y}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                 "-pix_fmt", "yuv420p"]
        # tenta manter o audio original; se o formato nao couber em mp4, converte para AAC
        audios = (["-c:a", "copy"], ["-c:a", "aac", "-b:a", "192k"])
    else:
        video = ["-c:v", "copy"]
        audios = (["-c:a", "copy"],)

    for audio in audios:
        feito = subprocess.run(entrada + video + audio + meta + [str(parcial)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        if feito.returncode == 0:
            parcial.replace(destino)
            with open(registro, "a", encoding="utf-8") as f:
                f.write(origem.name + "\n")
            tamanho = f"{area[2]}x{area[3]}" if area else "tamanho original"
            return f"  pronto    {origem.name} -> {destino.parent.name}/{destino.name}  ({tamanho})"
    parcial.unlink(missing_ok=True)
    erro = feito.stderr.strip().splitlines()
    return f"  ERRO      {origem.name}: {erro[-1] if erro else 'ffmpeg falhou'}"


class JanelaRecorte:
    """Janela e seleção compartilhadas pelos controles de vídeo deste arquivo."""

    def __init__(self, videos, destino):
        self.videos, self.destino = videos, destino
        self.indice = -1
        self.salvas = self.omitidos = 0
        self.selecao = None   # (x0, y0, x1, y1) em pixels da tela
        self.inicio = None

        self.janela = tk.Tk()
        self.larg = int(self.janela.winfo_screenwidth() * 0.8)
        self.alt = int(self.janela.winfo_screenheight() * self.ALTURA)

        barra = tk.Frame(self.janela, padx=8, pady=6)
        barra.pack(fill="x")
        tk.Button(barra, text="Salvar", width=10, bg="#2e7d32", fg="white", command=self.salvar).pack(side="left")
        tk.Button(barra, text="Pular", width=10, command=self.pular).pack(side="right")
        self.aviso = tk.Label(barra, anchor="w", padx=12, wraplength=650, justify="left")
        self.aviso.pack(side="left", fill="x", expand=True)

        self.painel = tk.Frame(self.janela, padx=8)
        self.painel.pack(fill="x", pady=(0, 6))
        self.montar_pastas()

        self.tela = tk.Canvas(self.janela, width=self.larg, height=self.alt, bg="#2b2b2b",
                              highlightthickness=0, cursor="crosshair")
        self.tela.pack()
        self.tela.bind("<ButtonPress-1>", self.ao_clicar)
        self.tela.bind("<B1-Motion>", self.ao_arrastar)
        self.janela.bind("<Return>", lambda e: self.salvar())
        self.janela.bind("<Escape>", lambda e: self.limpar_selecao())

        self.montar_extras()
        self.proxima()


    def montar_extras(self):
        """Espaco para subclasses porem mais controles na janela."""


    def proxima(self):
        while True:
            self.indice += 1
            if self.indice >= len(self.videos):
                self.janela.destroy()
                return
            self.arquivo = self.videos[self.indice]
            self.original = self.abrir(self.arquivo)
            if self.original is not None:
                break
            print(f"  pulando {self.arquivo.name} (nao consegui abrir)")
        self.janela.title(f"Recortar ({self.indice + 1}/{len(self.videos)}) - {self.arquivo.name}")
        self.mostrar()


    def area_selecionada(self):
        """Selecao em pixels do vídeo (x0, y0, x1, y1), ou None se nao houver."""
        if self.selecao is None:
            return None
        h, w = self.original.shape[:2]
        bx0, by0, bx1, by1 = self.limites
        sx0, sy0, sx1, sy1 = self.selecao
        x0, x1 = (round((v - bx0) * w / (bx1 - bx0)) for v in (sx0, sx1))
        y0, y1 = (round((v - by0) * h / (by1 - by0)) for v in (sy0, sy1))
        return x0, y0, x1, y1


    def salvar(self, subpasta=None):
        """Salva no destino, ou numa subpasta dele, e abre a proxima."""
        pasta = self.destino / subpasta if subpasta else self.destino
        pasta.mkdir(parents=True, exist_ok=True)
        if self.gravar(self.area_selecionada(), pasta) is False:
            return
        self.salvas += 1
        self.proxima()


    def montar_pastas(self):
        """Um botao para cada subpasta do destino: clicar salva direto nela."""
        for item in self.painel.winfo_children():
            item.destroy()
        pastas = sorted(p.name for p in self.destino.iterdir() if p.is_dir()) if self.destino.is_dir() else []
        itens = [tk.Label(self.painel, text="Salvar na pasta:")]
        itens += [tk.Button(self.painel, text=nome, padx=8, command=lambda n=nome: self.salvar(n)) for nome in pastas]
        itens.append(tk.Button(self.painel, text="+ Nova pasta", padx=8, fg="#1565c0", command=self.nova_pasta))
        for i, item in enumerate(itens):
            item.grid(row=i // POR_LINHA, column=i % POR_LINHA, padx=(0, 6), pady=2, sticky="w")


    def nova_pasta(self):
        nome = simpledialog.askstring("Nova pasta", "Nome da pasta:", parent=self.janela)
        if nome:
            self.criar_pasta(nome)


    def criar_pasta(self, nome):
        """Cria a subpasta e ja salva o vídeo atual nela."""
        nome = limpar_nome(nome)
        if not nome:
            self.aviso.config(text="Nome de pasta invalido.")
            return
        (self.destino / nome).mkdir(parents=True, exist_ok=True)
        self.montar_pastas()
        self.salvar(nome)


    def pular(self):
        """Passa ao próximo vídeo sem salvar, mover ou apagar o original."""
        self.fechar()
        self.omitidos += 1
        print(f"  pulado    {self.arquivo.name}")
        self.proxima()


    def mostrar(self):
        h, w = self.original.shape[:2]
        escala = min(self.larg / w, self.alt / h, 4)
        lw, lh = max(1, round(w * escala)), max(1, round(h * escala))
        dx, dy = (self.larg - lw) // 2, (self.alt - lh) // 2
        self.limites = (dx, dy, dx + lw, dy + lh)

        self.tela.delete("all")
        self.selecao = None
        self.inicio = None
        self.desenhar(self.original)
        self.aviso.config(text=f"{w}x{h}   Arraste o mouse para selecionar a area que fica (ESC limpa). "
                               "Salvar corta na selecao, ou salva como esta.")


    def desenhar(self, img):
        """Poe a imagem na tela, por baixo da selecao."""
        x0, y0, x1, y1 = self.limites
        figura = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).resize((x1 - x0, y1 - y0), Image.LANCZOS)
        self.figura = ImageTk.PhotoImage(figura, master=self.janela)  # guardar, senao o tk apaga
        self.tela.delete("figura")
        self.tela.create_image(x0, y0, image=self.figura, anchor="nw", tags="figura")
        self.tela.tag_lower("figura")


    def prender(self, x, y):
        """Mantem o ponto dentro do vídeo."""
        x0, y0, x1, y1 = self.limites
        return min(max(x, x0), x1), min(max(y, y0), y1)





    def limpar_selecao(self):
        self.tela.delete("selecao")
        self.selecao = None


class RecortadorVideo(JanelaRecorte):
    ALTURA = 0.43   # espaço para os formatos, linha do tempo e miniaturas

    def __init__(self, videos, destino):
        self.video = None
        self.fila = ThreadPoolExecutor(max_workers=1)   # um corte por vez
        self.cortes = []
        self.agendado = None
        self.movendo = None
        super().__init__(videos, destino)

    # ---------- controles extras ----------

    def montar_extras(self):
        self.linha = tk.Canvas(self.janela, width=self.larg, height=26, bg="#1e1e1e",
                               highlightthickness=0, cursor="hand2")
        self.linha.pack(padx=8, pady=(6, 0))
        self.linha.bind("<ButtonPress-1>", self.ao_mexer_linha)
        self.linha.bind("<B1-Motion>", self.ao_mexer_linha)

        self.tira = tk.Canvas(self.janela, width=self.larg, height=ALTURA_MINI + 6, bg="#1e1e1e",
                              highlightthickness=0, cursor="hand2")
        self.tira.pack(padx=8, pady=(4, 0))
        self.tira.bind("<ButtonPress-1>", self.ao_clicar_tira)

        rodape = tk.Frame(self.janela, padx=8, pady=6)
        rodape.pack(fill="x")
        self.tempo = tk.Label(rodape, font=("Consolas", 10), anchor="w", width=30)
        self.tempo.pack(side="left")
        tk.Label(rodape, text="Titulo:").pack(side="left", padx=(8, 4))
        self.titulo = tk.Entry(rodape, width=45)
        self.titulo.pack(side="left", fill="x", expand=True)

        formatos = tk.LabelFrame(self.janela, text="Formato do recorte", padx=8, pady=4)
        formatos.pack(fill="x", padx=8, pady=(0, 6))
        self.formato = tk.StringVar(master=self.janela, value="Recorte livre")
        for i, nome in enumerate(FORMATOS):
            tk.Radiobutton(formatos, text=nome, variable=self.formato, value=nome,
                           indicatoron=False, padx=9, command=self.trocar_formato).grid(
                               row=i // 7, column=i % 7, padx=(0, 4), pady=2, sticky="w")
        self.dica = tk.Label(formatos, anchor="w", justify="left", wraplength=self.larg - 30)
        self.dica.grid(row=1, column=0, columnspan=7, sticky="w", pady=(4, 0))
        self.tela.bind("<ButtonRelease-1>", self.ao_soltar)

        for tecla, passo in (("<Left>", -1), ("<Right>", 1)):
            self.janela.bind(tecla, lambda e, p=passo: self.avancar_quadros(p * round(self.fps)))
        for tecla, passo in (("<comma>", -1), ("<period>", 1)):
            self.janela.bind(tecla, lambda e, p=passo: self.avancar_quadros(p))

    def proporcao(self):
        formato = FORMATOS[self.formato.get()]
        if formato == "original":
            h, w = self.original.shape[:2]
            return w, h
        return formato

    def ponto_video(self, x, y):
        x, y = self.prender(x, y)
        bx0, by0, bx1, by1 = self.limites
        h, w = self.original.shape[:2]
        return (x - bx0) * w / (bx1 - bx0), (y - by0) * h / (by1 - by0)

    def selecionar_na_tela(self, area):
        bx0, by0, bx1, by1 = self.limites
        h, w = self.original.shape[:2]
        x0, y0, x1, y1 = area
        self.selecao = (bx0 + x0 * (bx1 - bx0) / w, by0 + y0 * (by1 - by0) / h,
                        bx0 + x1 * (bx1 - bx0) / w, by0 + y1 * (by1 - by0) / h)
        self.desenhar_selecao()

    def desenhar_selecao(self):
        self.tela.delete("selecao")
        if self.selecao is None:
            return
        x0, y0, x1, y1 = self.selecao
        bx0, by0, bx1, by1 = self.limites
        for caixa in ((bx0, by0, bx1, y0), (bx0, y1, bx1, by1),
                      (bx0, y0, x0, y1), (x1, y0, bx1, y1)):
            self.tela.create_rectangle(*caixa, fill="black", stipple="gray50", width=0, tags="selecao")
        self.tela.create_rectangle(x0, y0, x1, y1, outline="#ffeb3b", width=2, tags="selecao")
        try:
            h, w = self.original.shape[:2]
            area = area_para_video(self.area_selecionada(), (w, h), self.proporcao())
            texto = f"{self.formato.get()} · {area[2]} × {area[3]} pixels"
        except ValueError as erro:
            texto = str(erro)
        self.dica.config(text=texto + " | Arraste dentro para mover. Esc limpa para desenhar outro recorte.")

    def limpar_selecao(self):
        super().limpar_selecao()
        self.inicio = None
        self.movendo = None
        self.dica.config(text="Arraste no vídeo para recortar. Esc limpa. Sem seleção, salva o vídeo inteiro. "
                              "Setas: 1 segundo; , e .: 1 quadro.")

    def trocar_formato(self):
        self.limpar_selecao()
        self.tela.focus_set()

    def ao_clicar(self, evento):
        self.tela.focus_set()
        ponto = self.prender(evento.x, evento.y)
        if self.selecao:
            x0, y0, x1, y1 = self.selecao
            if x0 <= ponto[0] <= x1 and y0 <= ponto[1] <= y1:
                self.inicio = ponto
                self.movendo = self.selecao
                return
        self.limpar_selecao()
        self.inicio = ponto

    def ao_arrastar(self, evento):
        if self.inicio is None:
            return
        x, y = self.prender(evento.x, evento.y)
        if self.movendo is not None:
            x0, y0, x1, y1 = self.movendo
            bx0, by0, bx1, by1 = self.limites
            dx = min(max(x - self.inicio[0], bx0 - x0), bx1 - x1)
            dy = min(max(y - self.inicio[1], by0 - y0), by1 - y1)
            self.selecao = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            self.desenhar_selecao()
            return
        if max(abs(x - self.inicio[0]), abs(y - self.inicio[1])) < 5:
            return
        h, w = self.original.shape[:2]
        area = selecionar_area(self.ponto_video(*self.inicio), self.ponto_video(x, y),
                              (w, h), self.proporcao())
        self.selecionar_na_tela(area)

    def ao_soltar(self, evento):
        self.inicio = None
        self.movendo = None

    def proxima(self):
        super().proxima()
        if self.indice >= len(self.videos):
            self.fechar()
            return
        self.movendo = None
        self.limpar_selecao()
        self.titulo.delete(0, "end")
        self.titulo.insert(0, self.arquivo.stem)
        self.montar_tira()
        self.ir_para(0)

    # ---------- abrir e navegar no video ----------

    def abrir(self, caminho):
        self.fechar()
        self.video = cv2.VideoCapture(str(caminho))
        self.total = max(1, int(self.video.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.fps = self.video.get(cv2.CAP_PROP_FPS) or 30
        self.quadro = 0
        ok, quadro = self.video.read()
        return quadro if ok else None

    def fechar(self):
        if self.agendado is not None:
            self.janela.after_cancel(self.agendado)
            self.agendado = None
        if self.video is not None:
            self.video.release()
            self.video = None

    def ler(self, numero):
        self.video.set(cv2.CAP_PROP_POS_FRAMES, numero)
        ok, quadro = self.video.read()
        return quadro if ok and quadro.shape == self.original.shape else None

    def ir_para(self, numero):
        """Mostra o quadro pedido, mantendo a selecao."""
        if self.video is None:
            return
        numero = min(max(int(numero), 0), self.total - 1)
        quadro = self.ler(numero)
        if quadro is not None:
            self.desenhar(quadro)
            self.quadro = numero
        self.atualizar_linha()

    def avancar_quadros(self, quadros):
        if self.janela.focus_get() is self.titulo:   # setas servem para editar o titulo
            return
        self.ir_para(self.quadro + quadros)

    def ao_mexer_linha(self, evento):
        self.tela.focus_set()
        self.alvo = evento.x / max(1, self.larg - 1) * (self.total - 1)
        # enquanto arrasta, le no maximo um quadro a cada 40 ms
        if self.agendado is None:
            self.agendado = self.janela.after(40, self.ir_para_alvo)

    def ir_para_alvo(self):
        self.agendado = None
        self.ir_para(self.alvo)

    def tempo_de(self, numero):
        s = numero / self.fps
        return f"{int(s // 60):02d}:{s % 60:05.2f}"

    def atualizar_linha(self):
        x = self.quadro / max(1, self.total - 1) * (self.larg - 1)
        self.linha.delete("all")
        self.linha.create_rectangle(0, 10, self.larg, 16, fill="#444", width=0)
        self.linha.create_rectangle(0, 10, x, 16, fill="#ffeb3b", width=0)
        self.linha.create_rectangle(x - 3, 3, x + 3, 23, fill="white", width=0)
        self.tempo.config(text=f"{self.tempo_de(self.quadro)} / {self.tempo_de(self.total - 1)}"
                               f"   quadro {self.quadro + 1}")
        # destaca a miniatura do trecho atual
        self.tira.delete("atual")
        if self.mini_quadros:
            i = min(range(len(self.mini_quadros)), key=lambda k: abs(self.mini_quadros[k] - self.quadro))
            x0 = i * self.celula
            self.tira.create_rectangle(x0 + 1, 1, x0 + self.celula - 2, ALTURA_MINI + 5,
                                       outline="#ffeb3b", width=2, tags="atual")

    # ---------- miniaturas ----------

    def montar_tira(self):
        """Uma fileira de quadros espalhados pelo video; clicar leva ate eles."""
        self.aviso.config(text="Carregando miniaturas...")
        self.janela.update_idletasks()
        n = min(MINIATURAS, self.total)
        self.celula = self.larg / n
        self.mini_quadros = [round(i * (self.total - 1) / max(1, n - 1)) for i in range(n)]
        self.minis = []
        self.tira.delete("all")
        for i, numero in enumerate(self.mini_quadros):
            quadro = self.ler(numero)
            if quadro is None:
                continue
            h, w = quadro.shape[:2]
            escala = min((self.celula - 6) / w, ALTURA_MINI / h)
            mini = Image.fromarray(cv2.cvtColor(quadro, cv2.COLOR_BGR2RGB)).resize(
                (max(1, int(w * escala)), max(1, int(h * escala))), Image.BILINEAR)
            self.minis.append(ImageTk.PhotoImage(mini, master=self.janela))
            self.tira.create_image((i + 0.5) * self.celula, ALTURA_MINI / 2 + 3, image=self.minis[-1])
        self.mostrar()   # restaura o aviso e a imagem do primeiro quadro

    def ao_clicar_tira(self, evento):
        self.tela.focus_set()
        i = min(int(evento.x // self.celula), len(self.mini_quadros) - 1)
        self.ir_para(self.mini_quadros[i])

    # ---------- salvar ----------

    def gravar(self, area, pasta):
        titulo = self.titulo.get().strip() or self.arquivo.stem
        nome = limpar_nome(titulo) or self.arquivo.stem
        if area is not None:
            h, w = self.original.shape[:2]
            try:
                area = area_para_video(area, (w, h), self.proporcao())
            except ValueError as erro:
                self.aviso.config(text=str(erro))
                return False
        corte = self.fila.submit(cortar, self.arquivo, pasta, nome, area, titulo, self.destino / REGISTRO)
        self.cortes.append(corte)
        tamanho = f"{area[2]}x{area[3]}" if area else "sem corte"
        print(f"  na fila   {self.arquivo.name}  ({tamanho})  titulo: {titulo}")


def listar_videos(origem, destino):
    """Videos da origem que ainda nao foram processados."""
    if not origem.is_dir():
        return []
    registro = destino / REGISTRO
    feitos = set(registro.read_text(encoding="utf-8").splitlines()) if registro.exists() else set()
    return sorted(p for p in origem.iterdir()
                  if p.is_file() and p.suffix.lower() in EXTENSOES_VIDEO and p.name not in feitos)


def main():
    if shutil.which("ffmpeg") is None:
        raise SystemExit("FFmpeg não encontrado. Instale-o, adicione a pasta bin ao PATH "
                         "e abra novamente o terminal. Consulte o README.md.")
    videos = listar_videos(ORIGEM, DESTINO)
    if not videos:
        raise SystemExit(f'Nenhum video para recortar em "{ORIGEM}" (os que ja foram feitos nao aparecem de novo).')
    DESTINO.mkdir(exist_ok=True)
    app = RecortadorVideo(videos, DESTINO)
    try:
        if app.indice < len(app.videos):
            app.janela.protocol("WM_DELETE_WINDOW", lambda: (app.fechar(), app.janela.destroy()))
            app.janela.mainloop()
    finally:
        app.fechar()
        pendentes = [c for c in app.cortes if not c.done()]
        if pendentes:
            print(f"Terminando {len(pendentes)} video(s), nao feche esta janela...")
        app.fila.shutdown(wait=True)
    erros = 0
    for corte in app.cortes:
        try:
            resultado = corte.result()
            print(resultado)
            erros += resultado.startswith("  ERRO")
        except Exception as erro:
            erros += 1
            print(f"  ERRO      {erro}")
    print(f'{len(app.cortes) - erros} vídeo(s) salvo(s) em "{DESTINO}", '
          f'{app.omitidos} pulado(s), {erros} erro(s).')
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
