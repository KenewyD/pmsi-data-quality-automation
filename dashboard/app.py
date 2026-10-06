import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="PMSI Data Quality Dashboard",
    page_icon="🏥",
    layout="wide"
)

@st.cache_data
def generate_demo_data(seed=42):
    rng = np.random.default_rng(seed)

    n = 2500
    services = ["MCO", "SMR", "HAD", "Psychiatrie"]

    df = pd.DataFrame({
        "sejour_id": [f"S{i:05d}" for i in range(1, n + 1)],
        "patient_id": [f"P{rng.integers(1, 1800):05d}" for _ in range(n)],
        "service": rng.choice(
            services,
            size=n,
            p=[0.58, 0.22, 0.10, 0.10]
        ),
        "date_entree": pd.to_datetime("2026-01-01")
        + pd.to_timedelta(rng.integers(0, 270, size=n), unit="D"),
        "duree_jours": rng.integers(0, 21, size=n),
        "diagnostic_principal": rng.choice(
            ["I10", "J18.9", "E11.9", "S72.0", "F32.9", "C50.9", None],
            size=n,
            p=[0.16, 0.16, 0.16, 0.14, 0.12, 0.16, 0.10]
        ),
        "acte_ccam": rng.choice(
            ["HBQK002", "YYYY030", "DEQP003", "ZZLP025", None],
            size=n
        ),
        "mode_entree": rng.choice(
            ["8", "6", "7", None],
            size=n,
            p=[0.65, 0.15, 0.15, 0.05]
        ),
        "mode_sortie": rng.choice(
            ["8", "6", "7", None],
            size=n,
            p=[0.70, 0.10, 0.15, 0.05]
        )
    })

    df["date_sortie"] = (
        df["date_entree"]
        + pd.to_timedelta(df["duree_jours"], unit="D")
    )

    # Quelques incohérences volontairement injectées
    bad_dates = rng.choice(df.index, size=22, replace=False)
    df.loc[bad_dates, "date_sortie"] = (
        df.loc[bad_dates, "date_entree"]
        - pd.to_timedelta(1, unit="D")
    )

    duplicates = rng.choice(df.index[1:], size=18, replace=False)
    df.loc[duplicates, "sejour_id"] = (
        df.loc[duplicates - 1, "sejour_id"].values
    )

    df["diagnostic_manquant"] = df["diagnostic_principal"].isna()

    df["date_incoherente"] = (
        df["date_sortie"] < df["date_entree"]
    )

    df["mode_manquant"] = (
        df["mode_entree"].isna()
        | df["mode_sortie"].isna()
    )

    df["doublon_sejour"] = df["sejour_id"].duplicated(
        keep=False
    )

    df["nb_anomalies"] = (
        df[
            [
                "diagnostic_manquant",
                "date_incoherente",
                "mode_manquant",
                "doublon_sejour"
            ]
        ]
        .astype(int)
        .sum(axis=1)
    )

    df["priorite"] = np.select(
        [
            df["date_incoherente"] | df["doublon_sejour"],
            df["diagnostic_manquant"] | df["mode_manquant"]
        ],
        [
            "Critique",
            "À corriger"
        ],
        default="Conforme"
    )

    def describe_issue(row):
        problems = []

        if row["diagnostic_manquant"]:
            problems.append("Diagnostic principal manquant")

        if row["date_incoherente"]:
            problems.append(
                "Date de sortie antérieure à l'entrée"
            )

        if row["mode_manquant"]:
            problems.append(
                "Mode entrée/sortie manquant"
            )

        if row["doublon_sejour"]:
            problems.append(
                "Identifiant séjour dupliqué"
            )

        return " | ".join(problems) if problems else "Aucune"

    df["anomalie"] = df.apply(
        describe_issue,
        axis=1
    )

    return df


df = generate_demo_data()

st.title("🏥 PMSI Data Quality Dashboard")

st.markdown(
    """
    Démonstrateur de contrôle qualité,
    d'exhaustivité et de cohérence
    des données hospitalières et PMSI.
    """
)

st.info(
    "Les données utilisées sont entièrement synthétiques. "
    "Aucune donnée patient réelle n'est utilisée."
)

# FILTRES
with st.sidebar:

    st.header("Filtres")

    selected_services = st.multiselect(
        "Champ d'activité",
        ["MCO", "SMR", "HAD", "Psychiatrie"],
        default=[
            "MCO",
            "SMR",
            "HAD",
            "Psychiatrie"
        ]
    )

    selected_priorities = st.multiselect(
        "Statut qualité",
        [
            "Critique",
            "À corriger",
            "Conforme"
        ],
        default=[
            "Critique",
            "À corriger",
            "Conforme"
        ]
    )

filtered = df[
    df["service"].isin(selected_services)
    & df["priorite"].isin(selected_priorities)
]

# KPI
total = len(filtered)

anomalies = (
    filtered["nb_anomalies"] > 0
).sum()

critical = (
    filtered["priorite"] == "Critique"
).sum()

quality_score = (
    100
    * (filtered["nb_anomalies"] == 0).mean()
    if total > 0
    else 0
)

exhaustivity = (
    100
    * (
        filtered["diagnostic_principal"].notna()
        & filtered["mode_entree"].notna()
        & filtered["mode_sortie"].notna()
    ).mean()
    if total > 0
    else 0
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Séjours contrôlés",
    total
)

c2.metric(
    "Taux d'exhaustivité",
    f"{exhaustivity:.1f}%"
)

c3.metric(
    "Score qualité",
    f"{quality_score:.1f}%"
)

c4.metric(
    "Anomalies détectées",
    anomalies
)

c5.metric(
    "Anomalies critiques",
    critical
)

st.markdown("---")

# GRAPHIQUES
col1, col2 = st.columns(2)

with col1:

    st.subheader(
        "Anomalies par champ d'activité"
    )

    anomaly_by_service = (
        filtered
        .assign(
            anomalie_flag=
            filtered["nb_anomalies"] > 0
        )
        .groupby(
            "service",
            as_index=False
        )["anomalie_flag"]
        .sum()
    )

    anomaly_by_service.columns = [
        "Service",
        "Nombre d'anomalies"
    ]

    fig = px.bar(
        anomaly_by_service,
        x="Service",
        y="Nombre d'anomalies",
        text="Nombre d'anomalies"
    )

    fig.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.subheader(
        "Répartition de la qualité"
    )

    quality = (
        filtered["priorite"]
        .value_counts()
        .reset_index()
    )

    quality.columns = [
        "Statut",
        "Nombre"
    ]

    fig = px.pie(
        quality,
        values="Nombre",
        names="Statut",
        hole=0.45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# TYPES D'ANOMALIES
st.subheader(
    "Typologie des anomalies"
)

issues = pd.DataFrame({
    "Type": [
        "Diagnostic principal manquant",
        "Date incohérente",
        "Mode entrée/sortie manquant",
        "Séjour dupliqué"
    ],
    "Nombre": [
        filtered[
            "diagnostic_manquant"
        ].sum(),

        filtered[
            "date_incoherente"
        ].sum(),

        filtered[
            "mode_manquant"
        ].sum(),

        filtered[
            "doublon_sejour"
        ].sum()
    ]
})

fig = px.bar(
    issues,
    x="Type",
    y="Nombre",
    text="Nombre"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# TABLEAU DES ANOMALIES
st.subheader(
    "Séjours nécessitant un contrôle"
)

anomaly_table = filtered[
    filtered["nb_anomalies"] > 0
][
    [
        "sejour_id",
        "patient_id",
        "service",
        "date_entree",
        "date_sortie",
        "diagnostic_principal",
        "acte_ccam",
        "priorite",
        "anomalie"
    ]
]

st.dataframe(
    anomaly_table,
    use_container_width=True,
    hide_index=True
)

csv = anomaly_table.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "Télécharger les anomalies",
    data=csv,
    file_name="anomalies_pmsi.csv",
    mime="text/csv"
)

# EVOLUTION TEMPORELLE
st.subheader(
    "Évolution mensuelle du taux de conformité"
)

monthly = df.copy()

monthly["mois"] = (
    monthly["date_entree"]
    .dt.to_period("M")
    .astype(str)
)

monthly["conforme"] = (
    monthly["nb_anomalies"] == 0
)

monthly = (
    monthly
    .groupby(
        "mois",
        as_index=False
    )["conforme"]
    .mean()
)

monthly[
    "Taux de conformité"
] = monthly["conforme"] * 100

fig = px.line(
    monthly,
    x="mois",
    y="Taux de conformité",
    markers=True
)

fig.update_yaxes(
    range=[0, 100]
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# METHODOLOGIE
with st.expander(
    "Voir la méthodologie des contrôles"
):

    st.markdown(
        """
        ### Contrôles simulés

        - diagnostic principal manquant ;
        - date de sortie antérieure à la date d'entrée ;
        - mode d'entrée ou de sortie absent ;
        - séjour dupliqué ;
        - contrôle d'exhaustivité ;
        - priorisation des anomalies.

        ### Logique

        1. Récupération des données
        2. Application des règles qualité
        3. Détection des anomalies
        4. Priorisation
        5. Export des dossiers à vérifier
        6. Suivi des indicateurs

        Dans un environnement réel,
        ces règles seraient adaptées
        aux référentiels PMSI et aux procédures
        de l'établissement.
        """
    )

st.markdown("---")

st.caption(
    "PMSI Data Quality Automation — "
    "adaptation portfolio par Kenewy Diallo | "
    "Données synthétiques uniquement."
)
