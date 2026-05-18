"""Configuracoes do portal SERASA Experian."""

from selenium.webdriver.common.by import By


URL_PORTAL = "https://menu.serasaexperian.com.br/meus-produtos/login"

TIMEOUT_PADRAO = 30
TIMEOUT_LOGIN_MANUAL = 300
TIMEOUT_LOCALIZAR_AUTO = 20
TENTATIVAS_POR_ITEM = 3
CHECKPOINT_A_CADA = 1
PAUSA_APOS_ENVIO_REAL = 2.0

# Ajuste para True apenas se a tela nao exigir interacao visual.
HEADLESS = False

# O portal envia codigo por e-mail; por padrao o login fica assistido pelo usuario.
LOGIN_MANUAL_ASSISTIDO = True

# Modo de teste seguro: quando True, nao clica no botao final "Enviar".
MODO_TESTE_SEM_ENVIAR = False

# Mantem o Chrome visivel, mas usa preenchimentos/cliques por DOM sempre que
# possivel para permitir que outras janelas fiquem na frente.
OPERAR_SEM_DEPENDER_DO_FOCO = True

SELETORES = {
    "campo_usuario_login": (
        By.XPATH,
        "//input[not(@type='password') and ("
        "@type='email' or @type='text' or @type='tel' or not(@type)"
        ") and ("
        "contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'email') or "
        "contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'usuario') or "
        "contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'user') or "
        "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'email') or "
        "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'usuario') or "
        "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'user') or "
        "contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'email') or "
        "contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'usuario')"
        ")]",
    ),
    "campo_senha_login": (By.XPATH, "//input[@type='password']"),
    "botao_login": (
        By.XPATH,
        "//button[@type='submit' or contains(normalize-space(), 'Entrar') or "
        "contains(normalize-space(), 'Continuar') or contains(normalize-space(), 'Acessar')]",
    ),
    "botao_pular_tour": (By.XPATH, "//a[normalize-space()='Pular tour']"),
    "botao_acessar_produto": (By.XPATH, "//button[contains(@class, 'card-product__footer--accessBtn') and normalize-space()='Acessar'] | //button[normalize-space()='Acessar']"),
    "campo_cpf_cnpj": (By.ID, "debtorDocument"),
    "botao_pesquisar": (By.XPATH, "//button[@type='submit' and normalize-space()='Pesquisar']"),
    "linhas_tabela": (By.CSS_SELECTOR, "article table tbody tr, table tbody tr"),
    "sem_dividas": (By.CSS_SELECTOR, "[data-testid='empty-state']"),
    "botao_excluir_linha": (By.CSS_SELECTOR, "button[aria-label='Excluir']"),
    "botao_confirmar_sim": (By.XPATH, "//button[normalize-space()='Sim']"),
    "botao_voltar_motivo": (By.XPATH, "//button[@type='button' and normalize-space()='Voltar']"),
    "botao_enviar_motivo": (By.XPATH, "//form//button[@type='submit' and normalize-space()='Enviar' and not(@disabled)]"),
    "mensagem_temporaria": (
        By.CSS_SELECTOR,
        "[role='alert'], [data-testid*='toast'], [class*='toast'], [class*='Toast'], [class*='snackbar'], [class*='Snackbar']",
    ),
    "overlay_carregando": None,
}

MOTIVOS_BAIXA = {
    "1": "PAGAMENTO DA DIVIDA",
    "2": "RENEGOCIACAO DA DIVIDA",
    "3": "POR SOLICITACAO DO CLIENTE",
    "4": "ORDEM JUDICIAL",
    "5": "CORRECAO DO ENDERECO",
    "6": "ATUALIZACAO DO VALOR - VALORIZACAO",
    "7": "ATUALIZACAO DO VALOR - PAGAMENTO PARCIAL",
    "8": "ATUALIZACAO DA DATA",
    "9": "CORRECAO DO NOME",
    "10": "CORRECAO DO NUMERO DO CONTRATO",
    "11": "CORRECAO DE VARIOS VALORES (VALOR+DATA+ETC)",
    "12": "BAIXA POR PERDA DE CONTROLE DA BASE",
    "13": "MOTIVO NAO IDENTIFICADO",
    "14": "PONTUALIZACAO DA DIVIDA",
    "15": "BAIXA POR CONCESSAO DE CREDITO",
    "16": "INCORPORACAO/MUDANCA DE TITULARIDADE",
    "17": "COMUNICADO DEVOLVIDO DO CORREIO",
    "18": "CORRECAO DE DADOS DO COOBRIGADO/AVALISTA",
    "19": "RENEGOCIACAO DA DIVIDA POR ACORDO",
    "20": "PAGAMENTO DA DIVIDA POR DEPOSITO BANCARIO",
    "21": "ANALISE DE DOCUMENTOS",
    "22": "CORRECAO DE DADOS PELA LOJA/FILIAL",
    "23": "PGTO DA DIVIDA POR EMISSAO DE NOTA PROMISSORIA",
    "24": "ANALISE DE DOCUMENTO PELO SEGURO",
    "25": "DEVOLUCAO OU TROCA DE BEM FINANCIADO",
    "40": "BAIXA POR FRAUDE",
    "41": "BAIXA POR CALAMIDADE PUBLICA",
    "42": "BAIXA COMPULSORIA",
    "43": "BAIXA POR NEGOCIACAO",
    "44": "FALECIMENTO",
    "45": "CONTESTACAO",
}

TEXTOS_SUCESSO = (
    "sucesso",
    "baixado",
    "baixa realizada",
    "operacao realizada",
    "operacao efetuada",
)

TEXTOS_ERRO = (
    "erro",
    "falha",
    "nao encontrado",
    "nao foi possivel",
    "invalido",
)


def seletor_configurado(nome: str) -> bool:
    seletor = SELETORES.get(nome)
    return bool(seletor and len(seletor) == 2 and seletor[1])


def seletores_pendentes():
    obrigatorios = (
        "campo_cpf_cnpj",
        "botao_pesquisar",
        "linhas_tabela",
        "botao_excluir_linha",
        "botao_confirmar_sim",
        "botao_enviar_motivo",
    )
    return [nome for nome in obrigatorios if not seletor_configurado(nome)]
