# 📋 App de Relatório de Visitas

App Streamlit para registro de visitas de vendedores, com gravação automática no Google Sheets.

---

## Stack

- **Frontend**: Streamlit
- **Backend de dados**: Google Sheets via gspread
- **Autenticação**: Login simples por usuário/senha (configurável em `config.py`)
- **Deploy**: Streamlit Community Cloud (gratuito)

---

## Setup local

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Google Sheets

#### 2a. Criar Service Account no Google Cloud
1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto (ou use um existente)
3. Ative as APIs: **Google Sheets API** e **Google Drive API**
4. Vá em "IAM e Admin" → "Service Accounts" → "Criar conta de serviço"
5. Baixe o arquivo JSON de credenciais

#### 2b. Criar a planilha
1. Crie uma planilha no Google Sheets
2. Compartilhe com o e-mail da service account (com permissão de Editor)
3. Copie o ID da planilha da URL:  
   `https://docs.google.com/spreadsheets/d/**ID_AQUI**/edit`

#### 2c. Configurar secrets
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Preencha `secrets.toml` com as credenciais do JSON baixado e o ID da planilha.

### 3. Rodar localmente

```bash
streamlit run app.py
```

---

## Configuração de usuários

Edite `config.py` → dicionário `USUARIOS`, associando cada vendedor a uma divisão:

```python
USUARIOS = {
    "matheus": {"senha": "senha123", "divisao": "Higiene"},
    "ana": {"senha": "senha456", "divisao": "Alimentos"},
}
```

> Em produção, substitua por hashes bcrypt + banco de dados.

E o e-mail do supervisor responsável por cada divisão, em `SUPERVISORES`:

```python
SUPERVISORES = {
    "Higiene": "supervisor.higiene@empresa.com",
    "Alimentos": "supervisor.alimentos@empresa.com",
}
```

---

## Alerta automático ao supervisor

Todo dia à meia-noite (horário de Brasília), um workflow do GitHub Actions
(`.github/workflows/alerta_supervisor.yml`) roda `scripts/alerta_supervisor.py`,
que verifica quais vendedores não registraram nenhuma visita no dia que
acabou de terminar e manda um e-mail ao supervisor de cada divisão com a
lista de quem falta.

O job roda todo dia (cron não filtra dia da semana), mas o script sempre
avalia o dia **anterior** à execução — porque rodando exatamente à meia-noite,
`date.today()` já é o dia novo — e pula silenciosamente sábado e domingo
(sem visita esperada, sem e-mail). Ou seja: o alerta de segunda-feira sai
terça de madrugada, o de sexta sai sábado de madrugada, e não sai nada no
domingo/segunda de madrugada (fim de semana).

Isso roda fora do Streamlit (o Community Cloud só executa código quando
alguém abre o app), então precisa do projeto num repositório GitHub com
os secrets abaixo cadastrados em **Settings → Secrets and variables → Actions**:

| Secret | Valor |
|---|---|
| `GCP_SERVICE_ACCOUNT_JSON` | Conteúdo do arquivo JSON baixado na etapa "Criar Service Account" (passo 2a acima) — cole o JSON inteiro como está |
| `SPREADSHEET_ID` | O mesmo de `secrets.toml` → `[google_sheets] spreadsheet_id` |
| `SMTP_SERVER` | O mesmo de `secrets.toml` → `[email] smtp_server` |
| `SMTP_PORT` | O mesmo de `secrets.toml` → `[email] smtp_port` |
| `SMTP_USUARIO` | O mesmo de `secrets.toml` → `[email] usuario` |
| `SMTP_SENHA` | O mesmo de `secrets.toml` → `[email] senha` |

Para testar sem esperar o horário agendado, vá em **Actions → Alerta ao
supervisor... → Run workflow** e dispare manualmente — lembrando que ele
sempre avalia o dia anterior à execução, então um teste disparado hoje
verifica quem faltou ontem, não hoje.

---

## Resumo em PDF por e-mail

A cada relatório enviado com sucesso (modo rápido ou fechamento de dia), o
app gera um PDF com o resumo das visitas daquele envio (`pdf_utils.py`) e
manda por e-mail ao supervisor da divisão do vendedor, usando o mesmo
`[email]` do `secrets.toml`. Se a divisão do vendedor não tiver supervisor
cadastrado em `SUPERVISORES` (`config.py`), o envio é simplesmente pulado.

Falha no envio do PDF não impede o relatório de ser salvo na planilha —
aparece só um aviso na tela.

Antes de montar o PDF, o app busca no Postgres (`clientes_db.py`, tabela
`clientes`) os dados cadastrais de cada cliente pelo CNPJ ou pelo código
interno (coluna `cliente`) e inclui no PDF: razão social, nome fantasia,
cidade, bairro, endereço, situação cadastral e limite. A situação é
calculada assim:

- `antecipado = 'A28'` → **Antecipado**
- senão, `situacao = 'A'` → **Liberado**
- qualquer outro caso → **Suspenso**

Se a consulta falhar ou o cliente não for encontrado, o PDF sai sem essa
seção — não bloqueia o envio.

Cada foto enviada pelo vendedor também é embutida no PDF (além de ir para
o Google Drive), redimensionada e recomprimida para no máximo 900px de
largura em JPEG — uma foto de celular de vários MB vira uns 150-250KB no
PDF, para não pesar demais no e-mail.

---

## Histórico do cliente ao preencher CNPJ/código

Assim que o vendedor preenche o CNPJ ou o código interno de um cliente, o
app mostra automaticamente (se houver), **e o mesmo histórico também vai
no PDF enviado ao supervisor**:

- **Última** e **penúltima visita** — datas distintas mais recentes desse
  cliente na planilha de visitas (`sheets.buscar_ultimas_visitas`), de
  qualquer vendedor.
- **Última compra do cliente na BIZ** — maior `data_emissao` em `vendas`
  (tabela do Postgres) para esse cliente, considerando só `tipo = 'V'`
  (exclui devoluções) e excluindo `vendedor = 2` (não é um vendedor real).
  O rótulo deixa explícito que é a última compra do cliente **na empresa
  como um todo**, não só com quem está preenchendo o relatório — a consulta
  nunca filtrou por vendedor. Se o cliente foi identificado por CNPJ, o
  código interno é resolvido primeiro via `clientes.cnpj`.

A consulta de última venda é cacheada por 3 minutos (`st.cache_data`), e
roda sobre um índice dedicado (`idx_vendas_cliente_tipo_data`, ver
`../Neon/migrate_postgree.py`) — o que era uma busca de ~0,2-0,5s virou
consulta de menos de 3ms.

---

## Deploy no Streamlit Community Cloud

1. Suba o código para um repositório GitHub (sem o `secrets.toml`)
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. "New app" → conecte o repositório → arquivo principal: `app.py`
4. Em "Advanced settings" → "Secrets": cole o conteúdo do `secrets.toml`
5. Deploy ✅

---

## Estrutura de arquivos

```
app_visitas/
├── app.py                              # App principal (formulário)
├── auth.py                             # Autenticação
├── sheets.py                           # Integração Google Sheets (camada Streamlit)
├── gsheets_core.py                     # Acesso ao Sheets/Drive sem dependência do Streamlit
├── email_utils.py                      # Envio de e-mail (SMTP)
├── pdf_utils.py                        # Geração do PDF de resumo de visitas
├── clientes_db.py                      # Consulta de dados cadastrais no Postgres
├── utils.py                            # Validadores (CNPJ)
├── config.py                           # Usuários, divisões, supervisores, marcas, motivos
├── scripts/alerta_supervisor.py        # Alerta diário de vendedores sem visita
├── .github/workflows/alerta_supervisor.yml
├── requirements.txt
└── .streamlit/
    └── secrets.toml    # Credenciais (não commitar)
```

---

## Próximos passos (v2)

- [ ] Login via Microsoft OAuth (conta corporativa)
- [ ] Migração para SharePoint via Graph API
- [ ] Tela de histórico de visitas por vendedor
- [ ] Dashboard de conversão integrado
- [ ] Hash de senha (bcrypt) + painel de administração de usuários
