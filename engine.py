# -*- coding: utf-8 -*-
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional


MONEY_QUANT = Decimal("0.01")
TARIFA_OPERACIONAL_ESCOLTA = Decimal("147.29")


def to_decimal(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, float)):
        return Decimal(str(x))

    s = str(x).strip()
    s = s.replace("R$", "").replace(" ", "")

    # Trata . e , em formato brasileiro
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")

    return Decimal(s)


def money(x: Decimal) -> Decimal:
    return x.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def brl(x: Decimal) -> str:
    x = money(x)
    s = f"{x:.2f}"
    return s.replace(".", ",")


@dataclass(frozen=True)
class Pedagio:
    id: str
    descricao: str
    valor_eixo: Decimal


@dataclass(frozen=True)
class ParametrosProgramacao:
    # Conforme folheto: PBT acima de 100,01 t; demais limites iguais/maiores
    pbt_programacao_t: Decimal = Decimal("100.01")
    largura_programacao_m: Decimal = Decimal("4.50")
    altura_programacao_m: Decimal = Decimal("5.40")
    comprimento_programacao_m: Decimal = Decimal("35.00")


def verifica_programacao(
    pbt_t,
    largura_m,
    altura_m,
    comprimento_m,
    params: ParametrosProgramacao = ParametrosProgramacao(),
) -> Tuple[bool, List[str]]:
    pbt_t = to_decimal(pbt_t)
    largura_m = to_decimal(largura_m)
    altura_m = to_decimal(altura_m)
    comprimento_m = to_decimal(comprimento_m)

    motivos = []

    if pbt_t > params.pbt_programacao_t:
        motivos.append(f"PBT {pbt_t}t > {params.pbt_programacao_t}t")
    if largura_m >= params.largura_programacao_m:
        motivos.append(f"Largura {largura_m}m >= {params.largura_programacao_m}m")
    if altura_m >= params.altura_programacao_m:
        motivos.append(f"Altura {altura_m}m >= {params.altura_programacao_m}m")
    if comprimento_m >= params.comprimento_programacao_m:
        motivos.append(f"Comprimento {comprimento_m}m >= {params.comprimento_programacao_m}m")

    precisa = len(motivos) > 0
    return precisa, motivos


def calcula_tarifa_operacional_escolta(precisa_programacao: bool) -> Decimal:
    return money(TARIFA_OPERACIONAL_ESCOLTA if precisa_programacao else Decimal("0.00"))


def calcula_tap_total(
    pbt_t,
    pedagios_passados: List[str],
    tabela_pedagios: Dict[str, Pedagio],
) -> Tuple[Decimal, List[dict]]:
    """
    TAP só se PBT > 45t e somente nos pedágios passados.

    Fórmula por pedágio:
      excedente = (PBT - 45)
      TAP_pedágio = excedente * 5 * valor_eixo

    Arredonda a TAP por pedágio em 2 casas.
    """
    pbt_t = to_decimal(pbt_t)

    if pbt_t <= Decimal("45"):
        return money(Decimal("0.00")), []

    excedente = pbt_t - Decimal("45")

    detalhes = []
    total = Decimal("0.00")

    for pid in pedagios_passados:
        if pid not in tabela_pedagios:
            raise ValueError(f"Pedágio '{pid}' não existe na tabela desta concessionária.")

        pedagio = tabela_pedagios[pid]
        tap = excedente * Decimal("5") * pedagio.valor_eixo
        tap = money(tap)  # arredonda por pedágio
        total += tap

        detalhes.append(
            {
                "pedagio_id": pedagio.id,
                "descricao": pedagio.descricao,
                "valor_eixo": brl(pedagio.valor_eixo),
                "excedente_pbt_t": str(excedente),
                "tap_calculada": brl(tap),
            }
        )

    return money(total), detalhes


# -----------------------------
# TABELAS DE PEDÁGIO
# -----------------------------

# Via Colinas
PEDAGIOS_COLINAS: Dict[str, Pedagio] = {
    "col_indaiatuba_sp075_km060_800": Pedagio(
        id="col_indaiatuba_sp075_km060_800",
        descricao="SP075 - Pedágio de Indaiatuba 060+800",
        valor_eixo=to_decimal("26,10")
    ),
    "col_boituva_sp280_km111_600": Pedagio(
        id="col_boituva_sp280_km111_600",
        descricao="SP280 - Pedágio de Boituva 111+600",
        valor_eixo=to_decimal("18,60")
    ),
    "col_riodaspedras_sp127_km058_600": Pedagio(
        id="col_riodaspedras_sp127_km058_600",
        descricao="SP127 - Pedágio de Rio das Pedras 058+600",
        valor_eixo=to_decimal("17,80")
    ),
    "col_rioclaro_sp127_km012_625": Pedagio(
        id="col_rioclaro_sp127_km012_625",
        descricao="SP127 - Pedágio de Rio Claro 012+625",
        valor_eixo=to_decimal("11,90")
    ),
    "col_itupeva_sp300_km076_680": Pedagio(
        id="col_itupeva_sp300_km076_680",
        descricao="SP300 - Pedágio de Itupeva 076+680",
        valor_eixo=to_decimal("14,20")
    ),
    "col_portofeliz_sp300_km136_722": Pedagio(
        id="col_portofeliz_sp300_km136_722",
        descricao="SP300 - Pedágio de Porto Feliz 136+722",
        valor_eixo=to_decimal("14,80")
    ),
}

# Rodovias do Tietê
PEDAGIOS_TIETE: Dict[str, Pedagio] = {
    "tie_monte_mor_sp101_km029_700": Pedagio(
        id="tie_monte_mor_sp101_km029_700",
        descricao="SP101 - Pedágio de Monte Mor 029+700m",
        valor_eixo=to_decimal("10,10")
    ),
    "tie_rafard_sp101_km055_800": Pedagio(
        id="tie_rafard_sp101_km055_800",
        descricao="SP101 - Pedágio de Rafard 055+800m",
        valor_eixo=to_decimal("7,20")
    ),
    "tie_conchas_sp300_km192_100": Pedagio(
        id="tie_conchas_sp300_km192_100",
        descricao="SP300 - Pedágio de Conchas 192+100m",
        valor_eixo=to_decimal("9,70")
    ),
    "tie_anhembi_sp300_km228_200": Pedagio(
        id="tie_anhembi_sp300_km228_200",
        descricao="SP300 - Pedágio de Anhembi 228+200m",
        valor_eixo=to_decimal("11,00")
    ),
    "tie_botucatu_sp300_km259_300": Pedagio(
        id="tie_botucatu_sp300_km259_300",
        descricao="SP300 - Pedágio de Botucatu 259+300m",
        valor_eixo=to_decimal("7,70")
    ),
    "tie_areiopolis_sp300_km285_000": Pedagio(
        id="tie_areiopolis_sp300_km285_000",
        descricao="SP300 - Pedágio de Areiópolis 285+000m",
        valor_eixo=to_decimal("8,60")
    ),
    "tie_lencois_paulista_sp300_km314_000": Pedagio(
        id="tie_lencois_paulista_sp300_km314_000",
        descricao="SP300 - Pedágio de Lençóis Paulista 314+000m",
        valor_eixo=to_decimal("8,30")
    ),
    "tie_elias_fausto_sp308_km109_300": Pedagio(
        id="tie_elias_fausto_sp308_km109_300",
        descricao="SP308 - Pedágio de Elias Fausto 109+300m",
        valor_eixo=to_decimal("5,00")
    ),
    "tie_riodaspedras_sp308_km147_300": Pedagio(
        id="tie_riodaspedras_sp308_km147_300",
        descricao="SP308 - Pedágio de Rio das Pedras 147+300m",
        valor_eixo=to_decimal("11,10")
    ),
}


def tabela_por_concessionaria(concessionaria: str) -> Dict[str, Pedagio]:
    c = concessionaria.strip().lower()
    if c in ("colinas", "via colinas", "via_colinas"):
        return PEDAGIOS_COLINAS
    if c in ("tiete", "tietê", "rodovias do tietê", "rodovias_do_tietê", "rdt"):
        return PEDAGIOS_TIETE
    raise ValueError("Concessionária inválida. Use 'colinas' ou 'tiete'.")


def calcular_resumo(
    concessionaria: str,
    pbt_t,
    largura_m,
    altura_m,
    comprimento_m,
    pedagios_passados: Optional[List[str]] = None,
) -> dict:
    if pedagios_passados is None:
        pedagios_passados = []

    tabela = tabela_por_concessionaria(concessionaria)

    precisa_prog, motivos = verifica_programacao(pbt_t, largura_m, altura_m, comprimento_m)
    tarifa_operacional = calcula_tarifa_operacional_escolta(precisa_prog)

    tap_total, tap_detalhes = calcula_tap_total(pbt_t, pedagios_passados, tabela)

    total_geral = money(tarifa_operacional + tap_total)

    return {
        "concessionaria": concessionaria,
        "entrada": {
            "pbt_t": str(to_decimal(pbt_t)),
            "largura_m": str(to_decimal(largura_m)),
            "altura_m": str(to_decimal(altura_m)),
            "comprimento_m": str(to_decimal(comprimento_m)),
            "pedagios_passados": pedagios_passados,
        },
        "programacao": {
            "precisa_programacao": precisa_prog,
            "motivos": motivos,
        },
        "custos": {
            "tarifa_operacional_escolta": brl(tarifa_operacional),
            "tap_total": brl(tap_total),
            "total_geral": brl(total_geral),
        },
        "tap_detalhamento": tap_detalhes,
    }


def listar_pedagios(concessionaria: str) -> List[Tuple[str, Pedagio]]:
    tabela = tabela_por_concessionaria(concessionaria)
    # retorna lista de (id, objeto) para facilitar ordenação/enumeração
    return list(tabela.items())