# utils.py — validadores e helpers gerais


def validar_cnpj(cnpj: str) -> bool:
    """Valida CNPJ pelo algoritmo padrão de dígitos verificadores.
    Aceita entrada com ou sem pontuação (00.000.000/0000-00)."""
    digitos = "".join(ch for ch in cnpj if ch.isdigit())

    if len(digitos) != 14 or digitos == digitos[0] * 14:
        return False

    def calcular_dv(base: str, pesos: list[int]) -> int:
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = calcular_dv(digitos[:12], pesos1)

    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv2 = calcular_dv(digitos[:12] + str(dv1), pesos2)

    return digitos[-2:] == f"{dv1}{dv2}"
