"""PORTFOLIO — automacao operacional omitida."""
from __future__ import annotations
from portfolio_omitted import omit


class AutomacaoBaixasSerasa:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def iniciar(self, *args, **kwargs):
        omit("AutomacaoBaixasSerasa.iniciar")

    def processar(self, *args, **kwargs):
        omit("AutomacaoBaixasSerasa.processar")

    def executar(self, *args, **kwargs):
        omit("AutomacaoBaixasSerasa.executar")

    def fechar(self, *args, **kwargs):
        omit("AutomacaoBaixasSerasa.fechar")

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            omit(f"AutomacaoBaixasSerasa.{name}")

        return _missing
