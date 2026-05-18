"""Nucleo Selenium para o portal SERASA."""

import re
import time
from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config_portal as config


class ConfiguracaoPortalIncompleta(Exception):
    """Indica que os seletores reais ainda precisam ser mapeados."""


class SemDividasEncontradas(Exception):
    """Indica que o portal retornou a tela de nenhuma divida encontrada."""


@dataclass
class ResultadoPortal:
    status: str
    mensagem: str
    tentativas: int
    observacao: str = ""


class AutomacaoPortalSerasa:
    def __init__(self, logger, headless=None):
        self.logger = logger
        self.headless = config.HEADLESS if headless is None else headless
        self.driver = None
        self.wait = None
        self.operar_sem_foco = config.OPERAR_SEM_DEPENDER_DO_FOCO

    def iniciar(self):
        if self.driver:
            return

        opcoes = Options()
        if self.headless:
            opcoes.add_argument("--headless=new")
        opcoes.add_argument("--start-maximized")
        opcoes.add_argument("--disable-blink-features=AutomationControlled")
        opcoes.add_argument("--disable-notifications")
        opcoes.add_argument("--log-level=3")

        self.logger.log("Abrindo navegador Chrome em guia normal...")
        self.driver = webdriver.Chrome(options=opcoes)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT_PADRAO)

    def abrir_portal(self):
        self._garantir_driver()
        self.logger.log(f"Abrindo portal: {config.URL_PORTAL}")
        self.driver.get(config.URL_PORTAL)

    def realizar_login_automatico(self, usuario: str, senha: str):
        if not usuario or not senha:
            self.logger.log("Credenciais nao preenchidas; login ficara manual.", "WARNING")
            return

        self._garantir_driver()
        self.logger.log("Tentando preencher login automaticamente...")
        try:
            campo_usuario = self._aguardar_curto("campo_usuario_login", timeout=20)
            if not campo_usuario:
                self.logger.log("Campo de usuario/e-mail nao localizado. Continue o login manualmente.", "WARNING")
                return

            self._preencher_elemento(campo_usuario, usuario)
            campo_senha = self._aguardar_curto("campo_senha_login", timeout=3)

            if not campo_senha:
                self._clicar_login_ou_enter(campo_usuario)
                campo_senha = self._aguardar_curto("campo_senha_login", timeout=45)

            if not campo_senha:
                self.logger.log("Campo de senha nao localizado. Continue o login manualmente.", "WARNING")
                return

            self._preencher_elemento(campo_senha, senha)
            self._clicar_login_ou_enter(campo_senha)
            self.logger.log(
                "Credenciais enviadas. Se o portal solicitar codigo por e-mail, informe manualmente.",
                "SUCCESS",
            )
        except Exception as exc:
            self.logger.log(f"Nao foi possivel concluir o login automatico: {exc.__class__.__name__}", "WARNING")

    def aguardar_login_manual(self):
        self._garantir_driver()
        self.logger.log(
            "Se necessario, finalize o login manualmente e informe o codigo recebido por e-mail. "
            "A automacao clicara em Acessar quando o produto aparecer e aguardara a tela de pesquisa.",
            "WARNING",
        )
        pendentes = config.seletores_pendentes()
        if pendentes:
            self.logger.log(
                "Seletores ainda pendentes em config_portal.py: " + ", ".join(pendentes),
                "WARNING",
            )
            return

        self._acessar_produto_apos_login()
        self.aguardar_tela_pesquisa()

    def aguardar_tela_pesquisa(self):
        WebDriverWait(self.driver, config.TIMEOUT_LOGIN_MANUAL).until(
            EC.presence_of_element_located(config.SELETORES["campo_cpf_cnpj"])
        )
        self.logger.log("Tela de pesquisa de dividas localizada.", "SUCCESS")
        if self.operar_sem_foco:
            self.logger.log(
                "Modo sem foco ativo: voce pode deixar outra janela na frente do Chrome.",
                "SUCCESS",
            )

    def pesquisar_cpf_cnpj(self, cpf_cnpj: str):
        pendentes = config.seletores_pendentes()
        if pendentes:
            raise ConfiguracaoPortalIncompleta("Seletores pendentes: " + ", ".join(pendentes))

        self.logger.log(f"Pesquisando CPF/CNPJ {cpf_cnpj}...")
        self._aguardar_overlay()
        self._preencher("campo_cpf_cnpj", cpf_cnpj)
        try:
            self._clicar("botao_pesquisar")
        except Exception:
            campo = self._buscar("campo_cpf_cnpj", clicavel=False)
            campo.send_keys(Keys.ENTER)
        self._aguardar_overlay()
        self._aguardar_resultado_pesquisa()

    def processar_baixa(self, cpf_cnpj: str, auto_infracao: str, motivo_id: str) -> ResultadoPortal:
        pendentes = config.seletores_pendentes()
        if pendentes:
            return ResultadoPortal(
                status="PENDENTE_MAPEAMENTO",
                mensagem="Seletores do portal ainda nao configurados.",
                tentativas=0,
                observacao="Preencher em config_portal.py: " + ", ".join(pendentes),
            )

        self.pesquisar_cpf_cnpj(cpf_cnpj)
        return self.processar_auto_na_tela(auto_infracao, motivo_id)

    def processar_auto_na_tela(self, auto_infracao: str, motivo_id: str) -> ResultadoPortal:
        if motivo_id not in config.MOTIVOS_BAIXA:
            return ResultadoPortal(
                status="ERRO",
                mensagem=f"Motivo de baixa invalido: {motivo_id}",
                tentativas=0,
            )

        ultima_mensagem = ""
        for tentativa in range(1, config.TENTATIVAS_POR_ITEM + 1):
            try:
                self.logger.log(
                    f"Baixando Auto {auto_infracao} | motivo {motivo_id} | tentativa {tentativa}"
                )
                self._aguardar_overlay()
                linha = self._localizar_linha_auto(auto_infracao)
                if linha is None:
                    self.logger.log(f"Auto {auto_infracao}: nao localizado na tabela.", "ERROR")
                    return ResultadoPortal(
                        status="NAO_LOCALIZADO",
                        mensagem=f"Auto {auto_infracao} nao localizado na tabela do CPF/CNPJ pesquisado.",
                        tentativas=tentativa,
                    )

                self.logger.log(f"Auto {auto_infracao}: procurando botao Excluir na linha...")
                botao_excluir = linha.find_element(*config.SELETORES["botao_excluir_linha"])
                self.logger.log(f"Auto {auto_infracao}: clicando no botao Excluir.")
                self._clicar_elemento(botao_excluir)
                self._aguardar_overlay()
                self.logger.log(f"Auto {auto_infracao}: clique em Excluir concluido. Confirmando em Sim...")
                self._clicar("botao_confirmar_sim")
                self._aguardar_overlay()
                self.logger.log(f"Auto {auto_infracao}: clique em Sim concluido. Selecionando motivo {motivo_id}...")
                self._selecionar_motivo(motivo_id)
                self.logger.log(f"Auto {auto_infracao}: motivo {motivo_id} selecionado.")
                if config.MODO_TESTE_SEM_ENVIAR:
                    self.logger.log(
                        "MODO TESTE ATIVO: o botao final Enviar nao sera clicado. Fechando modal em Voltar.",
                        "WARNING",
                    )
                    self.logger.log(f"Auto {auto_infracao}: clicando em Voltar para fechar o modal de teste.")
                    self._clicar("botao_voltar_motivo")
                    self._aguardar_modal_motivo_fechar()
                    self.logger.log(f"Auto {auto_infracao}: modal fechado em Voltar. Proximo item liberado.", "SUCCESS")
                    return ResultadoPortal(
                        status="TESTE_SEM_ENVIO",
                        mensagem=(
                            f"Fluxo validado ate a selecao do motivo para o Auto {auto_infracao}. "
                            "Baixa nao enviada; modal fechado em Voltar."
                        ),
                        tentativas=tentativa,
                        observacao="Modo teste ativo em config_portal.py",
                    )
                self.logger.log(f"Auto {auto_infracao}: clicando no botao final Enviar.")
                self._clicar("botao_enviar_motivo")
                mensagem = self._aguardar_pos_envio(auto_infracao)
                self.logger.log(f"Auto {auto_infracao}: envio final concluido.", "SUCCESS")
                return ResultadoPortal(status="SUCESSO", mensagem=mensagem, tentativas=tentativa)
            except (TimeoutException, ElementClickInterceptedException, StaleElementReferenceException) as exc:
                ultima_mensagem = f"Falha temporaria no portal: {exc.__class__.__name__}"
                self.logger.log(ultima_mensagem, "WARNING")
                time.sleep(min(tentativa * 2, 8))
            except NoSuchElementException as exc:
                ultima_mensagem = f"Elemento esperado nao encontrado: {exc.__class__.__name__}"
                self.logger.log(ultima_mensagem, "WARNING")
                time.sleep(min(tentativa * 2, 8))
            except WebDriverException as exc:
                ultima_mensagem = f"Erro do navegador: {exc.__class__.__name__}"
                self.logger.log(ultima_mensagem, "ERROR")
                time.sleep(min(tentativa * 2, 8))

        return ResultadoPortal(
            status="ERRO",
            mensagem=ultima_mensagem or "Nao foi possivel concluir a baixa.",
            tentativas=config.TENTATIVAS_POR_ITEM,
        )

    def fechar(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        self.driver = None
        self.wait = None

    def _garantir_driver(self):
        if not self.driver or not self.wait:
            raise RuntimeError("Navegador ainda nao iniciado.")

    def _buscar(self, nome, clicavel=False):
        seletor = config.SELETORES.get(nome)
        if not seletor:
            raise ConfiguracaoPortalIncompleta(f"Seletor nao configurado: {nome}")
        condicao = EC.element_to_be_clickable(seletor) if clicavel else EC.presence_of_element_located(seletor)
        return self.wait.until(condicao)

    def _acessar_produto_apos_login(self):
        try:
            self._pular_tour_se_aparecer()
            WebDriverWait(self.driver, config.TIMEOUT_LOGIN_MANUAL).until(
                lambda driver: driver.find_elements(*config.SELETORES["botao_acessar_produto"])
                or driver.find_elements(*config.SELETORES["campo_cpf_cnpj"])
            )
            if self.driver.find_elements(*config.SELETORES["campo_cpf_cnpj"]):
                self.logger.log("Tela de pesquisa ja esta aberta; nao preciso clicar em Acessar.")
                return

            botao = self._primeiro_elemento_visivel("botao_acessar_produto")
            if botao:
                self.logger.log("Produto localizado. Clicando em Acessar...")
                handles_antes = set(self.driver.window_handles)
                self._clicar_elemento(botao)
                self._aguardar_overlay()
                handles_depois = set(self.driver.window_handles)
                novas_janelas = list(handles_depois - handles_antes)
                if novas_janelas:
                    self.driver.switch_to.window(novas_janelas[-1])
                    self.logger.log("Produto abriu em nova guia. Alternando para ela.")
                WebDriverWait(self.driver, config.TIMEOUT_LOGIN_MANUAL).until(
                    EC.presence_of_element_located(config.SELETORES["campo_cpf_cnpj"])
                )
                return

            self.logger.log("Botao Acessar apareceu no DOM, mas nenhum estava visivel.", "WARNING")
        except TimeoutException:
            self.logger.log("Botao Acessar nao apareceu; tentando localizar tela de pesquisa diretamente.", "WARNING")

    def _pular_tour_se_aparecer(self):
        try:
            botao = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(config.SELETORES["botao_pular_tour"])
            )
            self.logger.log("Tour inicial localizado. Clicando em Pular tour...")
            self._clicar_elemento(botao)
            self._aguardar_overlay()
        except TimeoutException:
            return

    def _preencher(self, nome, valor):
        elemento = self._buscar(nome, clicavel=False)
        self._rolar_para(elemento)
        self._preencher_elemento(elemento, valor)

    def _preencher_elemento(self, elemento, valor):
        self._rolar_para(elemento)
        if self.operar_sem_foco:
            self._preencher_input_por_js(elemento, valor)
            return

        try:
            elemento.click()
            elemento.send_keys(Keys.CONTROL, "a")
            elemento.send_keys(Keys.BACKSPACE)
            elemento.send_keys(str(valor))
            return
        except ElementClickInterceptedException:
            self.logger.log(f"Clique interceptado no campo {nome}; preenchendo por foco controlado.", "WARNING")

        self._preencher_input_por_js(elemento, valor)

    def _aguardar_curto(self, nome, timeout=10):
        seletor = config.SELETORES.get(nome)
        if not seletor:
            return None
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(seletor))
        except TimeoutException:
            return None

    def _clicar_login_ou_enter(self, elemento_fallback):
        botao = self._primeiro_elemento_visivel("botao_login")
        if botao:
            self._clicar_elemento(botao)
        else:
            elemento_fallback.send_keys(Keys.ENTER)
        self._aguardar_overlay()

    def _clicar(self, nome):
        elemento = self._buscar(nome, clicavel=not self.operar_sem_foco)
        self._clicar_elemento(elemento)

    def _clicar_elemento(self, elemento):
        self._rolar_para(elemento)
        if self.operar_sem_foco:
            self.driver.execute_script("arguments[0].click();", elemento)
            return

        try:
            elemento.click()
        except ElementClickInterceptedException:
            try:
                ActionChains(self.driver).move_to_element(elemento).click().perform()
            except Exception:
                self.driver.execute_script("arguments[0].click();", elemento)
        except WebDriverException:
            self.driver.execute_script("arguments[0].click();", elemento)

    def _primeiro_elemento_visivel(self, nome):
        seletor = config.SELETORES.get(nome)
        if not seletor:
            return None
        for elemento in self.driver.find_elements(*seletor):
            try:
                if elemento.is_displayed() and elemento.is_enabled():
                    return elemento
            except StaleElementReferenceException:
                continue
        return None

    def _preencher_input_por_js(self, elemento, valor):
        script = """
            const element = arguments[0];
            const value = arguments[1];
            element.focus();
            const prototype = Object.getPrototypeOf(element);
            const descriptor = Object.getOwnPropertyDescriptor(prototype, 'value');
            if (descriptor && descriptor.set) {
                descriptor.set.call(element, value);
            } else {
                element.value = value;
            }
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
        """
        self.driver.execute_script(script, elemento, str(valor))

    def _aguardar_resultado_pesquisa(self):
        try:
            resultado = WebDriverWait(self.driver, config.TIMEOUT_PADRAO).until(
                lambda driver: driver.find_elements(*config.SELETORES["linhas_tabela"])
                or driver.find_elements(*config.SELETORES["sem_dividas"])
            )
            if resultado and resultado[0].get_attribute("data-testid") == "empty-state":
                texto = (resultado[0].text or "").strip()
                if "nenhuma" in texto.lower() or "oops" in texto.lower():
                    raise SemDividasEncontradas(texto or "Nenhuma divida encontrada")
        except TimeoutException:
            self.logger.log("Nenhuma linha de resultado apareceu para o CPF/CNPJ pesquisado.", "WARNING")

    def _localizar_linha_auto(self, auto_infracao: str):
        alvo = self._normalizar_texto_busca(auto_infracao)
        fim = time.time() + config.TIMEOUT_LOCALIZAR_AUTO
        primeira_tentativa = True

        while time.time() < fim:
            linhas = self.driver.find_elements(*config.SELETORES["linhas_tabela"])
            for linha in linhas:
                try:
                    texto_linha = self._normalizar_texto_busca(linha.text)
                    title_linha = self._normalizar_texto_busca(linha.get_attribute("innerText") or "")
                    html_linha = self._normalizar_texto_busca(linha.get_attribute("outerHTML") or "")
                    if alvo in texto_linha or alvo in title_linha or alvo in html_linha:
                        self.logger.log(f"Auto localizado na tabela: {auto_infracao}", "SUCCESS")
                        return linha
                except StaleElementReferenceException:
                    break

            if primeira_tentativa:
                self.logger.log(
                    f"Auto {auto_infracao}: ainda nao apareceu na tabela; aguardando atualizacao do portal...",
                    "WARNING",
                )
                primeira_tentativa = False
            time.sleep(0.5)

        return None

    def _selecionar_motivo(self, motivo_id: str):
        seletor = ("css selector", f"input[name='reason'][value='{motivo_id}']")
        radio = self.wait.until(EC.presence_of_element_located(seletor))
        self._rolar_para(radio)
        if self.operar_sem_foco:
            self.driver.execute_script("arguments[0].click();", radio)
            self.logger.log(f"Motivo selecionado: {motivo_id} - {config.MOTIVOS_BAIXA[motivo_id]}")
            return

        try:
            radio.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", radio)
        self.logger.log(f"Motivo selecionado: {motivo_id} - {config.MOTIVOS_BAIXA[motivo_id]}")

    def _aguardar_pos_envio(self, auto_infracao: str) -> str:
        mensagem = self._capturar_mensagem_temporaria()
        self._aguardar_modal_motivo_fechar()
        self._aguardar_tabela_estabilizar()
        if mensagem:
            return mensagem
        return f"Envio final realizado para o Auto {auto_infracao}."

    def _aguardar_tabela_estabilizar(self):
        self._aguardar_overlay()
        try:
            WebDriverWait(self.driver, config.TIMEOUT_PADRAO).until(
                EC.presence_of_all_elements_located(config.SELETORES["linhas_tabela"])
            )
        except TimeoutException:
            self.logger.log("Tabela nao reapareceu no tempo esperado apos envio.", "WARNING")
        time.sleep(config.PAUSA_APOS_ENVIO_REAL)

    def _aguardar_modal_motivo_fechar(self):
        try:
            WebDriverWait(self.driver, 10).until_not(
                EC.presence_of_element_located(("css selector", "input[name='reason']"))
            )
        except TimeoutException:
            self.logger.log("Modal de motivo nao desapareceu dentro do tempo esperado.", "WARNING")

    def _capturar_mensagem_temporaria(self) -> str:
        seletor = config.SELETORES.get("mensagem_temporaria")
        if not seletor:
            return ""
        try:
            elemento = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(seletor))
            return (elemento.text or "").strip()
        except TimeoutException:
            return ""

    def _capturar_mensagem(self) -> str:
        elemento = self._buscar("mensagem_resultado", clicavel=False)
        texto = (elemento.text or "").strip()
        return texto or "Operacao concluida, mas sem mensagem visivel."

    def _classificar_mensagem(self, mensagem: str) -> str:
        texto = (mensagem or "").lower()
        if any(sinal in texto for sinal in config.TEXTOS_SUCESSO):
            return "SUCESSO"
        if any(sinal in texto for sinal in config.TEXTOS_ERRO):
            return "ERRO"
        return "VERIFICAR"

    def _aguardar_overlay(self):
        seletor = config.SELETORES.get("overlay_carregando")
        if not seletor:
            return
        try:
            WebDriverWait(self.driver, 5).until(EC.invisibility_of_element_located(seletor))
        except TimeoutException:
            self.logger.log("Overlay de carregamento permaneceu visivel; seguindo com cautela.", "WARNING")

    def _rolar_para(self, elemento):
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)

    def _normalizar_texto_busca(self, texto: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", str(texto or "").upper())
