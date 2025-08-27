import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# Função para converter os valores
def converter_valor(valor, tipo="int"):
    if valor is None or valor.strip() == "":
        return None
    valor = valor.replace(".", "").replace(",", ".")
    try:
        if tipo == "int":
            return int(float(valor))
        else:
            return float(valor)
    except:
        return None

# Função principal de extração
def extrair_dados(pdf_file):
    dados = []
    chapas_padrao = []

    with pdfplumber.open(pdf_file) as pdf:
        for idx, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()

            # Extrair nome da cidade
            cidade_match = re.search(r"^(.*?)\s*-\s*CREA PR", texto, re.MULTILINE)
            cidade = cidade_match.group(1).strip() if cidade_match else "NÃO ENCONTRADO"

            tabela = pagina.extract_table()

            if tabela:
                colunas = tabela[0]

                # Na primeira página, salvar a ordem das chapas como padrão
                if idx == 0:
                    chapas_padrao = [linha[0].strip() for linha in tabela[1:]]

                registro = {"Cidade": cidade}

                for linha in tabela[1:]:
                    linha_dict = dict(zip(colunas, linha))
                    chapa = linha_dict["Chapas"].strip()

                    registro[f"{chapa} - Votos"] = converter_valor(linha_dict["Votos"], "int")
                    registro[f"{chapa} - Percentual"] = converter_valor(linha_dict["Percentual"], "float")
                    registro[f"{chapa} - % Válidos*"] = converter_valor(linha_dict["% Válidos*"], "float")

                dados.append(registro)

    df = pd.DataFrame(dados)

    # Construir ordem final
    colunas_final = ["Cidade"]
    for chapa in chapas_padrao:
        colunas_final.append(f"{chapa} - Votos")
        colunas_final.append(f"{chapa} - Percentual")
        colunas_final.append(f"{chapa} - % Válidos*")

    colunas_final = [c for c in colunas_final if c in df.columns]
    df = df[colunas_final]

    return df


# ---------------- STREAMLIT APP ---------------- #

st.title("📊 Extração de Votos - Apuração Confea 2025")

uploaded_file = st.file_uploader("Envie o arquivo PDF", type="pdf")

if uploaded_file is not None:
    st.info("⏳ Processando arquivo, aguarde...")

    df = extrair_dados(uploaded_file)

    st.success("✅ Extração concluída!")

    st.dataframe(df.head())  # mostra prévia

    # Gerar CSV para download
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, sep=";")
    st.download_button(
        label="⬇️ Baixar CSV",
        data=csv_buffer.getvalue(),
        file_name="resultado_eleicoes.csv",
        mime="text/csv"
    )

    # Gerar Excel para download
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Apuração")
    st.download_button(
        label="⬇️ Baixar Excel",
        data=excel_buffer.getvalue(),
        file_name="resultado_eleicoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
