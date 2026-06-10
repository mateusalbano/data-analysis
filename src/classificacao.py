import pandas as pd
import warnings

from itertools import combinations

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score, accuracy_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

ARQUIVO_ENTRADA = "data/adapted_data.csv"
ARQUIVO_SAIDA = "data/resultado_combinacoes.csv"

MIN_COLUNAS = 4
MAX_COLUNAS = 10

MIN_GRUPOS = 3
MAX_GRUPOS = 10

SALVAR_A_CADA = 500

print("Carregando dataset...")

df = pd.read_csv(ARQUIVO_ENTRADA)

print(f"Linhas: {len(df)}")
print(f"Colunas: {len(df.columns)}")

col_textuais = [
    "Classification Key",
    "Country",
    "Subregion",
    "Region"
]

col_binarias = [
    "Appeal",
    "OFDA/BHA Response",
    "Declaration"
]

for col in col_binarias:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.lower()
            .map({
                "yes": 1,
                "no": 0
            })
        )

encoders = {}

for col in col_textuais:
    if col in df.columns:
        encoder = LabelEncoder()
        df[col] = encoder.fit_transform(df[col].astype(str))
        encoders[col] = encoder

df = df.dropna()

print("Normalizando dados...")

scaler = StandardScaler()
df[df.columns] = scaler.fit_transform(df[df.columns])

colunas = list(df.columns)

def executar_kmeans(X):
    melhor_score = -1
    melhor_labels = None
    melhor_k = None

    for k in range(MIN_GRUPOS, MAX_GRUPOS + 1):
        try:
            modelo = MiniBatchKMeans(
                n_clusters=k,
                random_state=42,
                n_init=5,
                batch_size=2048
            )

            labels = modelo.fit_predict(X)

            score = silhouette_score(
                X,
                labels,
                sample_size=min(3000, len(X)),
                random_state=42
            )

            if score > melhor_score:
                melhor_score = score
                melhor_labels = labels
                melhor_k = k

        except Exception as e:
            print(f"Erro no KMeans k={k}: {e}")
            continue

    if melhor_labels is None:
        raise Exception("Nenhum K válido encontrado.")

    return melhor_score, melhor_labels, melhor_k

def executar_knn(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y
    )

    modelo = KNeighborsClassifier(
        n_neighbors=5,
        n_jobs=-1
    )

    modelo.fit(X_train, y_train)

    pred = modelo.predict(X_test)

    return accuracy_score(y_test, pred)

resultados = []

total = sum(
    len(list(combinations(colunas, i)))
    for i in range(MIN_COLUNAS, MAX_COLUNAS + 1)
)

contador = 0

print(f"Total de combinações: {total}")

for tamanho in range(MIN_COLUNAS, MAX_COLUNAS + 1):
    for combinacao in combinations(colunas, tamanho):
        contador += 1

        print(f"[{contador}/{total}] Testando {combinacao}")

        try:
            X = df[list(combinacao)].values

            qualidade, grupos, k = executar_kmeans(X)

            acuracia = executar_knn(X, grupos)

            resultados.append({
                "Qtd_Colunas": tamanho,
                "Colunas": ",".join(combinacao),
                "Silhouette_Score": qualidade,
                "Perc_acertos_class": acuracia * 100,
                "K_melhor": k
            })

        except Exception as e:
            print(f"ERRO na combinação {combinacao}: {e}")
            continue

        if contador % SALVAR_A_CADA == 0:
            pd.DataFrame(resultados).to_csv(
                ARQUIVO_SAIDA,
                index=False,
                encoding="utf-8"
            )

            print("Arquivo salvo...")

pd.DataFrame(resultados).to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8"
)

print(f"\nFINALIZADO - Resultado salvo em: {ARQUIVO_SAIDA}")