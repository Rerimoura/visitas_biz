# app.py — Relatório de Visitas (Streamlit)

import uuid
from datetime import date

import streamlit as st
from auth import requer_login, logout
from sheets import gravar_visitas, upload_foto_drive, verificar_visita_existente
from config import MARCAS, MOTIVOS_NAO_VENDA, USUARIOS
from utils import validar_cnpj

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Relatório de Visitas",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Inicializar tema ──────────────────────────────────────────────────────────
if "tema_escuro" not in st.session_state:
    st.session_state.tema_escuro = True

tema = st.session_state.tema_escuro

# ── Paleta de cores por tema ──────────────────────────────────────────────────
if tema:
    BG          = "#0f1117"
    CARD_BG     = "#1a1d27"
    BORDER      = "#2a2d3d"
    INPUT_BG    = "#12141e"
    TEXT        = "#e0e0e0"
    TEXT_SEC    = "#888"
    ACCENT      = "#5b6fff"
    ACCENT_HOV  = "#4455ee"
    DIVIDER     = "#2a2d3d"
    RESUMO_TXT  = "#c0c0c0"
    SUCCESS_BG  = "#1a1d27"
    INFO_BG     = "#1e2235"
    INFO_BORDER = "#3a3f5c"
    INFO_TXT    = "#a0aaff"
    TEMA_ICON   = "☀️"
    TEMA_LABEL  = "Tema claro"
else:
    BG          = "#f5f6fa"
    CARD_BG     = "#ffffff"
    BORDER      = "#dde1f0"
    INPUT_BG    = "#f0f2fb"
    TEXT        = "#1a1d2e"
    TEXT_SEC    = "#666"
    ACCENT      = "#4a5ce8"
    ACCENT_HOV  = "#3347d4"
    DIVIDER     = "#e0e3f0"
    RESUMO_TXT  = "#444"
    SUCCESS_BG  = "#f0f7ff"
    INFO_BG     = "#eef0fb"
    INFO_BORDER = "#c5caf0"
    INFO_TXT    = "#3347d4"
    TEMA_ICON   = "🌙"
    TEMA_LABEL  = "Tema escuro"

# ── CSS dinâmico ──────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* Fundo geral */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    section.main {{
        background: {BG} !important;
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}

    /* Texto geral */
    p, label, span, div, h1, h2, h3, h4 {{ color: {TEXT}; }}

    /* Header de cliente */
    .cliente-header {{
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: {ACCENT};
        text-transform: uppercase;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid {BORDER};
    }}

    /* Info box (dica CNPJ/código) */
    .info-box {{
        background: {INFO_BG};
        border: 1px solid {INFO_BORDER};
        border-left: 3px solid {ACCENT};
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        font-size: 0.82rem;
        color: {INFO_TXT};
        margin-bottom: 0.75rem;
    }}

    /* Botão primário */
    .stButton > button[kind="primary"] {{
        background: {ACCENT} !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #fff !important;
        transition: background 0.2s;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: {ACCENT_HOV} !important;
    }}

    /* Botões secundários */
    .stButton > button[kind="secondary"] {{
        border: 1px dashed {BORDER} !important;
        background: transparent !important;
        color: {TEXT_SEC} !important;
        border-radius: 8px !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: {ACCENT} !important;
        color: {ACCENT} !important;
    }}

    /* Inputs de texto e número */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        background: {INPUT_BG} !important;
        border-color: {BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT} !important;
    }}

    /* Selectbox — campo fechado */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] > div > div > div {{
        background: {INPUT_BG} !important;
        border-color: {BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT} !important;
    }}
    /* Selectbox — texto selecionado e placeholder */
    [data-testid="stSelectbox"] span,
    [data-testid="stSelectbox"] p {{
        color: {TEXT} !important;
    }}
    /* Selectbox — ícone chevron */
    [data-testid="stSelectbox"] svg {{
        fill: {TEXT_SEC} !important;
    }}
    /* Selectbox — lista dropdown (popover) */
    [data-testid="stSelectbox"] ul,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"] {{
        background: {INPUT_BG} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
    }}
    /* Selectbox — itens da lista */
    div[data-baseweb="menu"] li,
    div[data-baseweb="menu"] [role="option"] {{
        background: {INPUT_BG} !important;
        color: {TEXT} !important;
    }}
    /* Selectbox — item em hover */
    div[data-baseweb="menu"] li:hover,
    div[data-baseweb="menu"] [role="option"]:hover,
    div[data-baseweb="menu"] [aria-selected="true"] {{
        background: {BORDER} !important;
        color: {TEXT} !important;
    }}

    /* Multiselect — campo */
    [data-testid="stMultiSelect"] > div > div {{
        background: {INPUT_BG} !important;
        border-color: {BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT} !important;
    }}
    [data-testid="stMultiSelect"] span,
    [data-testid="stMultiSelect"] input {{
        color: {TEXT} !important;
        background: transparent !important;
    }}
    /* Multiselect — tags selecionadas */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background: {ACCENT} !important;
        border-radius: 6px !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
        color: #fff !important;
    }}
    /* Multiselect — lista dropdown */
    [data-testid="stMultiSelect"] ul,
    [data-baseweb="popover"] ul {{
        background: {INPUT_BG} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
    }}
    [data-baseweb="popover"] li,
    [data-baseweb="popover"] [role="option"] {{
        background: {INPUT_BG} !important;
        color: {TEXT} !important;
    }}
    [data-baseweb="popover"] li:hover,
    [data-baseweb="popover"] [role="option"]:hover {{
        background: {BORDER} !important;
        color: {TEXT} !important;
    }}

    /* Radio buttons — texto */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] span {{
        color: {TEXT} !important;
    }}

    /* Separador */
    hr {{ border-color: {DIVIDER} !important; }}

    /* Resumo */
    .resumo-row {{
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid {DIVIDER};
        font-size: 0.88rem;
        color: {RESUMO_TXT};
    }}
    .resumo-row:last-child {{ border-bottom: none; }}

    /* Ocultar menu e rodapé */
    #MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ── Autenticação ──────────────────────────────────────────────────────────────
requer_login()

vendedor = st.session_state["vendedor"]
divisao = USUARIOS[vendedor]["divisao"]


def novo_cliente() -> dict:
    return {"id": uuid.uuid4().hex[:8]}


# ── Inicializar estado ────────────────────────────────────────────────────────
if "clientes_rapido" not in st.session_state:
    st.session_state.clientes_rapido = [novo_cliente()]

if "clientes_dia" not in st.session_state:
    st.session_state.clientes_dia = [novo_cliente()]

if "modo_registro" not in st.session_state:
    st.session_state.modo_registro = "rapido"

if "enviado" not in st.session_state:
    st.session_state.enviado = False

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_tema, col_user = st.columns([3, 1, 1])
with col_title:
    st.markdown(f"<h2 style='color:{TEXT};margin:0;padding-top:0.3rem;'>📋 Relatório de Visitas</h2>", unsafe_allow_html=True)
with col_tema:
    if st.button(f"{TEMA_ICON} {TEMA_LABEL}", use_container_width=True):
        st.session_state.tema_escuro = not st.session_state.tema_escuro
        st.rerun()
with col_user:
    st.markdown(f"<p style='text-align:right;color:{TEXT_SEC};font-size:0.85rem;padding-top:0.6rem;'>👤 {vendedor}</p>", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        logout()

st.divider()

# ── Tela de sucesso ───────────────────────────────────────────────────────────
if st.session_state.enviado:
    st.success("✅ Relatório enviado com sucesso!")
    st.markdown(f"""
    <div style="background:{SUCCESS_BG};border:1px solid {BORDER};border-radius:12px;
                padding:1.5rem;text-align:center;margin-top:1rem;">
        <div style="font-size:3rem;">🎉</div>
        <h3 style="color:{TEXT};margin:0.5rem 0;">Tudo certo, {vendedor.capitalize()}!</h3>
        <p style="color:{TEXT_SEC};">Suas visitas foram gravadas na planilha.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Novo relatório", type="primary", use_container_width=True):
        st.session_state.clientes_rapido = [novo_cliente()]
        st.session_state.clientes_dia = [novo_cliente()]
        st.session_state.enviado = False
        st.rerun()
    st.stop()

# ── Modo de registro ────────────────────────────────────────────────────────────
modo_opcoes = {
    "rapido": "⚡ Visita rápida (1 cliente agora)",
    "dia": "📋 Fechar o dia (várias visitas)",
}
modo_registro = st.radio(
    "Como você quer registrar?",
    options=list(modo_opcoes.keys()),
    format_func=lambda k: modo_opcoes[k],
    horizontal=True,
    key="modo_registro",
)

st.divider()

# ── Data da visita ──────────────────────────────────────────────────────────────
data_visita = st.date_input("Data da visita", value=date.today())

st.divider()


# ── Bloco por cliente ─────────────────────────────────────────────────────────
def renderizar_bloco_cliente(cliente: dict, idx: int, mostrar_remover: bool) -> dict:
    cid = cliente["id"]

    col_header, col_remove = st.columns([5, 1]) if mostrar_remover else (st.container(), None)
    with col_header:
        st.markdown(f'<div class="cliente-header">Cliente {idx}</div>', unsafe_allow_html=True)
    if mostrar_remover:
        with col_remove:
            if st.button("🗑️", key=f"remover_{cid}", help="Remover este cliente"):
                # Só marca a remoção — mutar clientes_dia e chamar st.rerun() aqui
                # (no meio do loop) faria o Streamlit descartar o estado dos
                # widgets dos clientes seguintes, que ainda não foram desenhados
                # nesta execução do script.
                st.session_state.pending_remove_id = cid

    # Dica de identificação
    st.markdown(
        f'<div class="info-box">'
        f'💡 Preencha <strong>CNPJ</strong> ou <strong>Código Interno</strong> — apenas um é suficiente.'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_id1, col_id2 = st.columns(2)
    with col_id1:
        cnpj = st.text_input(
            "CNPJ",
            placeholder="00.000.000/0000-00  (opcional)",
            key=f"cnpj_{cid}",
        )
    with col_id2:
        codigo = st.text_input(
            "Código Interno",
            placeholder="Até 7 dígitos  (opcional)",
            max_chars=7,
            key=f"codigo_{cid}",
        )

    if cnpj.strip() and not validar_cnpj(cnpj):
        st.warning("CNPJ inválido — confira os números digitados.")

    if (cnpj.strip() or codigo.strip()) and verificar_visita_existente(
        vendedor, str(data_visita), cnpj, codigo
    ):
        st.warning("⚠️ Você já registrou esse cliente hoje. Confirme se quer mesmo lançar de novo.")

    vendeu = st.radio(
        "Vendeu?",
        options=["SIM", "NÃO"],
        index=1,
        horizontal=True,
        key=f"vendeu_{cid}",
    )

    motivo = ""
    marcas = []

    if vendeu == "NÃO":
        motivo = st.selectbox(
            "Motivo da não venda",
            options=[""] + MOTIVOS_NAO_VENDA,
            key=f"motivo_{cid}",
        )
    else:
        marcas = st.multiselect(
            "Marcas vendidas",
            options=MARCAS,
            key=f"marcas_{cid}",
        )

    comentario = st.text_area(
        "Comentário (opcional)",
        placeholder="Observações sobre o cliente...",
        key=f"comentario_{cid}",
        height=80,
    )

    fotos = st.file_uploader(
        "Fotos do cliente (opcional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"foto_{cid}",
    )

    st.markdown("---")

    return {
        "data_visita": str(data_visita),
        "vendedor": vendedor,
        "divisao": divisao,
        "ordem_cliente": idx,
        "cnpj": cnpj,
        "codigo_cliente": codigo,
        "vendeu": vendeu,
        "motivo_nao_venda": motivo,
        "marcas_vendidas": ", ".join(marcas),
        "comentario": comentario,
        "fotos_objeto": fotos,
    }


st.markdown(f"<h4 style='color:{TEXT};'>🏪 Cliente visitado</h4>" if modo_registro == "rapido"
            else f"<h4 style='color:{TEXT};'>🏪 Clientes visitados</h4>", unsafe_allow_html=True)

clientes_data = []

if modo_registro == "rapido":
    if len(st.session_state.clientes_rapido) != 1:
        st.session_state.clientes_rapido = [novo_cliente()]
    clientes_data.append(
        renderizar_bloco_cliente(st.session_state.clientes_rapido[0], 1, mostrar_remover=False)
    )
else:
    for i, cliente in enumerate(st.session_state.clientes_dia):
        idx = i + 1
        clientes_data.append(
            renderizar_bloco_cliente(
                cliente, idx, mostrar_remover=len(st.session_state.clientes_dia) > 1
            )
        )

    pending_remove_id = st.session_state.pop("pending_remove_id", None)
    if pending_remove_id is not None:
        st.session_state.clientes_dia = [
            c for c in st.session_state.clientes_dia if c["id"] != pending_remove_id
        ]
        st.rerun()

    # ── Botões de adicionar / remover cliente ────────────────────────────────
    col_add, col_remove = st.columns([3, 1])
    with col_add:
        if len(st.session_state.clientes_dia) < 10:
            if st.button("＋ Adicionar cliente", use_container_width=True):
                st.session_state.clientes_dia.append(novo_cliente())
                st.rerun()
    with col_remove:
        if len(st.session_state.clientes_dia) > 1:
            if st.button("Remover último", use_container_width=True):
                st.session_state.clientes_dia.pop()
                st.rerun()

    st.divider()

    # ── Resumo antes do envio ─────────────────────────────────────────────────
    with st.expander("📊 Ver resumo antes de enviar", expanded=False):
        ativos = [c for c in clientes_data if (c["cnpj"].strip() or c["codigo_cliente"].strip())]
        total_ativos = len(ativos)
        vendidos = sum(1 for c in ativos if c["vendeu"] == "SIM")
        nao_vendidos = total_ativos - vendidos

        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Clientes visitados", total_ativos)
        col_r2.metric("✅ Vendas", vendidos)
        col_r3.metric("❌ Não vendas", nao_vendidos)

        st.markdown("")
        for c in ativos:
            cnpj_val = c["cnpj"].strip()
            cod_val  = c["codigo_cliente"].strip()
            if cnpj_val and cod_val:
                label = f"{cnpj_val} ({cod_val})"
            elif cnpj_val:
                label = cnpj_val
            else:
                label = f"Cód: {cod_val}"

            status  = "✅ SIM" if c["vendeu"] == "SIM" else "❌ NÃO"
            detalhe = c["marcas_vendidas"] if c["vendeu"] == "SIM" else c["motivo_nao_venda"]
            st.markdown(
                f'<div class="resumo-row">'
                f'<span>{label}</span><span>{status}</span>'
                f'<span style="color:{TEXT_SEC}">{detalhe}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

if modo_registro == "rapido":
    st.divider()

# ── Validações ────────────────────────────────────────────────────────────────
erros = []

clientes_preenchidos = [c for c in clientes_data if (c["cnpj"].strip() or c["codigo_cliente"].strip())]
if not clientes_preenchidos:
    erros.append("Preencha o CNPJ ou o Código Interno de pelo menos um cliente.")

for c in clientes_data:
    if not (c["cnpj"].strip() or c["codigo_cliente"].strip()):
        continue
    cod = c["codigo_cliente"].strip()
    if cod and not cod.isdigit():
        erros.append(f"O código do cliente {c['ordem_cliente']} deve conter apenas números (até 7 dígitos).")
    if c["cnpj"].strip() and not validar_cnpj(c["cnpj"]):
        erros.append(f"O CNPJ do cliente {c['ordem_cliente']} é inválido.")
    if c["vendeu"] == "NÃO" and not c["motivo_nao_venda"]:
        erros.append(f"Selecione o motivo de não venda do cliente {c['ordem_cliente']}.")

if erros:
    for erro in erros:
        st.warning(erro)

# ── Envio ─────────────────────────────────────────────────────────────────────
st.markdown("")
enviar = st.button(
    "📤 Enviar relatório",
    type="primary",
    use_container_width=True,
    disabled=bool(erros),
)

if enviar:
    import os
    from datetime import datetime

    linhas = [c.copy() for c in clientes_data if (c["cnpj"].strip() or c["codigo_cliente"].strip())]

    with st.spinner("Enviando fotos e gravando no Google Sheets..."):
        for c in linhas:
            fotos_obj = c.pop("fotos_objeto", None) or []
            links = []
            for n, foto_obj in enumerate(fotos_obj, start=1):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = os.path.splitext(foto_obj.name)[1] or ".jpg"
                safe_filename = f"{ts}_{c['vendedor']}_cliente_{c['ordem_cliente']}_{n}{ext}"
                safe_filename = "".join(ch for ch in safe_filename if ch.isalnum() or ch in "._-")
                foto_bytes = foto_obj.getvalue()
                link = upload_foto_drive(foto_bytes, safe_filename, foto_obj.type or "image/jpeg")
                if link:
                    links.append(link)
            c["fotos_cliente"] = "\n".join(links)

        sucesso = gravar_visitas(linhas)

    if sucesso:
        st.session_state.enviado = True
        st.rerun()
