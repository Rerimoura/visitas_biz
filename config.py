# config.py — configurações do app

# Usuários permitidos: { "usuario": {"senha": ..., "divisao": ...} }
# Troque por hashes bcrypt em produção
USUARIOS = {
    "Diego Cesar": {"senha": "913574", "divisao": "Matheus"},
    "Karine": {"senha": "913692", "divisao": "Adriana"},
    "Luana": {"senha": "913077", "divisao": "Adriana"},
    "Matheus": {"senha": "913922", "divisao": "Matheus"},
    "Monica": {"senha": "913849", "divisao": "Adriana"},
    "Wellyngton": {"senha": "913596", "divisao": "Matheus"},
    "Fabiane": {"senha": "913381", "divisao": "Matheus"},
    "Barbara": {"senha": "913415", "divisao": "Adriana"},
    "Jean": {"senha": "913412", "divisao": "Matheus"},
    "Maria Tereza": {"senha": "913648", "divisao": "Matheus"},
    "Jose Guilherme": {"senha": "913124", "divisao": "Adriana"},
    "Rerisson": {"senha": "123456", "divisao": "Rerisson"},
}

# Supervisor responsável por cada divisão — recebe o alerta de
# vendedores que não registraram visita no dia (ver scripts/alerta_supervisor.py)
SUPERVISORES = {
    "Matheus": "rerisson@bizdistribuidora.com.br",
    "Adriana": "rerisson@bizdistribuidora.com.br",
    "Rerisson": "rerisson@bizdistribuidora.com.br",
}

# Marcas disponíveis para venda
MARCAS = [
    "Cargill",
    "Diageo",
    "Energizer/Rayovac",
    "Hypera",
    "Haleon",
    "Melitta",
    "Nivea",
    "Moet Chandon",
    "Reckitt Core",
    "BIC",
    "Vestacy",
    "Kimberly",
    "VCT",
]

# Motivos de não venda
MOTIVOS_NAO_VENDA = [
    "Comprador ausente",
    "Pediu retorno",
    "Avaliando proposta",
    "Recusou preço",
    "Sem interesse",
    "Estabelecimento fechado",
    "Outro",
]

# Nome da aba na planilha Google Sheets
SHEET_NAME = "Visitas"

# ID da pasta no Google Drive onde as fotos serão salvas
# Crie uma pasta no Drive, compartilhe com a service account e cole o ID aqui
# O ID está na URL: drive.google.com/drive/folders/ESTE_TRECHO_AQUI
DRIVE_PASTA_FOTOS_ID = ""  # preencher no secrets.toml (ver README)

# Colunas da planilha (ordem exata)
COLUNAS = [
    "timestamp_envio",
    "data_visita",
    "vendedor",
    "divisao",
    "ordem_cliente",
    "cnpj",
    "codigo_cliente",
    "vendeu",
    "motivo_nao_venda",
    "marcas_vendidas",
    "comentario",
    "fotos_cliente",
]
