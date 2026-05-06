

# region Imports
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


# region Auxiliares
# Filtrar > 0
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

# Carregar Dados
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


def apply_all_filters(data):
    result = data.copy()

    for key in filter_keys:
        if key in st.session_state and st.session_state[key]:  # ✅ Só filtra se houver seleção
            result = result[result[key].isin(st.session_state[key])]
    
    return result

def build_sidebar():


    with st.sidebar:
        st.sidebar.header("Filtros Globais")
        # Botão Resetar Filtros
        st.sidebar.button("Reiniciar Filtros", on_click=reset_filters)

        for key in filter_keys:
            options = sorted(full_data[key].dropna().unique())
            st.sidebar.multiselect(key, options, key=key)


build_sidebar()

aba_variavel, aba_correlacao, aba_heatmap = st.tabs(["Análise de Variáveis", "Correlação Entre Variáveis", "Heatmap"])
filtered_data = apply_all_filters(full_data)

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

    col1, col2, col3 = st.columns(3)
    
    with col1:
        chart_type = st.selectbox("Tipo de gráfico", ["Histograma", "Boxplot"])
    
    with col2:
        metric = st.selectbox("Métrica", most_important_cols)
    
    with col3:
        scale_type = st.selectbox(
            "Escala da Métrica",
            ["Normal", "Logarítmica"],
            key="dist_scale"
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

    st.subheader("Heatmap Correlação")    
    
    col1, col2 = st.columns(2)
    with col1:
        heatmap_scale = st.selectbox(
            "Filtrar zeros para heatmap (escala Log)?",
            ["Não", "Sim"],
            key="heatmap_scale"
        )
    
    heatmap_cols = corr_options
    heatmap_data = filtered_data.copy()
    heatmap_data = heatmap_data[heatmap_cols]

    if heatmap_scale == "Sim":
        heatmap_data = heatmap_data[(heatmap_data > 0).all(axis=1)]

    heatmap_corr = heatmap_data.corr()

    fig_heatmap = px.imshow(
        heatmap_corr,
        text_auto=True,
        title="Heatmap de Correlação"
    )

    st.plotly_chart(fig_heatmap)

    st.subheader("Análise de Correlação")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        x_col = st.selectbox("Variável X", corr_options, key="corr_x")
    
    with col2:
        x_scale = st.selectbox("Escala X", ["Linear", "Log"], key="x_scale")
    
    with col3:
        y_col = st.selectbox("Variável Y", corr_options, key="corr_y")
    
    with col4:
        y_scale = st.selectbox("Escala Y", ["Linear", "Log"], key="y_scale")

    corr_data = filtered_data.copy()
    
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

    st.subheader("Heatmap Customizado - Correlação por Escala")
    
    st.write("Selecione a escala (Linear/Log) para cada variável e visualize a matriz de correlação:")
    
    scale_selection = {}
    
    cols_per_row = 3
    cols = st.columns(cols_per_row)
    
    for idx, var in enumerate(corr_options):
        col_idx = idx % cols_per_row
        with cols[col_idx]:
            scale_selection[var] = st.selectbox(
                f"Escala - {var}",
                ["Linear", "Log"],
                key=f"custom_scale_{var}"
            )
        
        if (idx + 1) % cols_per_row == 0 and idx < len(corr_options) - 1:
            cols = st.columns(cols_per_row)
    
    custom_heatmap_data = filtered_data.copy()
    custom_heatmap_data = custom_heatmap_data[corr_options].copy()
    
    for var in corr_options:
        if scale_selection[var] == "Log":
            custom_heatmap_data = custom_heatmap_data[custom_heatmap_data[var] > 0]
    
    for var in corr_options:
        if scale_selection[var] == "Log":
            custom_heatmap_data[var] = np.log10(custom_heatmap_data[var])
    
    custom_corr = custom_heatmap_data.corr()
    
    custom_labels = [f"{var}\n({scale_selection[var]})" for var in corr_options]
    custom_corr.index = custom_labels
    custom_corr.columns = custom_labels
    
    fig_custom = px.imshow(
        custom_corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Matriz de Correlação - Escalas Customizadas",
        labels=dict(x="Variáveis", y="Variáveis")
    )
    
    st.plotly_chart(fig_custom)


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

    col1, col2 = st.columns(2)
    
    with col1:
        x_category = st.selectbox("Categoria eixo X", list(axis_options.keys()))
        x_level = st.selectbox("Nível eixo X", list(axis_options[x_category].keys()))
    
    with col2:
        y_category = st.selectbox("Categoria eixo Y", list(axis_options.keys()))
        y_level = st.selectbox("Nível eixo Y", list(axis_options[y_category].keys()))

    x_col = axis_options[x_category][x_level]
    y_col = axis_options[y_category][y_level]

    col1, col2 = st.columns(2)
    
    with col1:
        metric_option = st.selectbox(
            "Métrica",
            most_important_cols + ["Contagem de Registros"]
        )
    
    with col2:
        metric_scale = st.selectbox(
            "Escala da Métrica",
            ["Normal", "Logarítmica"],
            key="heatmap_metric_scale"
        )

    heatmap_data = filtered_data.copy()

    heatmap_data[x_col] = heatmap_data[x_col].astype(str)
    heatmap_data[y_col] = heatmap_data[y_col].astype(str)

    if metric_option == "Contagem de Registros":
        pivot = heatmap_data.groupby([y_col, x_col]).size().unstack(fill_value=0)
    else:
        pivot = heatmap_data.groupby([y_col, x_col])[metric_option] \
            .mean().unstack(fill_value=0)
        
        # Aplicar escala logarítmica se selecionada
        if metric_scale == "Logarítmica":
            # Substituir zeros por NaN antes de aplicar log
            pivot = pivot.replace(0, np.nan)
            pivot = np.log10(pivot)

    num_records = len(filtered_data)

    fig = px.imshow(
        pivot,
        color_continuous_scale="viridis",
        title=f"{metric_option} por {y_level} vs {x_level} ({metric_scale})"
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