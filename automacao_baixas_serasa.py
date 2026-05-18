"""Interface desktop da automacao de Baixas SERASA."""

import os
import re
import threading
import time
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk
from tkinter import ttk

import config_portal
from excel_utils import (
    COLUNA_AUTO_NORMALIZADO,
    COLUNA_CPF_CNPJ_NORMALIZADO,
    aplicar_resultado,
    exportar_resultado,
    preparar_base,
)
from logging_utils import Logger
from portal_serasa import AutomacaoPortalSerasa, SemDividasEncontradas


CORES = {
    "verde": "#27ae60",
    "vermelho": "#e74c3c",
    "azul": "#2980b9",
    "amarelo": "#f39c12",
    "escuro": "#2c3e50",
    "fundo": "#f0f0f0",
    "card": "#FFFFFF",
    "cinza": "#ecf0f1",
    "texto": "#1F2933",
}

FONTE = "Segoe UI"


class InterfaceBaixasSerasa:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Baixas SERASA")
        self.root.geometry("1040x720")
        self.root.minsize(920, 640)
        self.root.configure(bg=CORES["fundo"])

        self.arquivo_entrada = tk.StringVar()
        self.arquivo_saida = tk.StringVar()
        self.motivo_baixa = tk.StringVar()
        self.usuario_login = tk.StringVar()
        self.senha_login = tk.StringVar()
        self.status = tk.StringVar(value="Aguardando arquivo...")
        self.progresso = tk.DoubleVar(value=0)
        self.sucessos = tk.IntVar(value=0)
        self.erros = tk.IntVar(value=0)

        self.logger = Logger(self._log_callback)
        self.thread_automacao = None
        self.portal = None
        self.pausado = False
        self.parar = False
        self.executando = False
        self.motivo_id_execucao = "1"

        self._configurar_estilo()
        self._montar_tela()

    def executar(self):
        self.root.mainloop()

    def _configurar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background=CORES["card"])
        style.configure("Titulo.TLabel", background=CORES["fundo"], foreground=CORES["texto"], font=(FONTE, 18, "bold"))
        style.configure("Card.TLabel", background=CORES["card"], foreground=CORES["texto"], font=(FONTE, 10))
        style.configure("Primario.TButton", font=(FONTE, 10, "bold"))
        style.configure("Perigo.TButton", font=(FONTE, 10, "bold"))
        style.configure("TCombobox", font=(FONTE, 10))
        style.configure("Horizontal.TProgressbar", troughcolor="#D7DBDD", background=CORES["azul"])

    def _montar_tela(self):
        header = tk.Frame(self.root, bg=CORES["escuro"], height=62)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Baixas SERASA",
            font=(FONTE, 16, "bold"),
            bg=CORES["escuro"],
            fg="white",
        ).pack(side=tk.LEFT, padx=22, pady=18)
        modo_teste = " | MODO TESTE: nao envia baixas" if config_portal.MODO_TESTE_SEM_ENVIAR else ""
        tk.Label(
            header,
            text=f"Portal SERASA Experian | Execucao em guia normal{modo_teste}",
            font=(FONTE, 9),
            bg=CORES["escuro"],
            fg="#bdc3c7",
        ).pack(side=tk.LEFT, pady=21)

        container = tk.Frame(self.root, bg=CORES["fundo"], padx=20, pady=14)
        container.pack(fill=tk.BOTH, expand=True)

        card_login = tk.LabelFrame(
            container,
            text="  Login SERASA  ",
            bg=CORES["fundo"],
            font=(FONTE, 10, "bold"),
            relief=tk.GROOVE,
            bd=1,
            padx=14,
            pady=12,
        )
        card_login.pack(fill=tk.X, pady=(0, 12))
        self._linha_login(card_login, "Usuario/E-mail", self.usuario_login)
        self._linha_login(card_login, "Senha", self.senha_login, show="*")

        card_arquivos = tk.LabelFrame(
            container,
            text="  Arquivos e Motivo de Baixa  ",
            bg=CORES["fundo"],
            font=(FONTE, 10, "bold"),
            relief=tk.GROOVE,
            bd=1,
            padx=14,
            pady=12,
        )
        card_arquivos.pack(fill=tk.X, pady=(0, 12))

        self._linha_arquivo(
            card_arquivos,
            "Planilha de entrada",
            self.arquivo_entrada,
            self._selecionar_entrada,
        )
        self._linha_arquivo(
            card_arquivos,
            "Resultado automatico",
            self.arquivo_saida,
            self._selecionar_saida,
            texto_botao="Alterar pasta",
            somente_leitura=True,
        )
        self._linha_motivo(card_arquivos)

        card_status = tk.Frame(container, bg=CORES["cinza"], relief=tk.GROOVE, bd=1)
        card_status.pack(fill=tk.X, pady=(0, 12))
        miolo_status = tk.Frame(card_status, bg=CORES["cinza"])
        miolo_status.pack(padx=16, pady=10)
        self._label_stat(miolo_status, "Sucessos:", self.sucessos, CORES["verde"])
        self._label_stat(miolo_status, "Erros:", self.erros, CORES["vermelho"])
        tk.Label(miolo_status, textvariable=self.status, bg=CORES["cinza"], fg=CORES["azul"], font=(FONTE, 9, "bold")).pack(side=tk.LEFT, padx=(18, 0))

        card_log = tk.LabelFrame(
            container,
            text="  Logs  ",
            bg=CORES["fundo"],
            font=(FONTE, 10, "bold"),
            relief=tk.GROOVE,
            bd=1,
            padx=10,
            pady=8,
        )
        card_log.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            card_log,
            height=18,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config("ERROR", foreground=CORES["vermelho"])
        self.log_text.tag_config("SUCCESS", foreground=CORES["verde"])
        self.log_text.tag_config("WARNING", foreground=CORES["amarelo"])

        self.barra = ttk.Progressbar(container, variable=self.progresso, maximum=100)
        self.barra.pack(fill=tk.X, pady=(0, 12))

        card_acoes = tk.Frame(container, bg=CORES["fundo"])
        card_acoes.pack(fill=tk.X)
        self._botao(card_acoes, "Iniciar", CORES["verde"], self._iniciar).pack(side=tk.LEFT, padx=(0, 10))
        self._botao(card_acoes, "Pausar/Continuar", CORES["amarelo"], self._alternar_pausa).pack(side=tk.LEFT, padx=(0, 10))
        self._botao(card_acoes, "Parar", CORES["vermelho"], self._parar).pack(side=tk.LEFT, padx=(0, 10))
        self._botao(card_acoes, "Abrir portal para mapear", CORES["azul"], self._abrir_portal_mapeamento).pack(side=tk.LEFT)

    def _linha_arquivo(self, parent, titulo, variavel, comando, texto_botao="Selecionar", somente_leitura=False):
        frame = tk.Frame(parent, bg=CORES["fundo"])
        frame.pack(fill=tk.X, pady=4)
        tk.Label(frame, text=titulo, bg=CORES["fundo"], font=(FONTE, 9), width=22, anchor="w").pack(side=tk.LEFT)
        estado = "readonly" if somente_leitura else "normal"
        ttk.Entry(frame, textvariable=variavel, state=estado).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(frame, text=texto_botao, command=comando).pack(side=tk.LEFT)

    def _linha_login(self, parent, titulo, variavel, show=""):
        frame = tk.Frame(parent, bg=CORES["fundo"])
        frame.pack(fill=tk.X, pady=4)
        tk.Label(frame, text=titulo, bg=CORES["fundo"], font=(FONTE, 9), width=22, anchor="w").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=variavel, show=show).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _linha_motivo(self, parent):
        frame = tk.Frame(parent, bg=CORES["fundo"])
        frame.pack(fill=tk.X, pady=4)
        tk.Label(frame, text="Motivo da baixa", bg=CORES["fundo"], font=(FONTE, 9), width=22, anchor="w").pack(side=tk.LEFT)
        opcoes = [f"{codigo} - {descricao}" for codigo, descricao in config_portal.MOTIVOS_BAIXA.items()]
        self.combo_motivo = ttk.Combobox(frame, textvariable=self.motivo_baixa, values=opcoes, state="readonly")
        self.combo_motivo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo_motivo.set(opcoes[0])

    def _label_stat(self, parent, texto, variavel, cor):
        tk.Label(parent, text=texto, bg=CORES["cinza"], font=(FONTE, 9)).pack(side=tk.LEFT)
        tk.Label(parent, textvariable=variavel, bg=CORES["cinza"], fg=cor, font=(FONTE, 12, "bold")).pack(side=tk.LEFT, padx=(4, 22))

    def _botao(self, parent, texto, cor, comando):
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=cor,
            fg="white",
            font=(FONTE, 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=18,
            pady=10,
            activebackground=cor,
            activeforeground="white",
        )

    def _selecionar_entrada(self):
        caminho = filedialog.askopenfilename(
            title="Selecione a planilha",
            filetypes=[
                ("Planilhas", "*.xlsx *.xlsm *.xls *.csv"),
                ("Excel", "*.xlsx *.xlsm *.xls"),
                ("CSV", "*.csv"),
                ("Todos", "*.*"),
            ],
        )
        if not caminho:
            return
        self.arquivo_entrada.set(caminho)
        self.arquivo_saida.set(self._saida_padrao(caminho))

    def _selecionar_saida(self):
        if not self.arquivo_entrada.get():
            messagebox.showwarning(
                "Selecione a entrada",
                "Selecione primeiro a planilha de entrada para eu gerar o nome automatico do resultado.",
            )
            return
        pasta = filedialog.askdirectory(
            title="Escolha a pasta onde a planilha de resultado sera salva",
            initialdir=os.path.dirname(self.arquivo_entrada.get()),
        )
        if pasta:
            self.arquivo_saida.set(self._saida_padrao(self.arquivo_entrada.get(), pasta_saida=pasta))

    def _saida_padrao(self, entrada, pasta_saida=None):
        pasta = pasta_saida or os.path.dirname(entrada)
        nome_entrada = os.path.splitext(os.path.basename(entrada))[0]
        nome_entrada = self._limpar_nome_arquivo(nome_entrada)
        stamp = datetime.now().strftime("%d-%m-%Y %Hh%Mmin%Ss")
        return os.path.join(pasta, f"Resultado Baixas SERASA - {nome_entrada} - {stamp}.xlsx")

    def _limpar_nome_arquivo(self, nome):
        nome = str(nome or "Planilha").replace("_", " ")
        nome = re.sub(r'[<>:"/\\|?*]+', " ", nome)
        nome = re.sub(r"\s+", " ", nome).strip()
        return nome or "Planilha"

    def _motivo_id_selecionado(self):
        valor = self.motivo_baixa.get().strip()
        motivo_id = valor.split(" - ", 1)[0].strip()
        if motivo_id not in config_portal.MOTIVOS_BAIXA:
            raise ValueError("Selecione um motivo de baixa valido.")
        return motivo_id

    def _iniciar(self):
        if self.executando:
            messagebox.showwarning("Automacao em andamento", "A automacao ja esta em execucao.")
            return
        if not self.arquivo_entrada.get():
            messagebox.showwarning("Arquivo obrigatorio", "Selecione a planilha de entrada.")
            return
        if not self.arquivo_saida.get():
            self.arquivo_saida.set(self._saida_padrao(self.arquivo_entrada.get()))
        try:
            self.motivo_id_execucao = self._motivo_id_selecionado()
        except ValueError as exc:
            messagebox.showwarning("Motivo obrigatorio", str(exc))
            return

        self.parar = False
        self.pausado = False
        self.executando = True
        self.progresso.set(0)
        self.sucessos.set(0)
        self.erros.set(0)
        self.status.set("Iniciando...")

        pasta_logs = os.path.join(os.path.dirname(__file__), "logs")
        log_path = os.path.join(pasta_logs, f"baixas_serasa_{datetime.now():%Y%m%d_%H%M%S}.txt")
        self.logger.set_log_file(log_path)

        self.thread_automacao = threading.Thread(target=self._executar_automacao, daemon=True)
        self.thread_automacao.start()

    def _executar_automacao(self):
        df = None
        try:
            self.logger.log("Lendo e validando planilha...")
            df, colunas = preparar_base(self.arquivo_entrada.get())
            total = len(df)
            self.logger.log(
                f"Planilha carregada com {total} linha(s). Colunas: CPF/CNPJ='{colunas['cpf_cnpj']}', Auto='{colunas['auto_infracao']}'.",
                "SUCCESS",
            )

            self.portal = AutomacaoPortalSerasa(self.logger)
            self.portal.iniciar()
            self.portal.abrir_portal()
            self.portal.realizar_login_automatico(
                self.usuario_login.get().strip(),
                self.senha_login.get(),
            )
            self.portal.aguardar_login_manual()

            processadas = 0
            motivo_id = self.motivo_id_execucao

            for indice, linha in df[df["STATUS_BAIXA"].astype(str).str.upper() == "IGNORADO"].iterrows():
                self.logger.log(f"Linha ignorada por dados invalidos: indice {indice}", "WARNING")
                processadas += 1
                self._incrementar_contador(self.erros)
                self._atualizar_progresso(processadas, total)

            df_processar = df[df["STATUS_BAIXA"].astype(str).str.upper() != "IGNORADO"]
            for cpf_cnpj, grupo in df_processar.groupby(COLUNA_CPF_CNPJ_NORMALIZADO, sort=False):
                if self.parar:
                    for indice_grupo in grupo.index:
                        aplicar_resultado(df, indice_grupo, "PARADO", "Execucao interrompida pelo usuario.", 0)
                    self.logger.log("Execucao interrompida pelo usuario.", "WARNING")
                    break

                while self.pausado and not self.parar:
                    self._set_status("Pausado")
                    time.sleep(0.5)

                try:
                    self.portal.pesquisar_cpf_cnpj(cpf_cnpj)
                except SemDividasEncontradas as exc:
                    msg = f"CPF/CNPJ {cpf_cnpj}: nenhuma divida encontrada no portal."
                    self.logger.log(msg, "WARNING")
                    for indice_grupo in grupo.index:
                        aplicar_resultado(df, indice_grupo, "SEM_DIVIDA", str(exc) or msg, 0)
                        processadas += 1
                        self._incrementar_contador(self.erros)
                        self._atualizar_progresso(processadas, total)
                    exportar_resultado(df, self.arquivo_saida.get())
                    continue
                except Exception as exc:
                    erro_msg = f"Erro ao pesquisar CPF/CNPJ {cpf_cnpj}: {exc}"
                    self.logger.log(erro_msg, "ERROR")
                    for indice_grupo in grupo.index:
                        aplicar_resultado(df, indice_grupo, "ERRO", erro_msg, 0)
                        processadas += 1
                        self._incrementar_contador(self.erros)
                        self._atualizar_progresso(processadas, total)
                    exportar_resultado(df, self.arquivo_saida.get())
                    continue

                self.logger.log(f"CPF/CNPJ {cpf_cnpj}: {len(grupo)} auto(s) para baixar.")
                for indice, linha in grupo.iterrows():
                    if self.parar:
                        aplicar_resultado(df, indice, "PARADO", "Execucao interrompida pelo usuario.", 0)
                        processadas += 1
                        self._atualizar_progresso(processadas, total)
                        continue

                    while self.pausado and not self.parar:
                        self._set_status("Pausado")
                        time.sleep(0.5)

                    auto = linha[COLUNA_AUTO_NORMALIZADO]
                    resultado = self.portal.processar_auto_na_tela(auto, motivo_id)
                    aplicar_resultado(
                        df,
                        indice,
                        resultado.status,
                        resultado.mensagem,
                        resultado.tentativas,
                        resultado.observacao,
                    )

                    tipo_log = "SUCCESS" if resultado.status == "SUCESSO" else "WARNING"
                    if resultado.status in {"ERRO", "NAO_LOCALIZADO"}:
                        tipo_log = "ERROR"
                        self._incrementar_contador(self.erros)
                    elif resultado.status in {"SUCESSO", "TESTE_SEM_ENVIO"}:
                        self._incrementar_contador(self.sucessos)
                    self.logger.log(
                        f"Resultado linha {processadas + 1}/{total}: {resultado.status} - {resultado.mensagem}",
                        tipo_log,
                    )

                    processadas += 1
                    self._atualizar_progresso(processadas, total)
                    if processadas % config_portal.CHECKPOINT_A_CADA == 0:
                        exportar_resultado(df, self.arquivo_saida.get())

            exportar_resultado(df, self.arquivo_saida.get())
            self.logger.log(f"Resultado salvo em: {self.arquivo_saida.get()}", "SUCCESS")
            self._set_status("Concluido")
            self.root.after(0, lambda: messagebox.showinfo("Concluido", "Automacao finalizada. Resultado exportado."))
        except Exception as exc:
            erro_msg = str(exc)
            self.logger.log(f"Erro fatal: {erro_msg}", "ERROR")
            if df is not None:
                try:
                    exportar_resultado(df, self.arquivo_saida.get())
                    self.logger.log("Resultado parcial salvo apos erro.", "WARNING")
                except Exception as export_exc:
                    self.logger.log(f"Nao foi possivel salvar resultado parcial: {export_exc}", "ERROR")
            self._set_status("Erro")
            self.root.after(0, lambda msg=erro_msg: messagebox.showerror("Erro", msg))
        finally:
            if self.portal:
                self.portal.fechar()
            self.executando = False

    def _abrir_portal_mapeamento(self):
        if self.executando:
            messagebox.showwarning("Automacao em andamento", "Pare a execucao antes de abrir o modo de mapeamento.")
            return

        def trabalho():
            try:
                self.executando = True
                self.logger.log("Abrindo portal para mapeamento de telas...")
                self.portal = AutomacaoPortalSerasa(self.logger)
                self.portal.iniciar()
                self.portal.abrir_portal()
                self.logger.log(
                    "Navegue manualmente ate a tela de baixa. Depois informe os IDs/XPaths para configurar config_portal.py.",
                    "WARNING",
                )
                self._set_status("Portal aberto para mapeamento")
            except Exception as exc:
                erro_msg = str(exc)
                self.logger.log(f"Erro ao abrir portal: {erro_msg}", "ERROR")
                self.root.after(0, lambda msg=erro_msg: messagebox.showerror("Erro", msg))
            finally:
                self.executando = False

        threading.Thread(target=trabalho, daemon=True).start()

    def _alternar_pausa(self):
        if not self.executando:
            return
        self.pausado = not self.pausado
        self.logger.log("Automacao pausada." if self.pausado else "Automacao retomada.", "WARNING")

    def _parar(self):
        if not self.executando:
            return
        self.parar = True
        self.pausado = False
        self.logger.log("Solicitada parada da automacao.", "WARNING")

    def _log_callback(self, mensagem, tipo):
        def inserir():
            if tipo in {"ERROR", "SUCCESS", "WARNING"}:
                self.log_text.insert(tk.END, mensagem + "\n", tipo)
            else:
                self.log_text.insert(tk.END, mensagem + "\n")
            self.log_text.see(tk.END)

        self.root.after(0, inserir)

    def _atualizar_progresso(self, processadas, total):
        percentual = 0 if total == 0 else (processadas / total) * 100
        self.root.after(0, lambda: self.progresso.set(percentual))
        self._set_status(f"Processadas {processadas}/{total}")

    def _set_status(self, texto):
        self.root.after(0, lambda: self.status.set(texto))

    def _incrementar_contador(self, variavel):
        self.root.after(0, lambda: variavel.set(variavel.get() + 1))


if __name__ == "__main__":
    app = InterfaceBaixasSerasa()
    app.executar()
