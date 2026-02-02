import streamlit as st
import pandas as pd
from io import BytesIO
import os

from engine import (
    listar_pedagios,
    calcular_resumo
)

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Cálculo AET / TAP",
    page_icon="🚛",
    layout="centered"
)

# -----------------------------
# LOGO
# -----------------------------
st.image("Via-Appia.png.webp", width=200)

# -----------------------------
# TÍTULO
# -----------------------------
st.title("🚛 Sistema de Cálculo AET / TAP")
st.write("Via Colinas • Rodovias do Tietê")

# -----------------------------
# IDENTIFICAÇÃO AET
# -----------------------------
st.subheader("📄 Identificação")
numero_aet = st.text_input(
    "Número da AET",
    placeholder="Ex: AET-2026-000123"
)

# -----------------------------
# CONCESSIONÁRIA
# -----------------------------
concessionaria = st.selectbox(
    "Selecione a Concessionária",
    ["Via Colinas", "Rodovias do Tietê"]
)

# -----------------------------
# DADOS DA CARGA
# -----------------------------
st.subheader("📦 Dados da carga")

pbt = st.text_input("PBT (toneladas)", placeholder="Ex: 120,5")
largura = st.text_input("Largura (m)", placeholder="Ex: 4,20")
altura = st.text_input("Altura (m)", placeholder="Ex: 5,10")
comprimento = st.text_input("Comprimento (m)", placeholder="Ex: 25,00")

# -----------------------------
# PEDÁGIOS
# -----------------------------
st.subheader("🛣️ Pedágios percorridos")

itens = listar_pedagios(concessionaria)

pedagios_map = {
    ped.descricao: pid
    for pid, ped in itens
}

pedagios_escolhidos = st.multiselect(
    "Selecione os pedágios por onde a carga passará",
    options=list(pedagios_map.keys())
)

pedagios_ids = [pedagios_map[p] for p in pedagios_escolhidos]

# -----------------------------
# BOTÃO DE CÁLCULO
# -----------------------------
if st.button("🧮 Calcular"):

    resultado = calcular_resumo(
        concessionaria=concessionaria,
        pbt_t=pbt,
        largura_m=largura,
        altura_m=altura,
        comprimento_m=comprimento,
        pedagios_passados=pedagios_ids
    )

    st.divider()
    st.subheader("📊 Resultado")

    # -----------------------------
    # PROGRAMAÇÃO
    # -----------------------------
    if resultado["programacao"]["precisa_programacao"]:
        st.error("🚨 REQUER PROGRAMAÇÃO (Escolta necessária)")
        for motivo in resultado["programacao"]["motivos"]:
            st.write(f"• {motivo}")
    else:
        st.success("✅ NÃO requer programação")

    # -----------------------------
    # CUSTOS
    # -----------------------------
    st.subheader("💰 Custos")
    st.write(f"Tarifa Operacional (Escolta): R$ {resultado['custos']['tarifa_operacional_escolta']}")
    st.write(f"TAP Total: R$ {resultado['custos']['tap_total']}")
    st.markdown(f"### **TOTAL GERAL: R$ {resultado['custos']['total_geral']}**")

    # -----------------------------
    # DETALHAMENTO TAP
    # -----------------------------
    if resultado["tap_detalhamento"]:
        st.subheader("📑 Detalhamento da TAP")
        for det in resultado["tap_detalhamento"]:
            with st.expander(det["descricao"]):
                st.write(f"Valor eixo: R$ {det['valor_eixo']}")
                st.write(f"Excedente PBT: {det['excedente_pbt_t']} t")
                st.write(f"TAP calculada: R$ {det['tap_calculada']}")

    # -----------------------------
    # DADOS PARA PLANILHA / HISTÓRICO
    # -----------------------------
    dados = {
        "Número AET": numero_aet,
        "Concessionária": resultado["concessionaria"],
        "PBT (t)": resultado["entrada"]["pbt_t"],
        "Largura (m)": resultado["entrada"]["largura_m"],
        "Altura (m)": resultado["entrada"]["altura_m"],
        "Comprimento (m)": resultado["entrada"]["comprimento_m"],
        "Pedágios Percorridos": ", ".join(pedagios_escolhidos),
        "Requer Programação": "Sim" if resultado["programacao"]["precisa_programacao"] else "Não",
        "Motivos Programação": " | ".join(resultado["programacao"]["motivos"]),
        "Tarifa Operacional (R$)": resultado["custos"]["tarifa_operacional_escolta"],
        "TAP Total (R$)": resultado["custos"]["tap_total"],
        "Total Geral (R$)": resultado["custos"]["total_geral"],
    }

    df_resultado = pd.DataFrame([dados])

    # -----------------------------
    # SALVAR HISTÓRICO AUTOMÁTICO
    # -----------------------------
    arquivo_historico = "historico_aet.xlsx"

    if os.path.exists(arquivo_historico):
        df_historico = pd.read_excel(arquivo_historico)
        df_historico = pd.concat([df_historico, df_resultado], ignore_index=True)
    else:
        df_historico = df_resultado

    df_historico.to_excel(arquivo_historico, index=False)

    st.success("📂 Histórico salvo automaticamente")

    # -----------------------------
    # GERAR PLANILHA PARA DOWNLOAD
    # -----------------------------
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Resumo AET")

    buffer.seek(0)

    st.download_button(
        label="📥 Baixar planilha Excel",
        data=buffer,
        file_name=f"AET_{numero_aet}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )