# email_utils.py — envio de e-mail via SMTP, sem dependência do Streamlit
# (usado por auth.py e por scripts/alerta_supervisor.py)

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def enviar_email(smtp_config: dict, destinatario: str, assunto: str, corpo_html: str) -> None:
    """Envia um e-mail HTML via SMTP_SSL.

    smtp_config precisa ter: usuario, senha, smtp_server, smtp_port.
    Lança exceção em caso de falha — quem chama decide como tratar.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = smtp_config["usuario"]
    msg["To"] = destinatario
    msg.attach(MIMEText(corpo_html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        smtp_config["smtp_server"], int(smtp_config["smtp_port"]), context=context
    ) as server:
        server.login(smtp_config["usuario"], smtp_config["senha"])
        server.sendmail(smtp_config["usuario"], destinatario, msg.as_string())
