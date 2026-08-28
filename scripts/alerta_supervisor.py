# scripts/alerta_supervisor.py — roda fora do Streamlit (via GitHub Actions agendado,
# à meia-noite). Verifica quais vendedores não registraram visita no dia que
# acabou de terminar e avisa o supervisor de cada divisão por e-mail.
#
# Importante: como o job roda À meia-noite (não antes dela), date.today() no
# momento da execução já é o dia NOVO — por isso o dia avaliado é sempre
# "ontem" em relação ao horário de execução, não hoje.
#
# Variáveis de ambiente necessárias:
#   GCP_SERVICE_ACCOUNT_JSON  — JSON da service account (mesmo conteúdo do secrets.toml)
#   SPREADSHEET_ID            — ID da planilha do Google Sheets
#   SMTP_SERVER, SMTP_PORT, SMTP_USUARIO, SMTP_SENHA — credenciais de envio de e-mail

import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gsheets_core
from config import SHEET_NAME, SUPERVISORES, USUARIOS
from email_utils import enviar_email


def vendedores_sem_visita(spreadsheet_id: str, dia: str) -> list[str]:
    creds_dict = json.loads(os.environ["GCP_SERVICE_ACCOUNT_JSON"])
    client = gsheets_core.build_client(creds_dict)
    df = gsheets_core.carregar_visitas_df(client, spreadsheet_id, SHEET_NAME)

    if df.empty or "vendedor" not in df.columns or "data_visita" not in df.columns:
        visitaram = set()
    else:
        visitaram = set(df.loc[df["data_visita"].astype(str) == dia, "vendedor"])

    return [nome for nome in USUARIOS if nome not in visitaram]


def montar_corpo_email(divisao: str, faltantes: list[str], dia: str) -> str:
    itens = "".join(f"<li style='padding:4px 0;color:#222;'>{nome.capitalize()}</li>" for nome in faltantes)
    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
      <div style="max-width:520px;margin:auto;background:#fff;border-radius:10px;
                  padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <h2 style="color:#5b6fff;margin-top:0;">📋 Vendedores sem visita registrada</h2>
        <p style="color:#444;">Divisão <strong>{divisao}</strong> — {dia}</p>
        <ul style="margin:16px 0;padding-left:20px;">{itens}</ul>
        <p style="color:#888;font-size:0.8rem;">Alerta automático do Relatório de Visitas, enviado à meia-noite.</p>
      </div>
    </body>
    </html>
    """


def main() -> None:
    dia_verificado = date.today() - timedelta(days=1)

    if dia_verificado.weekday() >= 5:  # 5=sábado, 6=domingo
        print(f"[{dia_verificado.isoformat()}] Fim de semana — sem checagem de visitas.")
        return

    dia = dia_verificado.isoformat()
    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    smtp_config = {
        "smtp_server": os.environ["SMTP_SERVER"],
        "smtp_port": os.environ["SMTP_PORT"],
        "usuario": os.environ["SMTP_USUARIO"],
        "senha": os.environ["SMTP_SENHA"],
    }

    faltantes = vendedores_sem_visita(spreadsheet_id, dia)
    if not faltantes:
        print(f"[{dia}] Todos os vendedores registraram visita. Nada a fazer.")
        return

    faltantes_por_divisao: dict[str, list[str]] = {}
    for nome in faltantes:
        divisao = USUARIOS[nome]["divisao"]
        faltantes_por_divisao.setdefault(divisao, []).append(nome)

    for divisao, nomes in faltantes_por_divisao.items():
        supervisor_email = SUPERVISORES.get(divisao)
        if not supervisor_email:
            print(f"[{dia}] Divisão '{divisao}' sem supervisor configurado — pulando. Faltantes: {nomes}")
            continue

        try:
            enviar_email(
                smtp_config=smtp_config,
                destinatario=supervisor_email,
                assunto=f"[Visitas App] {len(nomes)} vendedor(es) sem visita em {dia} — {divisao}",
                corpo_html=montar_corpo_email(divisao, nomes, dia),
            )
            print(f"[{dia}] Alerta enviado para {supervisor_email} ({divisao}): {nomes}")
        except Exception as e:
            print(f"[{dia}] Falha ao enviar alerta para {supervisor_email} ({divisao}): {e}")


if __name__ == "__main__":
    main()
