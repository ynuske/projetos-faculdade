import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

# Cores e configuracoes visuais
COR_FUNDO = "#1e1e2e"
COR_COLUNA = "#181825"
COR_CARTAO = "#313244"
COR_TEXTO = "#cdd6f4"
COR_TEXTO_SUAVE = "#a6adc8"
COR_BORDA = "#45475a"
COR_AZUL = "#89b4fa"
COR_VERDE = "#a6e3a1"
COR_VERMELHO = "#f38ba8"
COR_ESCURO = "#11111b"

STATUS_ORDEM = ["A Fazer", "Fazendo", "Concluido"]
COR_STATUS = {"Fazendo": COR_AZUL, "Concluido": COR_VERDE}
FORMATO_DATA = "%d/%m/%Y"


# Funcao para validar formato de data
def validar_data(texto: str) -> bool:
    if not texto:
        return True
    try:
        datetime.strptime(texto, FORMATO_DATA)
        return True
    except ValueError:
        return False


# Funcao auxiliar para criar campos de entrada
def criar_entrada(pai, largura: int = 20) -> tk.Entry:
    return tk.Entry(
        pai, width=largura, bg=COR_CARTAO, fg=COR_TEXTO, insertbackground="white",
        relief="flat", highlightthickness=1,
        highlightbackground=COR_BORDA, highlightcolor=COR_AZUL
    )


# Funcao auxiliar para criar botoes
def criar_botao(pai, texto: str, comando, bg: str = COR_BORDA, fg: str = COR_TEXTO,
                fonte=("Sans", 8)) -> tk.Button:
    return tk.Button(
        pai, text=texto, command=comando, bg=bg, fg=fg, font=fonte,
        relief="flat", bd=0, padx=8, pady=3, cursor="hand2",
        activebackground=bg, activeforeground=fg
    )


# Classe base para tarefas
class Tarefa:
    NIVEIS_PRIORIDADE = {
        "Baixa": {"peso": 1, "etiqueta": "🟢 [Baixa]"},
        "Media": {"peso": 2, "etiqueta": "🟡 [Media]"},
        "Alta": {"peso": 3, "etiqueta": "🔴 [Alta]"}
    }

    def __init__(self, titulo: str, descricao: str = "", prioridade: str = "Media", status: str = "A Fazer"):
        self.titulo = titulo
        self.descricao = descricao
        self.prioridade = prioridade if prioridade in self.NIVEIS_PRIORIDADE else "Media"
        self.status = status

    # Converter objeto em dicionario
    def para_dicionario(self) -> dict:
        return {
            "tipo": "padrao",
            "titulo": self.titulo,
            "descricao": self.descricao,
            "prioridade": self.prioridade,
            "status": self.status
        }

    # Criar objeto a partir de dicionario
    @classmethod
    def de_dicionario(cls, dados: dict):
        return cls(
            titulo=dados.get("titulo", ""),
            descricao=dados.get("descricao", ""),
            prioridade=dados.get("prioridade", "Media"),
            status=dados.get("status", "A Fazer")
        )


# Subclasse para tarefas com data limite
class TarefaComPrazo(Tarefa):
    def __init__(self, titulo: str, descricao: str, prioridade: str, data_limite: str, status: str = "A Fazer"):
        super().__init__(titulo, descricao, prioridade, status)
        self.data_limite = data_limite

    def para_dicionario(self) -> dict:
        dados = super().para_dicionario()
        dados["tipo"] = "com_prazo"
        dados["data_limite"] = self.data_limite
        return dados

    @classmethod
    def de_dicionario(cls, dados: dict):
        return cls(
            titulo=dados.get("titulo", ""),
            descricao=dados.get("descricao", ""),
            prioridade=dados.get("prioridade", "Media"),
            data_limite=dados.get("data_limite", ""),
            status=dados.get("status", "A Fazer")
        )


# Fabrica para criar o tipo correto de tarefa
def criar_tarefa(titulo: str, descricao: str, prioridade: str, data_limite: str, status: str) -> Tarefa:
    if data_limite:
        return TarefaComPrazo(titulo, descricao, prioridade, data_limite, status)
    return Tarefa(titulo, descricao, prioridade, status)


# Classe de gestao do projeto e dados
class ProjetoKanban:
    def __init__(self, nome: str):
        self.nome = nome
        self.tarefas = []

    def adicionar_tarefa(self, tarefa: Tarefa):
        self.tarefas.append(tarefa)

    def remover_tarefa(self, tarefa: Tarefa):
        if tarefa in self.tarefas:
            self.tarefas.remove(tarefa)

    def substituir_tarefa(self, antiga: Tarefa, nova: Tarefa):
        if antiga in self.tarefas:
            self.tarefas[self.tarefas.index(antiga)] = nova

    # Salvar dados em arquivo json
    def salvar_para_json(self, arquivo="quadro_kanban.json"):
        dados = {
            "nome_projeto": self.nome,
            "tarefas": [t.para_dicionario() for t in self.tarefas]
        }
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    # Carregar dados do arquivo json
    def carregar_de_json(self, arquivo="quadro_kanban.json"):
        if os.path.exists(arquivo):
            try:
                with open(arquivo, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.nome = dados.get("nome_projeto", self.nome)
                    tarefas_carregadas = []
                    for item in dados.get("tarefas", []):
                        if item.get("tipo") == "com_prazo":
                            tarefas_carregadas.append(TarefaComPrazo.de_dicionario(item))
                        else:
                            tarefas_carregadas.append(Tarefa.de_dicionario(item))
                    self.tarefas = tarefas_carregadas
            except Exception:
                self.tarefas = []


# Janela modal para editar tarefas
class DialogoEditarTarefa(tk.Toplevel):
    def __init__(self, pai, tarefa: Tarefa):
        super().__init__(pai)
        self.resultado = None
        self.title("Editar tarefa")
        self.configure(bg=COR_FUNDO, padx=20, pady=16)
        self.resizable(False, False)
        self.transient(pai)
        self.grid_columnconfigure(1, weight=1)

        # Campos do formulario de edicao
        self._rotulo("Titulo:", 0)
        self.entrada_titulo = criar_entrada(self, 42)
        self.entrada_titulo.grid(row=0, column=1, sticky="ew", pady=5, ipady=3)
        self.entrada_titulo.insert(0, tarefa.titulo)

        self._rotulo("Prioridade:", 1)
        self.combo_prioridade = ttk.Combobox(self, values=list(Tarefa.NIVEIS_PRIORIDADE), width=12, state="readonly")
        self.combo_prioridade.set(tarefa.prioridade)
        self.combo_prioridade.grid(row=1, column=1, sticky="w", pady=5)

        self._rotulo("Coluna:", 2)
        self.combo_status = ttk.Combobox(self, values=STATUS_ORDEM, width=12, state="readonly")
        self.combo_status.set(tarefa.status)
        self.combo_status.grid(row=2, column=1, sticky="w", pady=5)

        self._rotulo("Prazo (dd/mm/aaaa):", 3)
        self.entrada_prazo = criar_entrada(self, 14)
        self.entrada_prazo.grid(row=3, column=1, sticky="w", pady=5, ipady=3)
        self.entrada_prazo.insert(0, getattr(tarefa, "data_limite", ""))

        self._rotulo("Descricao:", 4, sticky="nw")
        self.texto_descricao = tk.Text(
            self, width=42, height=5, wrap="word", bg=COR_CARTAO, fg=COR_TEXTO,
            insertbackground="white", relief="flat", highlightthickness=1,
            highlightbackground=COR_BORDA, highlightcolor=COR_AZUL, font=("Sans", 9)
        )
        self.texto_descricao.grid(row=4, column=1, sticky="ew", pady=5)
        self.texto_descricao.insert("1.0", tarefa.descricao)

        # Botoes de acao
        botoes = tk.Frame(self, bg=COR_FUNDO)
        botoes.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        criar_botao(botoes, "Cancelar", self.destroy, fonte=("Sans", 9)).pack(side="left", padx=(0, 8))
        criar_botao(botoes, "Salvar", self._salvar, bg=COR_VERDE, fg=COR_ESCURO,
                    fonte=("Sans", 9, "bold")).pack(side="left")

        self.bind("<Escape>", lambda e: self.destroy())
        self.entrada_titulo.bind("<Return>", lambda e: self._salvar())
        self.entrada_prazo.bind("<Return>", lambda e: self._salvar())

        self._centralizar(pai)
        self.wait_visibility()
        self.grab_set()
        self.entrada_titulo.focus_set()

    # Criar rotulos de texto
    def _rotulo(self, texto: str, linha: int, sticky: str = "w"):
        tk.Label(self, text=texto, font=("Sans", 9), bg=COR_FUNDO, fg=COR_TEXTO).grid(
            row=linha, column=0, sticky=sticky, padx=(0, 12), pady=5
        )

    # Centralizar janela popup
    def _centralizar(self, pai):
        self.update_idletasks()
        x = pai.winfo_rootx() + (pai.winfo_width() - self.winfo_width()) // 2
        y = pai.winfo_rooty() + (pai.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # Salvar alteracoes da tarefa
    def _salvar(self):
        titulo = self.entrada_titulo.get().strip()
        prazo = self.entrada_prazo.get().strip()

        if not titulo:
            messagebox.showwarning("Aviso", "O titulo da tarefa e obrigatorio.", parent=self)
            return
        if not validar_data(prazo):
            messagebox.showwarning("Aviso", "Prazo invalido. Use o formato dd/mm/aaaa.", parent=self)
            return

        self.resultado = {
            "titulo": titulo,
            "descricao": self.texto_descricao.get("1.0", "end").strip(),
            "prioridade": self.combo_prioridade.get(),
            "data_limite": prazo,
            "status": self.combo_status.get(),
        }
        self.destroy()


# Componente visual para cada coluna do kanban
class ColunaKanban(tk.Frame):
    def __init__(self, pai, titulo: str, chave_status: str, referencia_app, cor_fundo: str):
        super().__init__(pai, bg=cor_fundo, bd=1, relief="ridge")
        self.titulo = titulo
        self.chave_status = chave_status
        self.app = referencia_app

        # Cabecalho da coluna
        cabecalho = tk.Frame(self, bg=cor_fundo)
        cabecalho.pack(fill="x", padx=12, pady=(10, 6))
        tk.Label(
            cabecalho, text=self.titulo.upper(), font=("Sans", 11, "bold"),
            bg=cor_fundo, fg=COR_TEXTO
        ).pack(side="left")
        self.lbl_contador = tk.Label(
            cabecalho, text="0", font=("Sans", 9, "bold"),
            bg=COR_CARTAO, fg=COR_TEXTO, padx=8
        )
        self.lbl_contador.pack(side="right")

        # Area de conteudo com rolagem
        corpo = tk.Frame(self, bg=cor_fundo)
        corpo.pack(fill="both", expand=True, padx=(8, 4), pady=(0, 8))

        self.canvas = tk.Canvas(corpo, bg=cor_fundo, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(corpo, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.container_cartoes = tk.Frame(self.canvas, bg=cor_fundo)
        self._janela = self.canvas.create_window((0, 0), window=self.container_cartoes, anchor="nw")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._janela, width=e.width))
        self.container_cartoes.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

    # Rolar conteudo da coluna
    def rolar(self, direcao: int):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(direcao * 2, "units")

    # Manter posicao da barra de rolagem
    def restaurar_rolagem(self, posicao: float):
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(posicao)

    # Limpar cartoes da coluna
    def limpar(self):
        for widget in self.container_cartoes.winfo_children():
            widget.destroy()

    # Atualizar total de tarefas da coluna
    def atualizar_contador(self, quantidade: int):
        self.lbl_contador.configure(text=str(quantidade))

    # Desenhar cartao da tarefa
    def adicionar_cartao(self, tarefa: Tarefa):
        cartao = tk.Frame(self.container_cartoes, bg=COR_CARTAO, padx=10, pady=8, bd=1, relief="groove")
        cartao.pack(fill="x", pady=4, padx=(4, 6))

        rotulos_quebraveis = []

        # Adicionar texto com quebra automatica
        def novo_texto(texto, fonte, cor, pady):
            lbl = tk.Label(cartao, text=texto, font=fonte, bg=COR_CARTAO, fg=cor,
                           anchor="w", justify="left", wraplength=240)
            lbl.pack(fill="x", pady=pady)
            rotulos_quebraveis.append(lbl)
            return lbl

        # Ajustar largura do texto ao redimensionar
        def ajustar_quebra(evento):
            for lbl in rotulos_quebraveis:
                lbl.configure(wraplength=max(evento.width - 30, 60))

        cartao.bind("<Configure>", ajustar_quebra)

        lbl_etiqueta = tk.Label(
            cartao, text=Tarefa.NIVEIS_PRIORIDADE[tarefa.prioridade]["etiqueta"],
            font=("Sans", 8, "bold"), bg=COR_CARTAO, fg=COR_TEXTO
        )
        lbl_etiqueta.pack(anchor="w")

        novo_texto(tarefa.titulo, ("Sans", 10, "bold"), COR_TEXTO, (2, 0))
        if tarefa.descricao:
            novo_texto(tarefa.descricao, ("Sans", 8), COR_TEXTO_SUAVE, (2, 2))
        if isinstance(tarefa, TarefaComPrazo):
            tk.Label(
                cartao, text=f"⏰ {tarefa.data_limite}", font=("Sans", 8, "italic"),
                bg=COR_CARTAO, fg=COR_VERMELHO, anchor="w"
            ).pack(fill="x", pady=(2, 0))

        # Botoes do cartao
        acoes = tk.Frame(cartao, bg=COR_CARTAO)
        acoes.pack(fill="x", pady=(8, 0))

        indice = STATUS_ORDEM.index(self.chave_status)

        if indice > 0:
            anterior = STATUS_ORDEM[indice - 1]
            criar_botao(acoes, f"← {anterior}",
                        lambda: self.app.mover_tarefa(tarefa, anterior)).pack(side="left")

        criar_botao(acoes, "✕", lambda: self.app.excluir_tarefa(tarefa),
                    bg=COR_VERMELHO, fg=COR_ESCURO).pack(side="right")
        criar_botao(acoes, "Editar",
                    lambda: self.app.editar_tarefa(tarefa)).pack(side="right", padx=(0, 4))

        if indice < len(STATUS_ORDEM) - 1:
            proximo = STATUS_ORDEM[indice + 1]
            criar_botao(acoes, f"{proximo} →", lambda: self.app.mover_tarefa(tarefa, proximo),
                        bg=COR_STATUS[proximo], fg=COR_ESCURO).pack(side="right", padx=(0, 4))

        # Abrir edicao com duplo clique
        for widget in [cartao, lbl_etiqueta] + rotulos_quebraveis:
            widget.bind("<Double-Button-1>", lambda e: self.app.editar_tarefa(tarefa))


# Classe principal da aplicacao
class AppKanban(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Tarefas - Quadro Kanban")
        self.geometry("1040x640")
        self.minsize(900, 560)
        self.configure(bg=COR_FUNDO)

        self.projeto = ProjetoKanban("Desenvolvimento de Software")
        self.projeto.carregar_de_json()
        self.widgets_colunas = {}

        self._construir_interface()
        self._configurar_rolagem_mouse()
        self.atualizar_quadro()

    # Construir elementos da interface
    def _construir_interface(self):
        quadro_formulario = tk.LabelFrame(
            self, text=" Nova Tarefa no Kanban ", font=("Sans", 10, "bold"),
            bg=COR_FUNDO, fg=COR_AZUL, padx=15, pady=10
        )
        quadro_formulario.pack(fill="x", padx=15, pady=(12, 8))
        quadro_formulario.grid_columnconfigure(1, weight=1)

        def rotulo(texto, linha, coluna, padx=(0, 6)):
            tk.Label(quadro_formulario, text=texto, font=("Sans", 9), bg=COR_FUNDO, fg=COR_TEXTO).grid(
                row=linha, column=coluna, sticky="w", padx=padx, pady=4
            )

        rotulo("Titulo:", 0, 0)
        self.entrada_titulo = criar_entrada(quadro_formulario)
        self.entrada_titulo.grid(row=0, column=1, sticky="ew", pady=4, ipady=3)

        rotulo("Prioridade:", 0, 2, padx=(18, 6))
        self.combo_prioridade = ttk.Combobox(
            quadro_formulario, values=list(Tarefa.NIVEIS_PRIORIDADE), width=9, state="readonly"
        )
        self.combo_prioridade.set("Media")
        self.combo_prioridade.grid(row=0, column=3, sticky="w", pady=4)

        rotulo("Prazo (dd/mm/aaaa):", 0, 4, padx=(18, 6))
        self.entrada_prazo = criar_entrada(quadro_formulario, 14)
        self.entrada_prazo.grid(row=0, column=5, sticky="ew", pady=4, ipady=3)

        rotulo("Descricao:", 1, 0)
        self.entrada_descricao = criar_entrada(quadro_formulario)
        self.entrada_descricao.grid(row=1, column=1, columnspan=4, sticky="ew", pady=4, ipady=3)

        criar_botao(
            quadro_formulario, "+ Adicionar Tarefa", self.tratar_adicionar_tarefa,
            bg=COR_VERDE, fg=COR_ESCURO, fonte=("Sans", 9, "bold")
        ).grid(row=1, column=5, sticky="ew", pady=4, padx=(0, 0))

        for campo in (self.entrada_titulo, self.entrada_descricao, self.entrada_prazo):
            campo.bind("<Return>", lambda e: self.tratar_adicionar_tarefa())

        quadro_colunas = tk.Frame(self, bg=COR_FUNDO)
        quadro_colunas.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        quadro_colunas.grid_rowconfigure(0, weight=1)

        for indice, status in enumerate(STATUS_ORDEM):
            quadro_colunas.grid_columnconfigure(indice, weight=1, uniform="colunas")
            coluna = ColunaKanban(quadro_colunas, status, status, self, COR_COLUNA)
            coluna.grid(row=0, column=indice, sticky="nsew", padx=6)
            self.widgets_colunas[status] = coluna

    # Habilitar rolagem via roda do mouse
    def _configurar_rolagem_mouse(self):
        self.bind_all("<MouseWheel>", self._ao_rolar)
        self.bind_all("<Button-4>", self._ao_rolar)
        self.bind_all("<Button-5>", self._ao_rolar)

    # Processar evento de rolagem
    def _ao_rolar(self, evento):
        try:
            widget = self.winfo_containing(evento.x_root, evento.y_root)
        except KeyError:
            return
        while widget is not None and not isinstance(widget, ColunaKanban):
            widget = widget.master
        if widget is None:
            return

        if evento.num == 4:
            direcao = -1
        elif evento.num == 5:
            direcao = 1
        else:
            direcao = -1 if evento.delta > 0 else 1
        widget.rolar(direcao)

    # Adicionar nova tarefa
    def tratar_adicionar_tarefa(self):
        titulo = self.entrada_titulo.get().strip()
        descricao = self.entrada_descricao.get().strip()
        prioridade = self.combo_prioridade.get()
        data_limite = self.entrada_prazo.get().strip()

        if not titulo:
            messagebox.showwarning("Aviso", "O titulo da tarefa e obrigatorio.")
            return
        if not validar_data(data_limite):
            messagebox.showwarning("Aviso", "Prazo invalido. Use o formato dd/mm/aaaa.")
            return

        nova_tarefa = criar_tarefa(titulo, descricao, prioridade, data_limite, "A Fazer")
        self.projeto.adicionar_tarefa(nova_tarefa)
        self.projeto.salvar_para_json()

        self.entrada_titulo.delete(0, tk.END)
        self.entrada_descricao.delete(0, tk.END)
        self.entrada_prazo.delete(0, tk.END)
        self.combo_prioridade.set("Media")
        self.entrada_titulo.focus_set()

        self.atualizar_quadro()

    # Abrir janela para editar tarefa
    def editar_tarefa(self, tarefa: Tarefa):
        dialogo = DialogoEditarTarefa(self, tarefa)
        self.wait_window(dialogo)

        if dialogo.resultado is None:
            return

        tarefa_editada = criar_tarefa(**dialogo.resultado)
        self.projeto.substituir_tarefa(tarefa, tarefa_editada)
        self.projeto.salvar_para_json()
        self.atualizar_quadro()

    # Mover tarefa entre colunas
    def mover_tarefa(self, tarefa: Tarefa, novo_status: str):
        tarefa.status = novo_status
        self.projeto.salvar_para_json()
        self.atualizar_quadro()

    # Excluir tarefa do projeto
    def excluir_tarefa(self, tarefa: Tarefa):
        if not messagebox.askyesno("Excluir tarefa", f"Excluir a tarefa \"{tarefa.titulo}\"?"):
            return
        self.projeto.remover_tarefa(tarefa)
        self.projeto.salvar_para_json()
        self.atualizar_quadro()

    # Redesenhar todos os cartoes no quadro
    def atualizar_quadro(self):
        posicoes = {chave: col.canvas.yview()[0] for chave, col in self.widgets_colunas.items()}
        contagem = {chave: 0 for chave in self.widgets_colunas}

        for coluna in self.widgets_colunas.values():
            coluna.limpar()

        for tarefa in self.projeto.tarefas:
            if tarefa.status in self.widgets_colunas:
                self.widgets_colunas[tarefa.status].adicionar_cartao(tarefa)
                contagem[tarefa.status] += 1

        for chave, coluna in self.widgets_colunas.items():
            coluna.atualizar_contador(contagem[chave])
            coluna.restaurar_rolagem(posicoes[chave])


if __name__ == "__main__":
    app = AppKanban()
    app.mainloop()