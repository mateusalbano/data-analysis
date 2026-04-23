def preprocess_data(df):
    df = df.copy()

    # Remover zeros nas métricas principais
    df = df[
        (df['Total Impacted'] > 0) &
        (df["Total Damage ('000 US$)"] > 0) &
        (df['Number of Days'] > 0)
    ]

    # Regra crítica: Fatality Rate inválido
    df = df[
        (df['Fatality Rate'] > 0) &
        (df['Total Deaths'] > 0)
    ]

    return df

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load
@st.cache_data
def load_data():
    return pd.read_csv("data/prepared_public_emdat_2026.csv")

data = load_data()
data = preprocess_data(data)

most_important_cols = [
    'Total Impacted',
    "Total Damage ('000 US$)",
    'Number of Days',
    'Fatality Rate'
]

st.sidebar.header("Filtros Globais")

years = st.sidebar.multiselect("Ano", sorted(data['Start Year'].dropna().unique()))
months = st.sidebar.multiselect("Mês", sorted(data['Start Month'].dropna().unique()))
countries = st.sidebar.multiselect("País", data['Country'].dropna().unique())
regions = st.sidebar.multiselect("Região", data['Region'].dropna().unique())
subregions = st.sidebar.multiselect("Subregião", data['Subregion'].dropna().unique())

filtered_data = data.copy()


if years:
    filtered_data = filtered_data[filtered_data['Start Year'].isin(years)]
if months:
    filtered_data = filtered_data[filtered_data['Start Month'].isin(months)]
if countries:
    filtered_data = filtered_data[filtered_data['Country'].isin(countries)]
if regions:
    filtered_data = filtered_data[filtered_data['Region'].isin(regions)]
if subregions:
    filtered_data = filtered_data[filtered_data['Subregion'].isin(subregions)]

st.header("Distribuição")

chart_type = st.selectbox("Tipo de gráfico", ["Histograma", "Boxplot"])
metric = st.selectbox("Métrica", most_important_cols)

plot_data = filtered_data[filtered_data[metric] > 0]

fig, ax = plt.subplots()

if chart_type == "Histograma":
    sns.histplot(plot_data[metric], bins=50, kde=True, log_scale=True, ax=ax)
    ax.set_title(f'Distribution of {metric}')

else:
    sns.boxplot(y=plot_data[metric], ax=ax)
    ax.set_yscale('log')
    ax.set_title(f'Boxplot of {metric}')

st.pyplot(fig)
st.write(plot_data[metric].describe())


st.header("Correlação")

x_col = st.selectbox("Eixo X", most_important_cols, key="corr_x")
y_col = st.selectbox("Eixo Y", most_important_cols, key="corr_y")

corr_data = filtered_data[
    (filtered_data[x_col] > 0) & (filtered_data[y_col] > 0)
]

correlation = corr_data[x_col].corr(corr_data[y_col])

fig, ax = plt.subplots()
ax.scatter(corr_data[x_col], corr_data[y_col], alpha=0.5)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_title(f'Correlation: {correlation:.3f}')

st.pyplot(fig)
st.write(f"Coeficiente de correlação: {correlation:.4f}")


st.header("Heatmap Multivariável")

axis_options = {
    "Data": {
        "Ano": "Start Year",
        "Mês": "Start Month"
    },
    "Localidade": {
        "País": "Country",
        "Região": "Region",
        "Subregião": "Subregion"
    },
    "Tipo de Desastre": {
        "Grupo": "Disaster Group",
        "Subgrupo": "Disaster Subgroup",
        "Tipo": "Disaster Type",
        "Subtipo": "Disaster Subtype"
    }
}


x_category = st.selectbox("Categoria eixo X", list(axis_options.keys()))
x_level = st.selectbox("Nível eixo X", list(axis_options[x_category].keys()))

y_category = st.selectbox("Categoria eixo Y", list(axis_options.keys()))
y_level = st.selectbox("Nível eixo Y", list(axis_options[y_category].keys()))

x_col = axis_options[x_category][x_level]
y_col = axis_options[y_category][y_level]


metric_option = st.selectbox(
    "Métrica",
    most_important_cols + ["Contagem de Registros"]
)


filtered_data = filtered_data.copy()

filtered_data[x_col] = filtered_data[x_col].astype(str)
filtered_data[y_col] = filtered_data[y_col].astype(str)

if metric_option == "Contagem de Registros":
    pivot = filtered_data.groupby([y_col, x_col]).size().unstack(fill_value=0)
else:
    pivot = filtered_data.groupby([y_col, x_col])[metric_option] \
        .mean().unstack(fill_value=0)


fig, ax = plt.subplots(figsize=(12, 8))

sns.heatmap(pivot, cmap="viridis", ax=ax)

ax.set_title(f"{metric_option} by {y_level} vs {x_level}")

st.pyplot(fig)