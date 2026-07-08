"""PORTFOLIO — automacao operacional omitida."""
from __future__ import annotations
from portfolio_omitted import omit


class PortalSerasa:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def iniciar(self, *args, **kwargs):
        omit("PortalSerasa.iniciar")

    def abrir_portal(self, *args, **kwargs):
        omit("PortalSerasa.abrir_portal")

    def realizar_login_automatico(self, *args, **kwargs):
        omit("PortalSerasa.realizar_login_automatico")

    def aguardar_login_manual(self, *args, **kwargs):
        omit("PortalSerasa.aguardar_login_manual")

    def aguardar_tela_pesquisa(self, *args, **kwargs):
        omit("PortalSerasa.aguardar_tela_pesquisa")

    def pesquisar_cpf_cnpj(self, *args, **kwargs):
        omit("PortalSerasa.pesquisar_cpf_cnpj")

    def processar_baixa(self, *args, **kwargs):
        omit("PortalSerasa.processar_baixa")

    def processar_auto_na_tela(self, *args, **kwargs):
        omit("PortalSerasa.processar_auto_na_tela")

    def fechar(self, *args, **kwargs):
        omit("PortalSerasa.fechar")

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            omit(f"PortalSerasa.{name}")

        return _missing
