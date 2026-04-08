import pandas as pd
import numpy as np
import os

MAX_MISSINGNESS_THRESHOLD = 5 # Percentage threshold for dropping columns


def get_column_data_missingness(df):
    missingness = df.isnull().mean() * 100
    return missingness.sort_values(ascending=False)

def drop_highly_missing_columns(df):
    missingness = get_column_data_missingness(df)
    columns_to_drop = missingness[missingness > MAX_MISSINGNESS_THRESHOLD].index
    return df.drop(columns=columns_to_drop)

def fill_missing_numeric_values(df):
    for col in df.columns:
        if df[col].dtype in [np.float64, np.int64]:
            df[col] = df[col].fillna(df[col].median())
        # else:
        #     df[col] = df[col].fillna(df[col].mode()[0])
    return df


def _format_date(df):
    return pd.to_datetime(
        df[['Start Year', 'Start Month', 'Start Day']].rename(
            columns={'Start Year': 'year', 'Start Month': 'month', 'Start Day': 'day'}
        ), errors='coerce'
    )

def _get_total_affected(df):
    return df['No. Injured'] + df['No. Affected'] + df['No. Homeless']

def clean_emdat_data(df):
    df = df.drop_duplicates()

    mandatory_cols = ['DisNo.', 'ISO', 'Classification Key', 'Start Year']
    df = df.dropna(subset=mandatory_cols)

    
    df['Start Month'] = df['Start Month'].fillna(1).astype(int)
    df['Start Day'] = df['Start Day'].fillna(1).astype(int)
    df['Formatted_Start_Date'] = _format_date(df)

    impact_cols = ['No. Injured', 'No. Affected', 'No. Homeless']
    for col in impact_cols:
        df[col] = df[col].fillna(0)
    
    df['Total Affected'] = df['Total Affected'].fillna(_get_total_affected(df))
    df['External IDs'] = df['External IDs'].str.split('|')

    df = drop_highly_missing_columns(df)
    df = fill_missing_numeric_values(df)
    
    return df


if __name__ == "__main__":
    dir_path = "data"
    file_path = os.path.join(dir_path, "raw_public_emdat_2026.xlsx")
    raw_data = pd.read_excel(file_path)
    cleaned_data = clean_emdat_data(raw_data)
    cleaned_data.to_csv(os.path.join(dir_path, "cleaned_public_emdat_2026.csv"), index=False)