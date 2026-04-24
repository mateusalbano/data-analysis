import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


# region Auxiliares
def apply_metric_filter(df, metric):
    df = df.copy()

    if metric in ['Total Impacted', "Total Damage ('000 US$)", 'Number of Days']:
        df = df[df[metric] > 0]

    elif metric == 'Fatality Rate':
        df = df[
            (df['Fatality Rate'] > 0) &
            (df['Fatality Rate'] < 1) &
            (df['Total Deaths'] > 0) &
            (df['Total Impacted'] > 0)
        ]

    return df

# region Carregar Dados
@st.cache_data
def load_data():
    return pd.read_csv("data/prepared_public_emdat_2026.csv")


most_important_cols = [
    'Total Impacted',
    "Total Damage ('000 US$)",
    'Number of Days',
    'Fatality Rate'
]

data = load_data()


# region Sidebar - Filtros
st.sidebar.header("Filtros Globais")

filtered_data = data.copy()

# Região
regions = sorted(filtered_data["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Região", regions)

if selected_regions:
    filtered_data = filtered_data[filtered_data["Region"].isin(selected_regions)]

# Subregião
subregions = sorted(filtered_data["Subregion"].dropna().unique())
selected_subregions = st.sidebar.multiselect("Subregião", subregions)

if selected_subregions:
    filtered_data = filtered_data[filtered_data["Subregion"].isin(selected_subregions)]

# País
countries = sorted(filtered_data["Country"].dropna().unique())
selected_countries = st.sidebar.multiselect("País", countries)

if selected_countries:
    filtered_data = filtered_data[filtered_data["Country"].isin(selected_countries)]

# Grupo
groups = sorted(filtered_data["Disaster Group"].dropna().unique())
selected_groups = st.sidebar.multiselect("Grupo de Desastre", groups)

if selected_groups:
    filtered_data = filtered_data[filtered_data["Disaster Group"].isin(selected_groups)]

# Subgrupo
subgroups = sorted(filtered_data["Disaster Subgroup"].dropna().unique())
selected_subgroups = st.sidebar.multiselect("Subgrupo de Desastre", subgroups)

if selected_subgroups:
    filtered_data = filtered_data[filtered_data["Disaster Subgroup"].isin(selected_subgroups)]

# Tipo
types = sorted(filtered_data["Disaster Type"].dropna().unique())
selected_types = st.sidebar.multiselect("Tipo de Desastre", types)

if selected_types:
    filtered_data = filtered_data[filtered_data["Disaster Type"].isin(selected_types)]

# Subtipo
subtypes = sorted(filtered_data["Disaster Subtype"].dropna().unique())
selected_subtypes = st.sidebar.multiselect("Subtipo de Desastre", subtypes)

if selected_subtypes:
    filtered_data = filtered_data[filtered_data["Disaster Subtype"].isin(selected_subtypes)]

# Ano
years = sorted(filtered_data["Start Year"].dropna().unique())
selected_years = st.sidebar.multiselect("Ano", years)

if selected_years:
    filtered_data = filtered_data[filtered_data["Start Year"].isin(selected_years)]

# Mês
months = sorted(filtered_data["Start Month"].dropna().unique())
selected_months = st.sidebar.multiselect("Mês", months)

if selected_months:
    filtered_data = filtered_data[filtered_data["Start Month"].isin(selected_months)]


# region Card Resumo
st.header("Resumo")

selected_metric_card = st.selectbox(
    "Selecione a métrica para resumo",
    most_important_cols + ["Contagem de Registros"],
    key="card_metric"
)

if selected_metric_card == "Contagem de Registros":
    total_value = len(filtered_data)
else:
    card_data = apply_metric_filter(filtered_data, selected_metric_card)

    if selected_metric_card == 'Fatality Rate' or selected_metric_card == 'Number of Days':
        total_value = card_data[selected_metric_card].mean()
    else:
        total_value = card_data[selected_metric_card].sum()

st.metric(
    label=f"{selected_metric_card}",
    # value=f"{total_value:,.2f}" if isinstance(total_value, float) else total_value
    value=f"{total_value:,.2f}"
)


# region Distribuição
st.header("Distribuição")

chart_type = st.selectbox("Tipo de gráfico", ["Histograma", "Boxplot"])
metric = st.selectbox("Métrica", most_important_cols)

plot_data = apply_metric_filter(filtered_data, metric)

if chart_type == "Histograma":
    plot_data = plot_data.copy()
    plot_data[f'log_{metric}'] = np.log10(plot_data[metric])

    fig = px.histogram(
        plot_data,
        x=f'log_{metric}',
        title=f'Distribuição de {metric} (log10)'
    )
    fig.update_xaxes(title=f'log10({metric})')

else:
    fig = px.box(
        plot_data,
        y=metric,
        title=f'Boxplot de {metric}',
        log_y=True
    )

st.plotly_chart(fig)
st.write(plot_data[metric].describe())


# region Correlação
st.header("Correlação")

corr_options = most_important_cols + ["Start Year", "Start Month"]

x_col = st.selectbox("Eixo X", corr_options, key="corr_x")
y_col = st.selectbox("Eixo Y", corr_options, key="corr_y")

corr_data = filtered_data.copy()

# aplica filtro apenas para métricas contínuas
if x_col in most_important_cols:
    corr_data = corr_data[corr_data[x_col] > 0]

if y_col in most_important_cols:
    corr_data = corr_data[corr_data[y_col] > 0]

correlation = corr_data[x_col].corr(corr_data[y_col])

fig = px.scatter(
    corr_data,
    x=x_col,
    y=y_col,
    title=f'Correlação: {correlation:.3f}'
)

# log apenas para métricas contínuas
if x_col in most_important_cols:
    fig.update_xaxes(type="log")

if y_col in most_important_cols:
    fig.update_yaxes(type="log")

st.plotly_chart(fig)
st.write(f"Coeficiente de correlação: {correlation:.4f}")

# region Heatmap
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

heatmap_data = filtered_data.copy()

heatmap_data[x_col] = heatmap_data[x_col].astype(str)
heatmap_data[y_col] = heatmap_data[y_col].astype(str)

if metric_option == "Contagem de Registros":
    pivot = heatmap_data.groupby([y_col, x_col]).size().unstack(fill_value=0)
else:
    pivot = heatmap_data.groupby([y_col, x_col])[metric_option] \
        .mean().unstack(fill_value=0)

num_records = len(filtered_data)

fig = px.imshow(
    pivot,
    color_continuous_scale="viridis",
    title=f"{metric_option} por {y_level} vs {x_level}"
)

fig.add_annotation(
    text=f"Número de registros: {num_records}",
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.1,
    showarrow=False
)

st.plotly_chart(fig)