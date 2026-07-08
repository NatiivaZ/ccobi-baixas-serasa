# Baixas SERASA

Automacao desktop para processar baixas no portal SERASA Experian a partir de Excel/CSV.

Para manutencao em outro computador ou por outro agente do Cursor, leia tambem:

- `DOCUMENTACAO_TECNICA.md`

## Como iniciar

Execute `iniciar.bat` ou rode:

```bat
python automacao_baixas_serasa.py
```

O `iniciar.bat` verifica Python, instala dependencias de `requirements.txt` e abre a interface.

## Planilha de entrada

A planilha deve conter pelo menos:

- `CPF/CNPJ`
- `Auto de Infracao` ou `Identificador do Debito`

O sistema normaliza CPF/CNPJ para apenas digitos e remove espacos do Auto de Infracao.

## Resultado

A planilha de resultado e criada automaticamente na mesma pasta da planilha de
entrada. O nome segue o formato:

```text
Resultado Baixas SERASA - Nome da Planilha - 27-04-2026 19h47min30s.xlsx
```

O Excel de saida inclui as colunas:

- `STATUS_BAIXA`
- `MENSAGEM_PORTAL`
- `TENTATIVAS`
- `DATA_PROCESSAMENTO`
- `OBSERVACAO`

## Fluxo automatizado

O navegador abre em guia normal. A interface possui campos de usuario/e-mail e
senha; a automacao tenta fazer login automaticamente. Se o portal pedir codigo
por e-mail, finalize essa etapa manualmente. Quando o produto aparecer, a
automacao pula o tour inicial, clica em `Acessar` e aguarda a tela de pesquisa.

Depois disso, para cada CPF/CNPJ da planilha, a automacao:

- pesquisa o documento no campo `debtorDocument`;
- baixa todos os autos daquele CPF/CNPJ antes de ir para o proximo;
- localiza o auto na tabela pelo texto do contrato;
- clica em `Excluir`;
- confirma em `Sim`;
- escolhe o motivo selecionado na interface;
- clica em `Enviar`;
- registra o resultado no Excel.

Se o portal mostrar `Nenhuma divida encontrada`, todos os Autos daquele CPF/CNPJ
sao marcados como `SEM_DIVIDA` e a automacao segue para o proximo CPF/CNPJ.

## Seletores principais

Os seletores principais ficam em `config_portal.py`:

- `URL_PORTAL`
- `campo_cpf_cnpj`
- `botao_pesquisar`
- `linhas_tabela`
- `sem_dividas`
- `botao_excluir_linha`
- `botao_confirmar_sim`
- `botao_voltar_motivo`
- `botao_enviar_motivo`
- `overlay_carregando`, se existir

Cada seletor deve ficar no formato:

```python
(By.ID, "idDoElemento")
```

ou:

```python
(By.XPATH, "//button[contains(., 'Baixar')]")
```

Os motivos de baixa tambem ficam em `config_portal.py`, no dicionario
`MOTIVOS_BAIXA`.

## Modo teste e modo real

Em `config_portal.py`:

```python
MODO_TESTE_SEM_ENVIAR = False
```

- `False`: modo real, clica no botao final `Enviar`.
- `True`: modo teste, seleciona o motivo e clica em `Voltar` sem efetivar a baixa.

Antes de alterar seletores ou fluxo do portal, recomenda-se testar com
`MODO_TESTE_SEM_ENVIAR = True`.

---

## Aviso legal (portfólio)

Código **proprietário** — Todos os direitos reservados.  
Publicado apenas para avaliação por recrutadores. **Uso em produção, redistribuição ou comercialização são proibidos** sem autorização escrita. Ver `LICENSE` e `NOTICE.md`.

Este repositório **não** contém dados pessoais reais (LGPD) nem credenciais. Amostras devem ser fictícias.


---

## Versao portfolio (codigo operacional omitido)

Este repositorio publico e uma **demonstracao de portfolio**.

- Estrutura, interfaces e documentacao: visiveis para recrutadores
- Fluxos criticos de integracao / automacao / regras sensiveis: **omitidos de proposito**
- Chamadas as partes omitidas levantam ``PortfolioOmittedError`` / ``OMITIDO PARA PORTFOLIO``
- Uso em producao, redistribuicao ou copia da logica operacional: **proibido** (ver ``LICENSE``)

O codigo operacional completo permanece apenas no ambiente do autor.
