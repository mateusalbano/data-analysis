import pandas as pd

# Arquivo de entrada
arquivo_entrada = "data/prepared_public_emdat_2026.csv"

# Arquivo de saída
arquivo_saida = "data/adapted_data.csv"

# Ler CSV
df = pd.read_csv(arquivo_entrada)

# Remover colunas que não serão usadas
df = df.drop(columns=["DisNo.", "Historic", "ISO", 'End Day', 'Start Day', 'Disaster Group', 'Disaster Subgroup', 'Disaster Type', 'Disaster Subtype', 'Location', 'End Year', 'End Month', 'Date'], errors="ignore")

# Nomes das colunas originais
col_insured = "Insured Damage ('000 US$)"
col_total = "Total Damage ('000 US$)"

# Criar colunas corrigidas usando CPI
df[f"{col_insured}_corrigido"] = df[col_insured] * df["CPI"]
df[f"{col_total}_corrigido"] = df[col_total] * df["CPI"]

# Remover colunas antigas e CPI
df = df.drop(
    columns=[
        col_insured,
        col_total,
        "CPI"
    ],
    errors="ignore"
)

# Salvar resultado
df.to_csv(arquivo_saida, index=False)

print(f"Arquivo salvo em: {arquivo_saida}")