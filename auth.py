# auth.py — autenticação simples por usuário/senha

import streamlit as st
from config import USUARIOS
from email_utils import enviar_email


def check_login(usuario: str, senha: str) -> bool:
    dados = USUARIOS.get(usuario)
    return dados is not None and dados["senha"] == senha


def enviar_email_solicitacao(nome: str, divisao: str, senha_sugerida: str) -> bool:
    """Envia e-mail de solicitação de acesso para o administrador."""
    try:
        cfg = st.secrets["email"]

        corpo_html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
          <div style="max-width:520px;margin:auto;background:#fff;border-radius:10px;
                      padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <h2 style="color:#5b6fff;margin-top:0;">📋 Nova Solicitação de Acesso</h2>
            <p style="color:#444;">Um novo vendedor solicitou acesso ao <strong>Relatório de Visitas</strong>.</p>
            <table style="width:100%;border-collapse:collapse;margin:20px 0;">
              <tr style="background:#f8f9ff;">
                <td style="padding:10px 14px;color:#888;font-size:0.85rem;width:40%;">👤 Nome</td>
                <td style="padding:10px 14px;font-weight:600;color:#222;">{nome}</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;color:#888;font-size:0.85rem;">🏢 Divisão</td>
                <td style="padding:10px 14px;font-weight:600;color:#222;">{divisao}</td>
              </tr>
              <tr style="background:#f8f9ff;">
                <td style="padding:10px 14px;color:#888;font-size:0.85rem;">🔑 Senha sugerida</td>
                <td style="padding:10px 14px;font-weight:600;color:#222;">{senha_sugerida}</td>
              </tr>
            </table>
            <p style="color:#888;font-size:0.8rem;">
              Para aprovar, adicione o usuário em <code>config.py</code> → dicionário <code>USUARIOS</code>.
            </p>
          </div>
        </body>
        </html>
        """

        enviar_email(
            smtp_config=cfg,
            destinatario=cfg["destinatario"],
            assunto=f"[Visitas App] Solicitação de Acesso — {nome}",
            corpo_html=corpo_html,
        )

        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False


def tela_login():
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="font-size:1.6rem; font-weight:700; margin-bottom:0.25rem;">📋 Relatório de Visitas</h1>
        <p style="color:#888; font-size:0.9rem;">Entre com suas credenciais para continuar</p>
    </div>
    """, unsafe_allow_html=True)

    # Alterna entre Login e Solicitar Acesso
    if "modo_login" not in st.session_state:
        st.session_state.modo_login = "login"

    tab_login, tab_solicitar = st.tabs(["🔑 Entrar", "📩 Solicitar Acesso"])

    # ── Aba de Login ──────────────────────────────────────────────────────────
    with tab_login:
        with st.form("form_login"):
            usuario = st.selectbox(
                "Usuário",
                options=[""] + list(USUARIOS.keys()),
                format_func=lambda x: "Selecione seu usuário..." if x == "" else x.capitalize(),
            )
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            if not usuario:
                st.error("Selecione um usuário.")
            elif check_login(usuario, senha):
                st.session_state["logado"] = True
                st.session_state["vendedor"] = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    # ── Aba de Solicitação de Acesso ──────────────────────────────────────────
    with tab_solicitar:
        st.markdown(
            "<p style='color:#888;font-size:0.88rem;margin-bottom:1rem;'>"
            "Preencha os dados abaixo. O administrador receberá um e-mail e criará seu acesso.</p>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("solicitacao_enviada"):
            st.success("✅ Solicitação enviada! Aguarde o administrador criar seu acesso.")
            if st.button("Enviar outra solicitação", use_container_width=True):
                del st.session_state["solicitacao_enviada"]
                st.rerun()
        else:
            with st.form("form_solicitar"):
                nome_sol = st.text_input("Nome completo", placeholder="Ex: João Silva")
                divisao_sol = st.text_input("Divisão / Setor", placeholder="Ex: Higiene, Alimentos, Bebidas...")
                senha_sol = st.text_input(
                    "Senha sugerida",
                    type="password",
                    placeholder="Escolha uma senha",
                )
                senha_conf = st.text_input(
                    "Confirme a senha",
                    type="password",
                    placeholder="Repita a senha",
                )
                enviar_sol = st.form_submit_button("📩 Enviar Solicitação", use_container_width=True)

            if enviar_sol:
                if not nome_sol.strip():
                    st.error("Informe seu nome completo.")
                elif not divisao_sol.strip():
                    st.error("Informe sua divisão.")
                elif not senha_sol:
                    st.error("Defina uma senha sugerida.")
                elif senha_sol != senha_conf:
                    st.error("As senhas não coincidem.")
                else:
                    with st.spinner("Enviando solicitação..."):
                        ok = enviar_email_solicitacao(
                            nome=nome_sol.strip(),
                            divisao=divisao_sol.strip(),
                            senha_sugerida=senha_sol,
                        )
                    if ok:
                        st.session_state["solicitacao_enviada"] = True
                        st.rerun()


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def requer_login():
    """Chame no topo de cada página para garantir autenticação."""
    if not st.session_state.get("logado"):
        tela_login()
        st.stop()
