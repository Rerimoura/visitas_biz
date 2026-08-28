# email_utils.py — envio de e-mail via SMTP, sem dependência do Streamlit
# (usado por auth.py, app.py e por scripts/alerta_supervisor.py)

import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def enviar_email(
    smtp_config: dict,
    destinatario: str,
    assunto: str,
    corpo_html: str,
    anexos: list[tuple[str, bytes]] | None = None,
) -> None:
    """Envia um e-mail HTML via SMTP_SSL, com anexos PDF opcionais.

    smtp_config precisa ter: usuario, senha, smtp_server, smtp_port.
    anexos: lista de (nome_do_arquivo, conteudo_em_bytes).
    Lança exceção em caso de falha — quem chama decide como tratar.
    """
    if anexos:
        msg = MIMEMultipart("mixed")
        corpo = MIMEMultipart("alternative")
        corpo.attach(MIMEText(corpo_html, "html"))
        msg.attach(corpo)
        for nome_arquivo, conteudo in anexos:
            parte = MIMEApplication(conteudo, _subtype="pdf")
            parte.add_header("Content-Disposition", "attachment", filename=nome_arquivo)
            msg.attach(parte)
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(corpo_html, "html"))

    msg["Subject"] = assunto
    msg["From"] = smtp_config["usuario"]
    msg["To"] = destinatario

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        smtp_config["smtp_server"], int(smtp_config["smtp_port"]), context=context
    ) as server:
        server.login(smtp_config["usuario"], smtp_config["senha"])
        server.sendmail(smtp_config["usuario"], destinatario, msg.as_string())
