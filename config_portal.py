"""PORTFOLIO — configuracao do portal omitida."""
from portfolio_omitted import omit

URL_PORTAL = "OMITIDO_PARA_PORTFOLIO"
HEADLESS = True


def seletor(nome: str):
    omit(f"seletor portal SERASA: {nome}")
