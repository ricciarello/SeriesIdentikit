import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from collections import defaultdict
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")  # metti in .env o Streamlit secrets
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w300"

# ── DIMENSIONI PSICOLOGICHE ───────────────────────────────────────────────────
DIMENSIONS = {
    "🔪 Tension & Mistero":   [9648, 80, 53, 10765],   # mystery, crime, thriller, sci-fi
    "💔 Drama Profondo":      [18, 10749, 10751],        # drama, romance, family
    "💥 Action & Adrenalina": [28, 10752, 12],           # action, war, adventure
    "😂 Umorismo":            [35, 16],                  # comedy, animation
    "🚀 Sci-Fi & Fantasy":    [10765, 14, 878],          # sci-fi/fantasy, fantasy, sci-fi
    "🕵️ Crime & Noir":        [80, 9648, 53],            # crime, mystery, thriller
}

DIM_LABELS = list(DIMENSIONS.keys())

# Etichette psicologiche finali per ogni dimensione dominante
PSYCH_LABELS = {
    "🔪 Tension & Mistero":   "Cacciatore di Adrenalina",
    "💔 Drama Profondo":      "Empatico Seriale",
    "💥 Action & Adrenalina": "Amante del Caos",
    "😂 Umorismo":            "Anima Leggera",
    "🚀 Sci-Fi & Fantasy":    "Visionario",
    "🕵️ Crime & Noir":        "Detective Nato",
}

# ── TMDB HELPERS ──────────────────────────────────────────────────────────────
def tmdb_get(endpoint, params=None):
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    params["language"] = "it-IT"
    r = requests.get(f"{TMDB_BASE}{endpoint}", params=params, timeout=8)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False)
def search_series(query: str):
    data = tmdb_get("/search/tv", {"query": query})
    return data.get("results", [])[:5]

@st.cache_data(show_spinner=False)
def get_series_details(series_id: int):
    details  = tmdb_get(f"/tv/{series_id}")
    keywords = tmdb_get(f"/tv/{series_id}/keywords")
    return details, keywords

# ── LOGICA PROFILO ────────────────────────────────────────────────────────────
def compute_profile(series_list):
    """
    Per ogni serie: raccoglie genre_ids.
    Per ogni dimensione: conta quanti genre_ids matchano.
    Normalizza 0-100.
    """
    scores = defaultdict(float)

    for series in series_list:
        genre_ids = set(series.get("genre_ids", []))
        # Se dettagli completi (da get_series_details), usa genres
        if "genres" in series:
            genre_ids = {g["id"] for g in series["genres"]}

        for dim, ids in DIMENSIONS.items():
            matches = len(genre_ids & set(ids))
            scores[dim] += matches

    # Normalizza 0-100
    max_score = max(scores.values()) if scores and max(scores.values()) > 0 else 1
    normalized = {dim: round((scores[dim] / max_score) * 100) for dim in DIM_LABELS}
    return normalized

def get_dominant_traits(profile, top_n=2):
    sorted_traits = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    return [t for t in sorted_traits if t[1] > 0][:top_n]

# ── RECOMMENDATION ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_recommendations(series_ids: tuple):
    """Prende raccomandazioni TMDb per ogni serie, deduplicando."""
    seen = set(series_ids)
    recs = []
    for sid in series_ids:
        data = tmdb_get(f"/tv/{sid}/recommendations")
        for r in data.get("results", [])[:5]:
            if r["id"] not in seen:
                seen.add(r["id"])
                recs.append(r)
    return recs[:6]

# ── RADAR CHART ───────────────────────────────────────────────────────────────
def make_radar(profile: dict):
    labels = list(profile.keys())
    values = list(profile.values())
    values_closed = values + [values[0]]
    labels_closed  = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.25)",
        line=dict(color="#636EFA", width=2.5),
        marker=dict(size=6, color="#636EFA"),
        name="Il tuo profilo",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=9, color="#888"),
                gridcolor="rgba(150,150,150,0.2)",
            ),
            angularaxis=dict(
                tickfont=dict(size=12),
                gridcolor="rgba(150,150,150,0.2)",
            ),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=40, l=60, r=60),
        height=400,
    )
    return fig

# ── UI ────────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="SerieIdentikit",
        page_icon="🎬",
        layout="centered",
    )

    # CSS custom
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .big-title { font-size: 2.6rem; font-weight: 800; text-align: center; margin-bottom: 0; }
    .subtitle  { font-size: 1.1rem; text-align: center; color: #888; margin-bottom: 2rem; }
    .card { background: #1a1a2e; border-radius: 16px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
    .trait-badge {
        display: inline-block;
        background: linear-gradient(135deg, #636EFA, #EF553B);
        color: white; font-weight: 700; font-size: 1rem;
        padding: 0.4rem 1rem; border-radius: 999px; margin: 0.2rem;
    }
    .rec-title { font-weight: 600; font-size: 0.95rem; margin-top: 0.4rem; text-align: center; }
    .rec-year  { font-size: 0.8rem; color: #888; text-align: center; }
    .rec-score { font-size: 0.8rem; color: #FFD700; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="big-title">🎬 SerieIdentikit</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Scegli 3 serie. Scopri chi sei.</div>', unsafe_allow_html=True)

    if not TMDB_API_KEY:
        st.error("⚠️ TMDB_API_KEY non trovata. Aggiungila in `.streamlit/secrets.toml` o come variabile d'ambiente.")
        st.code('TMDB_API_KEY = "la_tua_chiave"', language="toml")
        st.stop()

    # ── SELEZIONE SERIE ───────────────────────────────────────────────────────
    selected_series = []

    for i in range(1, 4):
        st.markdown(f"#### Serie {i}")
        query = st.text_input(f"Cerca serie #{i}", key=f"q{i}", placeholder="es. Breaking Bad, The Bear, Dark...")

        if query:
            with st.spinner("Cerco..."):
                results = search_series(query)

            if not results:
                st.warning("Nessun risultato.")
            else:
                options = {f"{r['name']} ({r.get('first_air_date','?')[:4]})": r for r in results}
                choice = st.selectbox(f"Seleziona serie #{i}", list(options.keys()), key=f"sel{i}")
                if choice:
                    selected_series.append(options[choice])

        st.divider()

    # ── ANALISI ───────────────────────────────────────────────────────────────
    if len(selected_series) == 3:
        if st.button("🔍 Analizza il mio profilo", type="primary", use_container_width=True):
            with st.spinner("Costruisco il tuo identikit..."):

                # Fetch dettagli completi per generi precisi
                enriched = []
                for s in selected_series:
                    details, _ = get_series_details(s["id"])
                    enriched.append(details)

                profile = compute_profile(enriched)
                dominant = get_dominant_traits(profile, top_n=2)

                # ── CARTA D'IDENTITÀ ──────────────────────────────────────────
                st.markdown("---")
                st.markdown("## 🪪 La tua Carta d'Identità")

                col1, col2 = st.columns([1.2, 1])

                with col1:
                    st.markdown("**Il tuo profilo psicologico:**")
                    for dim, score in dominant:
                        label = PSYCH_LABELS.get(dim, dim)
                        st.markdown(
                            f'<span class="trait-badge">{label} {score}%</span>',
                            unsafe_allow_html=True
                        )
                    st.markdown("<br>", unsafe_allow_html=True)

                    # Barre dimensioni
                    df_profile = pd.DataFrame(
                        list(profile.items()), columns=["Dimensione", "Score"]
                    ).sort_values("Score", ascending=True)

                    fig_bar = go.Figure(go.Bar(
                        x=df_profile["Score"],
                        y=df_profile["Dimensione"],
                        orientation="h",
                        marker=dict(
                            color=df_profile["Score"],
                            colorscale="Viridis",
                        ),
                        text=df_profile["Score"].astype(str) + "%",
                        textposition="outside",
                    ))
                    fig_bar.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(range=[0,115], showgrid=False, visible=False),
                        yaxis=dict(tickfont=dict(size=12)),
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=280,
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                with col2:
                    st.markdown("**Radar del tuo profilo:**")
                    st.plotly_chart(make_radar(profile), use_container_width=True)

                # ── RACCOMANDAZIONI ───────────────────────────────────────────
                st.markdown("---")
                st.markdown("## 🎯 Serie consigliate per te")

                series_ids = tuple(s["id"] for s in enriched)
                recs = get_recommendations(series_ids)

                if recs:
                    cols = st.columns(3)
                    for idx, rec in enumerate(recs[:6]):
                        with cols[idx % 3]:
                            if rec.get("poster_path"):
                                st.image(
                                    TMDB_IMG + rec["poster_path"],
                                    use_container_width=True,
                                )
                            year = rec.get("first_air_date", "?")[:4]
                            score = rec.get("vote_average", 0)
                            st.markdown(f'<div class="rec-title">{rec["name"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="rec-year">{year}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="rec-score">⭐ {score:.1f}</div>', unsafe_allow_html=True)
                else:
                    st.info("Nessuna raccomandazione trovata per queste serie.")

    elif 0 < len(selected_series) < 3:
        st.info(f"Seleziona ancora {3 - len(selected_series)} serie per ottenere il tuo identikit.")

    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center; color:#555; font-size:0.8rem;">Dati da <a href="https://www.themoviedb.org" target="_blank">TMDb</a> · Progetto portfolio di Riccardo</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
