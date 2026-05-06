
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


def apply_metric_filter(df, metric):
    new_df = df.copy()

    if metric in ['Total Impacted', "Total Damage ('000 US$)", 'Number of Days']:
        new_df = new_df[new_df[metric] > 0]

    elif metric == 'Fatality Rate':
        new_df = new_df[
            (new_df['Fatality Rate'] > 0) &
            (new_df['Fatality Rate'] < 1) &
            (new_df['Total Deaths'] > 0) &
            (new_df['Total Impacted'] > 0)
        ]

    return new_df

@st.cache_data
def load_data():
    return pd.read_csv("data/prepared_public_emdat_2026.csv")

full_data = load_data()

# Chaves importantes para filtros
most_important_cols = [
    'Total Impacted',
    "Total Damage ('000 US$)",
    'Number of Days',
    'Fatality Rate',
    'Total Deaths'
]

filter_keys = [
    "Region", "Subregion", "Country",
    "Disaster Group", "Disaster Subgroup", "Disaster Type",
    "Disaster Subtype", "Start Year", "Start Month"
]


for key in filter_keys:
    if key not in st.session_state:
        st.session_state[key] = []


def reset_filters():
    for key in filter_keys:
        st.session_state[key] = []
    return filtered_data


with st.sidebar:
    st.sidebar.header("Filtros Globais")

    filtered_data = full_data.copy()

    st.sidebar.button("Reiniciar Filtros", on_click=reset_filters)

    for key in filter_keys:

        temp_data = sorted(filtered_data[key].dropna().unique())
        selected_data = st.sidebar.multiselect(key, temp_data, key=f"sel_{key.lower().replace(' ', '_')}")

        if selected_data:
            filtered_data = filtered_data[filtered_data[key].isin(selected_data)]


aba_variavel, aba_correlacao, aba_heatmap = st.tabs(["📄 Análise de Variáveis", "📈 Correlação Entre Variáveis", "📊  Heatmap"])


with aba_variavel:
    st.subheader("Resumo")

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
        value=f"{total_value:,.2f}"
    )


    st.subheader("Distribuição")

    chart_type = st.selectbox("Tipo de gráfico", ["Histograma", "Boxplot"])
    metric = st.selectbox("Métrica", most_important_cols)

    scale_type = st.radio(
        "Escala",
        ["Normal", "Logarítmica"],
        horizontal=True
    )

    plot_data = apply_metric_filter(filtered_data, metric)

    if chart_type == "Histograma":
        plot_data = plot_data.copy()

        if scale_type == "Logarítmica":
            plot_data[f'log_{metric}'] = np.log10(plot_data[metric])
            x_col = f'log_{metric}'
            x_title = f'log10({metric})'
        else:
            x_col = metric
            x_title = metric

        fig = px.histogram(
            plot_data,
            x=x_col,
            title=f'Distribuição de {metric}'
        )

        fig.update_xaxes(title=x_title)

    else:
        fig = px.box(
            plot_data,
            y=metric,
            title=f'Boxplot de {metric}',
            log_y=(scale_type == "Logarítmica")
        )

    st.plotly_chart(fig)
    st.write(plot_data[metric].describe())


with aba_correlacao:
    corr_options = most_important_cols + ["Start Year", "Start Month"]

    scale_options = ["Linear", "Log"]

    x_scale = st.selectbox("Escala eixo X", scale_options, key="x_scale")
    y_scale = st.selectbox("Escala eixo Y", scale_options, key="y_scale")

    # region Heatmap Correlação
    st.subheader("Heatmap Correlação")    
    heatmap_cols = corr_options
    heatmap_data = filtered_data.copy()
    heatmap_data = heatmap_data[heatmap_cols]

    if y_scale == "Log" or x_scale == "Log":
        heatmap_data = heatmap_data[(heatmap_data > 0).all(axis=1)]

    heatmap_corr = heatmap_data.corr()

    fig_heatmap = px.imshow(
        heatmap_corr,
        text_auto=True,
        title="Heatmap de Correlação"
    )

    st.plotly_chart(fig_heatmap)

    # region Correlação
    corr_data = filtered_data.copy()
    x_col = st.selectbox("Eixo X", corr_options, key="corr_x")
    y_col = st.selectbox("Eixo Y", corr_options, key="corr_y")

    if x_scale == "Log":
        corr_data = corr_data[corr_data[x_col] > 0]
    if y_scale == "Log":
        corr_data = corr_data[corr_data[y_col] > 0]

    x_values = corr_data[x_col]
    y_values = corr_data[y_col]

    if x_scale == "Log":
        x_values = np.log10(x_values)
    if y_scale == "Log":
        y_values = np.log10(y_values)

    correlation = x_values.corr(y_values)

    fig = px.scatter(
        corr_data,
        x=x_col,
        y=y_col,
        title=f'Correlação: {correlation:.3f}'
    )

    fig.update_xaxes(type="log" if x_scale == "Log" else "linear")
    fig.update_yaxes(type="log" if y_scale == "Log" else "linear")

    st.plotly_chart(fig)
    st.write(f"Coeficiente de correlação: {correlation:.4f}")


# region Aba Heatmap
with aba_heatmap:
    st.subheader("Heatmap Multivariável")

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