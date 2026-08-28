# pdf_utils.py — geração do PDF de resumo de visitas (enviado ao supervisor por e-mail)

import io
from datetime import datetime

from fpdf import FPDF
from PIL import Image

LARGURA_FOTO_MM = 55
LARGURA_FOTO_MAX_PX = 900


def _txt(valor: str) -> str:
    """Fonte core do fpdf2 (Helvetica) só cobre Latin-1 — troca qualquer
    caractere fora desse conjunto por um substituto em vez de quebrar o PDF."""
    return (valor or "").encode("latin-1", "replace").decode("latin-1")


def _fmt_data_br(data_iso: str) -> str:
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return data_iso


def _preparar_imagem(foto_bytes: bytes) -> io.BytesIO:
    """Redimensiona e recomprime a foto antes de embutir no PDF — fotos de
    celular na resolução original deixariam o e-mail pesado demais."""
    img = Image.open(io.BytesIO(foto_bytes))
    img = img.convert("RGB")
    if img.width > LARGURA_FOTO_MAX_PX:
        proporcao = LARGURA_FOTO_MAX_PX / img.width
        img = img.resize((LARGURA_FOTO_MAX_PX, int(img.height * proporcao)))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return buffer


def gerar_pdf_resumo(vendedor: str, divisao: str, data_visita: str, linhas: list[dict]) -> bytes:
    """Gera um PDF com o resumo das visitas de uma submissão (modo rápido ou dia completo)."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _txt("Relatorio de Visitas"), ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _txt(f"Vendedor: {vendedor.capitalize()}"), ln=True)
    pdf.cell(0, 7, _txt(f"Divisao: {divisao}"), ln=True)
    pdf.cell(0, 7, _txt(f"Data da visita: {data_visita}"), ln=True)
    pdf.cell(0, 7, _txt(f"Enviado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), ln=True)
    pdf.ln(3)

    vendidos = sum(1 for l in linhas if l["vendeu"] == "SIM")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(
        0, 8,
        _txt(f"Total de clientes: {len(linhas)}   |   Vendas: {vendidos}   |   Sem venda: {len(linhas) - vendidos}"),
        ln=True,
    )
    pdf.ln(2)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    for idx, linha in enumerate(linhas, start=1):
        cnpj = linha.get("cnpj", "").strip()
        codigo = linha.get("codigo_cliente", "").strip()
        identificacao = cnpj if cnpj else f"Codigo interno {codigo}"

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _txt(f"Cliente {idx} - {identificacao}"), ln=True)

        dados = linha.get("dados_cadastrais")
        if dados:
            nome = dados.get("nome_fantasia") or dados.get("razao_social")
            if nome:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, _txt(nome), ln=True)

            pdf.set_font("Helvetica", "", 9)
            if dados.get("razao_social") and dados.get("nome_fantasia"):
                pdf.cell(0, 5, _txt(f"Razao social: {dados['razao_social']}"), ln=True)

            cidade_bairro = " / ".join(x for x in [dados.get("cidade"), dados.get("bairro")] if x)
            if cidade_bairro or dados.get("endereco"):
                endereco_completo = dados.get("endereco") or ""
                if cidade_bairro:
                    endereco_completo = f"{endereco_completo} - {cidade_bairro}" if endereco_completo else cidade_bairro
                pdf.cell(0, 5, _txt(f"Endereco: {endereco_completo}"), ln=True)

            limite_fmt = ""
            if dados.get("limite") is not None:
                limite_fmt = f"R$ {dados['limite']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            linha_status = f"Situacao cadastral: {dados['status']}"
            if limite_fmt:
                linha_status += f"   |   Limite: {limite_fmt}"
            pdf.cell(0, 5, _txt(linha_status), ln=True)
            pdf.ln(1)
        elif cnpj or codigo:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 5, _txt("(cliente nao encontrado no cadastro)"), ln=True)

        historico = linha.get("historico") or {}
        historico_txt = []
        if historico.get("ultima_visita"):
            historico_txt.append(f"Ultima visita: {_fmt_data_br(historico['ultima_visita'])}")
        if historico.get("penultima_visita"):
            historico_txt.append(f"Penultima visita: {_fmt_data_br(historico['penultima_visita'])}")
        if historico.get("ultima_venda"):
            historico_txt.append(f"Ultima compra do cliente na BIZ: {_fmt_data_br(historico['ultima_venda'])}")
        if historico_txt:
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, _txt("   |   ".join(historico_txt)), ln=True)
            pdf.ln(1)

        pdf.set_font("Helvetica", "", 10)
        if linha["vendeu"] == "SIM":
            pdf.cell(0, 6, _txt("Status: Venda realizada"), ln=True)
            pdf.cell(0, 6, _txt(f"Marcas vendidas: {linha.get('marcas_vendidas') or '-'}"), ln=True)
        else:
            pdf.cell(0, 6, _txt("Status: Sem venda"), ln=True)
            pdf.cell(0, 6, _txt(f"Motivo: {linha.get('motivo_nao_venda') or '-'}"), ln=True)

        comentario = (linha.get("comentario") or "").strip()
        if comentario:
            pdf.multi_cell(0, 6, _txt(f"Comentario: {comentario}"))
            pdf.set_x(pdf.l_margin)

        if (linha.get("fotos_cliente") or "").strip():
            n_fotos = len(linha["fotos_cliente"].strip().split("\n"))
            pdf.cell(0, 6, _txt(f"Fotos anexadas na planilha: {n_fotos}"), ln=True)

        for foto_bytes in linha.get("fotos_bytes") or []:
            try:
                pdf.image(_preparar_imagem(foto_bytes), w=LARGURA_FOTO_MM)
                pdf.ln(2)
            except Exception:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, _txt("(nao foi possivel exibir uma das fotos)"), ln=True)

        pdf.ln(3)

    return bytes(pdf.output())
