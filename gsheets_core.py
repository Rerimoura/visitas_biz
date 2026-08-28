# gsheets_core.py — acesso ao Google Sheets/Drive sem dependência do Streamlit
# Usado tanto por sheets.py (app, credenciais via st.secrets) quanto por
# scripts/alerta_supervisor.py (credenciais via variável de ambiente).

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def build_client(creds_dict: dict) -> gspread.Client:
    """Cria um cliente gspread autenticado a partir de um dict de credenciais
    de service account (o mesmo formato do JSON baixado no Google Cloud)."""
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def build_drive_service(creds_dict: dict):
    """Cria um cliente autenticado da Google Drive API."""
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def get_worksheet(client: gspread.Client, spreadsheet_id: str, sheet_name: str, colunas: list[str]):
    """Abre (ou cria, se não existir) a aba informada, garantindo o cabeçalho."""
    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        sheet.append_row(colunas)
        return sheet

    primeira = sheet.row_values(1)
    if primeira != colunas:
        sheet.insert_row(colunas, index=1)
    return sheet


def carregar_visitas_df(client: gspread.Client, spreadsheet_id: str, sheet_name: str) -> pd.DataFrame:
    """Carrega todas as visitas registradas como DataFrame."""
    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.worksheet(sheet_name)
    dados = sheet.get_all_records()
    return pd.DataFrame(dados)
