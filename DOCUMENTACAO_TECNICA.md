# Documentacao Tecnica - Baixas SERASA

Esta pasta contem uma automacao desktop em Python para realizar baixas no portal
SERASA Experian a partir de uma planilha Excel/CSV.

Este documento foi escrito para facilitar manutencao em outro computador ou por
outro agente do Cursor.

## Estado Atual

- Navegador: Chrome em guia normal.
- Login: tentativa automatica por usuario/e-mail e senha informados na interface.
- Codigo por e-mail: se o portal pedir, o usuario informa manualmente e a automacao continua.
- Tour inicial: se aparecer, a automacao clica em `Pular tour`.
- Modo real: `MODO_TESTE_SEM_ENVIAR = False`, portanto a automacao clica em `Enviar`.
- Modo sem foco: ativo. O Chrome fica visivel, mas a automacao tenta operar por DOM/JavaScript para permitir que outras janelas fiquem na frente.
- Resultado: planilha Excel criada automaticamente com status de cada linha.

## Arquivos Principais

- `automacao_baixas_serasa.py`: interface Tkinter, validacoes iniciais, loop por CPF/CNPJ, progresso, logs e exportacao.
- `portal_serasa.py`: automacao Selenium do portal, login, clique em `Acessar`, pesquisa, baixa dos autos e tratamento de mensagens.
- `config_portal.py`: URL, timeouts, seletores do portal, modo teste e lista de motivos.
- `excel_utils.py`: leitura da planilha, deteccao de colunas, normalizacao de CPF/CNPJ e Auto, exportacao formatada.
- `logging_utils.py`: logger para tela, console e arquivo.
- `requirements.txt`: dependencias Python.
- `iniciar.bat`: script de execucao no Windows.

## Fluxo Funcional

1. Usuario seleciona planilha de entrada.
2. Sistema gera automaticamente o caminho da planilha de resultado.
3. Usuario escolhe o motivo da baixa.
4. Usuario informa usuario/e-mail e senha do SERASA na interface.
5. Automacao abre `https://menu.serasaexperian.com.br/meus-produtos/login`.
6. Automacao tenta preencher login automaticamente.
7. Se houver codigo por e-mail, usuario conclui manualmente.
8. Se aparecer tour inicial, automacao clica em `Pular tour`.
9. Automacao clica no produto pelo botao `Acessar`.
10. Automacao aguarda o campo `debtorDocument`.
11. Para cada CPF/CNPJ da planilha:
    - pesquisa o documento;
    - se aparecer `Nenhuma divida encontrada`, marca o grupo como `SEM_DIVIDA`;
    - se encontrar tabela, baixa todos os Autos daquele CPF/CNPJ antes de seguir.
12. Para cada Auto:
    - localiza a linha da tabela pelo texto do contrato/Auto;
    - clica em `Excluir`;
    - clica em `Sim`;
    - seleciona o motivo escolhido na interface;
    - clica em `Enviar` quando modo real estiver ativo;
    - aguarda a tabela estabilizar antes do proximo Auto.

## Planilha de Entrada

A primeira linha precisa ser cabecalho. A automacao detecta automaticamente
colunas com nomes parecidos.

Colunas aceitas para CPF/CNPJ:

- `CPF/CNPJ`
- `CPF CNPJ`
- `CPF`
- `CNPJ`
- `Documento`
- `Contribuinte`

Colunas aceitas para Auto:

- `Auto de Infracao`
- `Auto de Infração`
- `Auto Infracao`
- `Identificador do Debito`
- `Identificador do Débito`
- `Numero do Auto`
- `Número do Auto`
- `Auto`

Pode haver outras colunas na planilha.

## Resultado Gerado

O arquivo e salvo automaticamente com nome semelhante a:

```text
Resultado Baixas SERASA - Nome da Planilha - 27-04-2026 20h44min25s.xlsx
```

Colunas adicionadas no resultado:

- `STATUS_BAIXA`
- `MENSAGEM_PORTAL`
- `TENTATIVAS`
- `DATA_PROCESSAMENTO`
- `OBSERVACAO`

Status relevantes:

- `SUCESSO`: envio final realizado.
- `NAO_LOCALIZADO`: CPF/CNPJ encontrado, mas Auto nao estava na tabela.
- `SEM_DIVIDA`: portal retornou "Nenhuma divida encontrada".
- `ERRO`: erro inesperado ao pesquisar ou processar.
- `TESTE_SEM_ENVIO`: usado somente quando o modo teste esta ativo.
- `IGNORADO`: linha da planilha sem CPF/CNPJ ou Auto valido.
- `PARADO`: execucao interrompida pelo usuario.

## Configuracoes Importantes

Arquivo: `config_portal.py`.

```python
MODO_TESTE_SEM_ENVIAR = False
```

- `False`: modo real, clica em `Enviar`.
- `True`: modo teste, seleciona motivo, nao envia, clica em `Voltar`.

```python
OPERAR_SEM_DEPENDER_DO_FOCO = True
```

- Mantem o Chrome visivel, mas usa eventos DOM/JavaScript sempre que possivel.
- Permite deixar outra janela na frente do navegador.

```python
TIMEOUT_LOCALIZAR_AUTO = 20
PAUSA_APOS_ENVIO_REAL = 2.0
```

- Ajudam a evitar falso `NAO_LOCALIZADO` enquanto a tabela atualiza apos uma baixa.

## Fallback: Login Manual e Continuar do Botao Acessar

Se em outro computador o portal continuar pedindo codigo por e-mail, mesmo em
guia normal, pode ser melhor remover/ignorar a tentativa de login automatico e
fazer a automacao continuar somente depois que o usuario ja estiver logado.

Objetivo desse fallback:

1. Usuario abre a automacao.
2. Usuario clica em `Iniciar`.
3. Chrome abre no portal.
4. Usuario faz login manualmente, incluindo codigo por e-mail.
5. Quando chegar na tela do menu/produtos, a automacao continua sozinha a partir
   de `Pular tour` e `Acessar`.

Alteracoes recomendadas:

1. Em `automacao_baixas_serasa.py`, no metodo `_executar_automacao`, remover ou
   comentar a chamada:

```python
self.portal.realizar_login_automatico(
    self.usuario_login.get().strip(),
    self.senha_login.get(),
)
```

2. Manter a chamada seguinte, pois ela ja aguarda o usuario terminar login e
   depois procura `Pular tour`, `Acessar` e a tela de pesquisa:

```python
self.portal.aguardar_login_manual()
```

3. Opcionalmente, esconder da interface os campos `Usuario/E-mail` e `Senha`,
   removendo ou comentando a criacao do `card_login` em `_montar_tela`.

Trecho relacionado em `automacao_baixas_serasa.py`:

```python
card_login = tk.LabelFrame(...)
self._linha_login(card_login, "Usuario/E-mail", self.usuario_login)
self._linha_login(card_login, "Senha", self.senha_login, show="*")
```

Se quiser manter os campos para uso futuro, nao precisa remover. Basta deixar em
branco; a automacao registra que as credenciais nao foram preenchidas e segue
para login manual.

Ponto principal: o metodo `aguardar_login_manual()` em `portal_serasa.py` e o
responsavel por continuar depois do login. Ele faz:

- aguarda o usuario concluir login/codigo se necessario;
- tenta clicar em `Pular tour` se aparecer;
- procura e clica no botao `Acessar`;
- aguarda o campo `debtorDocument`.

Portanto, se o login automatico atrapalhar, nao refatore o fluxo todo. Apenas
ignore/remova `realizar_login_automatico()` e continue usando
`aguardar_login_manual()`.

## Seletores do Portal

Os seletores ficam em `SELETORES` dentro de `config_portal.py`.

Seletores mais sensiveis:

- `campo_usuario_login`
- `campo_senha_login`
- `botao_login`
- `botao_pular_tour`
- `botao_acessar_produto`
- `campo_cpf_cnpj`
- `botao_pesquisar`
- `linhas_tabela`
- `sem_dividas`
- `botao_excluir_linha`
- `botao_confirmar_sim`
- `botao_voltar_motivo`
- `botao_enviar_motivo`
- `mensagem_temporaria`

Se o layout do portal mudar, altere primeiro esses seletores.

Preferencia de seletores:

1. `By.ID` quando o ID for estavel.
2. `By.CSS_SELECTOR` com atributos estaveis (`data-testid`, `aria-label`, `name`).
3. `By.XPATH` por texto visivel quando nao houver alternativa melhor.

Evite XPath absoluto do tipo `/html/body/div/...`, pois quebra facilmente.

## Motivos de Baixa

Os motivos ficam no dicionario `MOTIVOS_BAIXA` em `config_portal.py`.

O valor selecionado na interface e usado para clicar no radio:

```css
input[name='reason'][value='<codigo>']
```

Exemplo:

- `3 - POR SOLICITACAO DO CLIENTE`
- `4 - ORDEM JUDICIAL`

## Logs e Auditoria

Logs sao exibidos na interface e gravados em:

```text
Baixas SERASA/logs/
```

A partir do momento em que um Auto e localizado, os logs registram:

- Auto localizado.
- Procurando botao `Excluir`.
- Clicando em `Excluir`.
- Confirmando em `Sim`.
- Selecionando motivo.
- Clicando em `Enviar` ou `Voltar` no modo teste.
- Resultado da linha.

Esses logs sao a principal forma de validar se o fluxo clicou em todos os botoes.

## Como Rodar em Outro Computador

1. Copie a pasta `Baixas SERASA` inteira.
2. Instale Python 3.11+ ou use o Python disponivel.
3. Execute `iniciar.bat`.
4. O script instala/atualiza as dependencias de `requirements.txt`.
5. Preencha login, senha, planilha e motivo na interface.
6. Execute.

Observacao: nao copie credenciais em arquivos. A senha deve ser digitada na
interface a cada execucao.

## Cuidados Para Outro Cursor/Agente

- Nao salvar usuario/senha em arquivo.
- Nao logar senha.
- Nao remover os logs detalhados do fluxo de baixa sem necessidade.
- Antes de mudar seletores, testar com `MODO_TESTE_SEM_ENVIAR = True`.
- Se mudar fluxo real do portal, manter a ordem:
  `Pesquisar` -> `Excluir` -> `Sim` -> `Motivo` -> `Enviar`.
- Se houver novo pop-up no portal, adicionar etapa opcional antes de `Acessar` ou antes da pesquisa.
- Se aparecer falso `NAO_LOCALIZADO`, aumentar `TIMEOUT_LOCALIZAR_AUTO` ou `PAUSA_APOS_ENVIO_REAL`.

## Comandos Uteis

Validar sintaxe:

```bat
python -m py_compile automacao_baixas_serasa.py portal_serasa.py excel_utils.py logging_utils.py config_portal.py
```

Executar:

```bat
python automacao_baixas_serasa.py
```

Instalar dependencias manualmente:

```bat
python -m pip install -r requirements.txt
```

## Historico de Decisoes

- A automacao foi testada primeiro em modo seguro.
- No modo teste, ela clicava em `Voltar` apos selecionar motivo para nao baixar por acidente.
- Apos validacao, `MODO_TESTE_SEM_ENVIAR` foi alterado para `False`.
- A guia anonima foi removida porque aumentava a chance de pedir codigo por e-mail.
- O navegador permanece visivel em guia normal.
- A automacao opera sem depender do foco para o usuario poder usar o PC durante a execucao.
