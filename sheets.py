# sheets.py — leitura e escrita no Google Sheets via gspread (camada Streamlit)

import io
from datetime import datetime

import pandas as pd
import streamlit as st
from googleapiclient.http import MediaIoBaseUpload

import gsheets_core
from config import COLUNAS, SHEET_NAME


@st.cache_resource
def get_client():
    """Retorna cliente gspread autenticado via service account."""
    return gsheets_core.build_client(st.secrets["gcp_service_account"])


@st.cache_resource
def get_drive_service():
    """Retorna cliente autenticado da Google Drive API."""
    return gsheets_core.build_drive_service(st.secrets["gcp_service_account"])


def upload_foto_drive(foto_bytes: bytes, filename: str, mimetype: str = "image/jpeg") -> str:
    """
    Faz upload de uma foto para a pasta do Google Drive configurada nos secrets.
    Retorna o link público de visualização, ou string vazia se falhar.
    """
    try:
        pasta_id = st.secrets["google_drive"]["pasta_fotos_id"]
        service = get_drive_service()

        file_metadata = {
            "name": filename,
            "parents": [pasta_id],
        }
        media = MediaIoBaseUpload(
            io.BytesIO(foto_bytes),
            mimetype=mimetype,
            resumable=False,
        )
        arquivo = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()

        file_id = arquivo.get("id")

        # Tornar o arquivo público (leitura para qualquer pessoa com o link)
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        return f"https://drive.google.com/file/d/{file_id}/view"

    except Exception as e:
        st.warning(f"Foto não pôde ser enviada: {e}")
        return ""


def get_sheet():
    client = get_client()
    spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
    return gsheets_core.get_worksheet(client, spreadsheet_id, SHEET_NAME, COLUNAS)


def gravar_visitas(linhas: list[dict]) -> bool:
    """
    Recebe lista de dicts com os dados de cada cliente e grava no Sheets.
    Retorna True se sucesso, False se erro.
    """
    try:
        sheet = get_sheet()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows_to_append = []
        for linha in linhas:
            linha["timestamp_envio"] = timestamp
            row = [str(linha.get(col, "")) for col in COLUNAS]
            rows_to_append.append(row)
        sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        carregar_visitas.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao gravar no Google Sheets: {e}")
        return False


@st.cache_data(ttl=120)
def carregar_visitas() -> pd.DataFrame:
    """Carrega todas as visitas como DataFrame (cache de 2min para não bater
    na API do Sheets a cada interação do usuário)."""
    try:
        client = get_client()
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        return gsheets_core.carregar_visitas_df(client, spreadsheet_id, SHEET_NAME)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


def verificar_visita_existente(vendedor: str, data_visita: str, cnpj: str, codigo: str) -> bool:
    """Verifica se já existe uma visita registrada para esse vendedor,
    nessa data, para o mesmo cliente (por CNPJ ou código interno)."""
    df = carregar_visitas()
    if df.empty:
        return False

    cnpj = cnpj.strip()
    codigo = codigo.strip()
    if not cnpj and not codigo:
        return False

    filtro = (df["vendedor"] == vendedor) & (df["data_visita"].astype(str) == str(data_visita))
    if cnpj:
        filtro &= df["cnpj"].astype(str).str.strip() == cnpj
    else:
        filtro &= df["codigo_cliente"].astype(str).str.strip() == codigo

    return bool(filtro.any())
