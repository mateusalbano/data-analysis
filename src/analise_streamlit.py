import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def apply_metric_filter(df, metric):
    df = df.copy()

    if metric in ['Total Impacted', "Total Damage ('000 US$)", 'Number of Days']:
        df = df[df[metric] > 0]

    elif metric == 'Fatality Rate':
        df = df[
            (df['Fatality Rate'] > 0) &
            (df['Total Deaths'] > 0) &
            (df['Total Impacted'] > 0)
        ]

    return df


# Load
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
for col in most_important_cols:
    data = apply_metric_filter(data, col)


st.sidebar.header("Filtros Globais")

global_filters = {
    "Ano": "Start Year",
    "Mês": "Start Month",
    "Região": "Region",
    "Subregião": "Subregion",
    "País": "Country",
    "Grupo de Desastre": "Disaster Group",
    "Subgrupo de Desastre": "Disaster Subgroup",
    "Tipo de Desastre": "Disaster Type",
    "Subtipo de Desastre": "Disaster Subtype"
}

filtered_data = data.copy()

for label, col in global_filters.items():
    options = sorted(data[col].dropna().unique())
    selected = st.sidebar.multiselect(label, options)
    if selected:
        filtered_data = filtered_data[filtered_data[col].isin(selected)]


st.header("Resumo")

selected_metric_card = st.selectbox(
    "Selecione a métrica para resumo",
    most_important_cols,
    key="card_metric"
)

card_data = apply_metric_filter(filtered_data, selected_metric_card)

total_value = 0

if selected_metric_card == 'Fatality Rate':
    total_value = card_data[selected_metric_card].mean()
else:
    total_value = card_data[selected_metric_card].sum()

st.metric(
    label=f"Total de {selected_metric_card}",
    value=f"{total_value:,.2f}" if isinstance(total_value, (float)) else total_value
)

st.header("Distribuição")

chart_type = st.selectbox("Tipo de gráfico", ["Histograma", "Boxplot"])
metric = st.selectbox("Métrica", most_important_cols)

plot_data = filtered_data[filtered_data[metric] > 0]

if chart_type == "Histograma":

    plot_data = filtered_data[filtered_data[metric] > 0].copy()
    plot_data[f'log_{metric}'] = np.log10(plot_data[metric])

    fig = px.histogram(
        plot_data,
        x=f'log_{metric}',
        title=f'Distribuição de {metric} (log10)'
    )
    fig.update_xaxes(title=f'log10({metric})')
else:
    fig = px.box(plot_data, y=metric, title=f'Boxplot of {metric}', log_y=True)

st.plotly_chart(fig)
st.write(plot_data[metric].describe())


st.header("Correlação")

x_col = st.selectbox("Eixo X", most_important_cols, key="corr_x")
y_col = st.selectbox("Eixo Y", most_important_cols, key="corr_y")

corr_data = filtered_data[
    (filtered_data[x_col] > 0) & (filtered_data[y_col] > 0)
]

correlation = corr_data[x_col].corr(corr_data[y_col])

fig = px.scatter(corr_data, x=x_col, y=y_col, title=f'Correlation: {correlation:.3f}')
fig.update_xaxes(type="log")
fig.update_yaxes(type="log")

st.plotly_chart(fig)
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

num_records = len(filtered_data)


fig = px.imshow(pivot, color_continuous_scale="viridis", title=f"{metric_option} by {y_level} vs {x_level}")
fig.add_annotation(text=f"Número de registros: {num_records}", xref="paper", yref="paper", x=0.5, y=1.1, showarrow=False)

st.plotly_chart(fig)