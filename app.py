import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from collections import defaultdict
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", st.secrets.get("TMDB_API_KEY", "") if hasattr(st, "secrets") else "")
TMDB_BASE    = "https://api.themoviedb.org/3"
TMDB_IMG     = "https://image.tmdb.org/t/p/w300"

# ── DIMENSIONI PSICOLOGICHE ───────────────────────────────────────────────────
DIMENSIONS = {
    "🔪 Tension & Mistero":   [9648, 80, 53, 10765],
    "💔 Drama Profondo":      [18, 10749, 10751],
    "💥 Action & Adrenalina": [28, 10752, 12],
    "😂 Umorismo":            [35, 16],
    "🚀 Sci-Fi & Fantasy":    [10765, 14, 878],
    "🕵️ Crime & Noir":        [80, 9648, 53],
}
DIM_LABELS = list(DIMENSIONS.keys())

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
    return data.get("results", [])[:6]

@st.cache_data(show_spinner=False)
def get_series_details(series_id: int):
    details  = tmdb_get(f"/tv/{series_id}")
    keywords = tmdb_get(f"/tv/{series_id}/keywords")
    return details, keywords

def compute_profile(series_list):
    scores = defaultdict(float)
    for series in series_list:
        genre_ids = set(series.get("genre_ids", []))
        if "genres" in series:
            genre_ids = {g["id"] for g in series["genres"]}
        for dim, ids in DIMENSIONS.items():
            matches = len(genre_ids & set(ids))
            scores[dim] += matches
    max_score = max(scores.values()) if scores and max(scores.values()) > 0 else 1
    return {dim: round((scores[dim] / max_score) * 100) for dim in DIM_LABELS}

def get_dominant_traits(profile, top_n=2):
    sorted_traits = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    return [t for t in sorted_traits if t[1] > 0][:top_n]

@st.cache_data(show_spinner=False)
def get_recommendations(series_ids: tuple):
    seen = set(series_ids)
    recs = []
    for sid in series_ids:
        data = tmdb_get(f"/tv/{sid}/recommendations")
        for r in data.get("results", [])[:5]:
            if r["id"] not in seen:
                seen.add(r["id"])
                recs.append(r)
    return recs[:6]

def make_radar(profile: dict):
    labels = list(profile.keys())
    values = list(profile.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(99,110,250,0.2)",
        line=dict(color="#636EFA", width=2.5),
        marker=dict(size=6, color="#636EFA"),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=9, color="#888"), gridcolor="rgba(150,150,150,0.2)"),
            angularaxis=dict(tickfont=dict(size=11), gridcolor="rgba(150,150,150,0.2)"),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=50, r=50),
        height=380,
    )
    return fig

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Series Identikit", page_icon="🎬", layout="wide")

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-title {
        font-size: 3.2rem; font-weight: 900; text-align: center;
        background: linear-gradient(135deg, #636EFA, #EF553B, #FFD700);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 0.3rem;
    }
    .hero-desc {
        max-width: 640px; margin: 0 auto 0.5rem auto;
        text-align: center; font-size: 1.05rem; color: #aaa; line-height: 1.7;
    }
    .step-row {
        display: flex; justify-content: center; gap: 2rem;
        margin: 1.2rem auto 2rem auto; max-width: 600px;
    }
    .step-item {
        display: flex; flex-direction: column; align-items: center;
        font-size: 0.85rem; color: #bbb; gap: 0.3rem;
    }
    .step-icon { font-size: 1.8rem; }
    .step-label { font-weight: 600; color: #ddd; }

    .selected-badge {
        display: flex; align-items: center; gap: 0.7rem;
        background: linear-gradient(135deg, #1a1a3e, #2a1a3e);
        border: 1px solid #636EFA44; border-radius: 12px;
        padding: 0.6rem 1rem; margin-top: 0.5rem;
    }
    .selected-badge .s-name { font-weight: 700; font-size: 0.95rem; }
    .selected-badge .s-year { font-size: 0.8rem; color: #888; }
    .selected-badge .s-tick { font-size: 1.2rem; color: #00C896; }

    .trait-badge {
        display: inline-block;
        background: linear-gradient(135deg, #636EFA, #EF553B);
        color: white; font-weight: 700; font-size: 1rem;
        padding: 0.4rem 1.1rem; border-radius: 999px; margin: 0.2rem;
    }
    .rec-card {
        background: #111827; border-radius: 12px;
        padding: 0.5rem; margin-bottom: 0.5rem; text-align: center;
    }
    .rec-title { font-weight: 600; font-size: 0.88rem; margin-top: 0.4rem; }
    .rec-meta  { font-size: 0.78rem; color: #888; }
    .rec-score { font-size: 0.8rem; color: #FFD700; }

    /* Modal overlay */
    .modal-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); z-index: 9999;
        display: flex; align-items: center; justify-content: center;
    }
    .modal-box {
        background: #0f0f1a; border: 1px solid #333; border-radius: 20px;
        padding: 2rem; max-width: 680px; width: 90%; position: relative;
    }

    .how-step {
        display: flex; align-items: flex-start; gap: 1rem;
        background: #1a1a2e; border-radius: 12px; padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .how-num {
        background: linear-gradient(135deg, #636EFA, #EF553B);
        color: white; font-weight: 900; font-size: 1.1rem;
        width: 2rem; height: 2rem; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .how-text h4 { margin: 0 0 0.2rem 0; font-size: 0.95rem; color: #eee; }
    .how-text p  { margin: 0; font-size: 0.85rem; color: #999; line-height: 1.5; }
                
    /* Margini laterali su desktop */
    .block-container {
    max-width: 1100px !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    margin: 0 auto !important;

    .github-link {
    color: #aaa; text-decoration: none;
    display: inline-flex; align-items: center; gap: 6px;
    font-weight: 600; transition: all 0.2s ease;
    }
    .github-link:hover { color: #ffd700; }
    .github-link svg { transition: transform 0.6s ease; }
    .github-link:hover svg { transform: rotate(360deg); }       
    }
                
    </style>
    """, unsafe_allow_html=True)

    # ── HERO ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="hero-title">🎬 SerieIdentikit</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-desc">
        Tre serie TV. Migliaia di dati nascosti dietro ogni titolo.<br>
        <strong>SerieIdentikit</strong> analizza i generi, i pattern narrativi e le affinità
        tra le serie che ami — e costruisce la tua <em>carta d'identità psicologica</em>
        da spettatore. Poi ti dice cosa guardare dopo.
    </div>
    <div class="step-row">
        <div class="step-item"><span class="step-icon">🔍</span><span class="step-label">Cerca</span>3 serie che ami</div>
        <div class="step-item"><span class="step-icon">⚡</span><span class="step-label">Analizza</span>i tuoi pattern</div>
        <div class="step-item"><span class="step-icon">🪪</span><span class="step-label">Scopri</span>chi sei</div>
        <div class="step-item"><span class="step-icon">🎯</span><span class="step-label">Ricevi</span>consigli su misura</div>
    </div>
    """, unsafe_allow_html=True)

    # ── COME FUNZIONA (popup) ─────────────────────────────────────────────────
    col_btn_l, col_btn_m, col_btn_r = st.columns([3,2,3])
    with col_btn_m:
        show_how = st.button("❓ Come funziona?", use_container_width=True)

    if show_how:
        with st.expander("🔬 Come funziona SerieIdentikit", expanded=True):
            st.markdown("""
            <div class="how-step">
                <div class="how-num">1</div>
                <div class="how-text">
                    <h4>Recupero dati da TMDb</h4>
                    <p>Ogni serie che selezioni viene interrogata tramite le API di <strong>The Movie Database (TMDb)</strong>.
                    Recuperiamo generi ufficiali, popolarità e metadati strutturati per ogni titolo.</p>
                </div>
            </div>
            <div class="how-step">
                <div class="how-num">2</div>
                <div class="how-text">
                    <h4>Feature Engineering sui generi</h4>
                    <p>I generi TMDb vengono mappati su <strong>6 dimensioni psicologiche</strong> definite a priori
                    (Tension, Drama, Action, Umorismo, Sci-Fi, Crime). Ogni serie contribuisce con i propri generi
                    a costruire un vettore numerico.</p>
                </div>
            </div>
            <div class="how-step">
                <div class="how-num">3</div>
                <div class="how-text">
                    <h4>Aggregazione e normalizzazione</h4>
                    <p>I vettori delle 3 serie vengono <strong>sommati e normalizzati 0–100</strong>.
                    Il risultato è il tuo profilo: un punto nello spazio a 6 dimensioni che descrive
                    il tuo "gusto cinematografico medio".</p>
                </div>
            </div>
            <div class="how-step">
                <div class="how-num">4</div>
                <div class="how-text">
                    <h4>Raccomandazione content-based</h4>
                    <p>Le serie consigliate vengono recuperate tramite l'endpoint <code>/recommendations</code> di TMDb —
                    un sistema ibrido che combina similarità di contenuto e segnali collaborativi
                    basati sul comportamento di milioni di utenti.</p>
                </div>
            </div>
            <div class="how-step">
                <div class="how-num">5</div>
                <div class="how-text">
                    <h4>Visualizzazione del profilo</h4>
                    <p>Il profilo viene rappresentato con un <strong>radar chart</strong> (le tue dimensioni dominanti)
                    e un <strong>bar chart orizzontale</strong> per confronto immediato tra le dimensioni.
                    Entrambi costruiti con <strong>Plotly</strong>.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    if not TMDB_API_KEY:
        st.error("⚠️ TMDB_API_KEY non trovata. Aggiungila in `.streamlit/secrets.toml`.")
        st.code('TMDB_API_KEY = "la_tua_chiave"', language="toml")
        st.stop()

    # ── SELEZIONE SERIE — 3 colonne ───────────────────────────────────────────
    st.markdown("### 🎬 Scegli le tue 3 serie")
    cols_sel = st.columns(3)
    selected_series = []

    for i, col in enumerate(cols_sel, start=1):
        with col:
            st.markdown(f"**Serie {i}**")
            key_q   = f"q{i}"
            key_sel = f"sel{i}"
            key_confirmed = f"confirmed{i}"

            # Se già confermata, mostra badge e bottone reset
            if st.session_state.get(key_confirmed):
                s = st.session_state[key_confirmed]
                year = s.get("first_air_date", "????")[:4]
                poster = s.get("poster_path")
                st.markdown(f"""
                <div class="selected-badge">
                    <span class="s-tick">✓</span>
                    <div><div class="s-name">{s['name']}</div><div class="s-year">{year}</div></div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("✏️ Cambia", key=f"reset{i}"):
                    del st.session_state[key_confirmed]
                    if key_q in st.session_state:
                        del st.session_state[key_q]
                    st.rerun()
                if poster:
                    st.image(TMDB_IMG + poster, use_container_width=True)
                selected_series.append(s)
            else:
                query = st.text_input(
                    f"Cerca...", key=key_q,
                    placeholder="es. Breaking Bad, Dark, The Bear",
                    label_visibility="collapsed"
                )
                if query:
                    with st.spinner(""):
                        results = search_series(query)
                    if not results:
                        st.warning("Nessun risultato.")
                    else:
                        options = {f"{r['name']} ({r.get('first_air_date','?')[:4]})": r for r in results}
                        choice = st.selectbox("", list(options.keys()), key=key_sel, label_visibility="collapsed")
                        if st.button("✅ Conferma", key=f"conf{i}", use_container_width=True):
                            st.session_state[key_confirmed] = options[choice]
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ANALISI ───────────────────────────────────────────────────────────────
    if len(selected_series) == 3:
        if st.button("🔍 Analizza il mio profilo", type="primary", use_container_width=True):
            with st.spinner("Costruisco il tuo identikit..."):
                enriched = []
                for s in selected_series:
                    details, _ = get_series_details(s["id"])
                    enriched.append(details)

                profile  = compute_profile(enriched)
                dominant = get_dominant_traits(profile, top_n=2)
                series_ids = tuple(s["id"] for s in enriched)
                recs = get_recommendations(series_ids)

            st.markdown("---")
            st.markdown("## 🪪 La tua Carta d'Identità")

            # Badge tratti dominanti
            for dim, score in dominant:
                label = PSYCH_LABELS.get(dim, dim)
                st.markdown(f'<span class="trait-badge">{label} · {score}%</span>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # ── DUE COLONNE: statistiche | raccomandazioni ─────────────────
            left_col, right_col = st.columns([1, 1], gap="large")

            with left_col:
                st.markdown("#### 📊 Il tuo profilo")

                # Bar chart
                df_profile = pd.DataFrame(list(profile.items()), columns=["Dimensione","Score"]).sort_values("Score", ascending=True)
                fig_bar = go.Figure(go.Bar(
                    x=df_profile["Score"], y=df_profile["Dimensione"], orientation="h",
                    marker=dict(color=df_profile["Score"], colorscale="Viridis"),
                    text=df_profile["Score"].astype(str) + "%", textposition="outside",
                ))
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(range=[0,120], showgrid=False, visible=False),
                    yaxis=dict(tickfont=dict(size=12)),
                    margin=dict(t=10, b=10, l=10, r=10), height=260,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # Radar chart
                st.markdown("#### 🕸️ Radar")
                st.plotly_chart(make_radar(profile), use_container_width=True)

            with right_col:
                st.markdown("#### 🎯 Serie consigliate per te")
                if recs:
                    rec_cols = st.columns(3)
                    for idx, rec in enumerate(recs[:6]):
                        with rec_cols[idx % 3]:
                            st.markdown('<div class="rec-card">', unsafe_allow_html=True)
                            if rec.get("poster_path"):
                                st.image(TMDB_IMG + rec["poster_path"], use_container_width=True)
                            year  = rec.get("first_air_date","?")[:4]
                            score = rec.get("vote_average", 0)
                            st.markdown(f'<div class="rec-title">{rec["name"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="rec-meta">{year} · <span class="rec-score">⭐ {score:.1f}</span></div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("Nessuna raccomandazione trovata.")

    elif 0 < len(selected_series) < 3:
        st.info(f"Mancano ancora {3 - len(selected_series)} serie — selezionale e conferma.")

    # # ── FOOTER ────────────────────────────────────────────────────────────────
    # st.markdown("---")
    # st.markdown(
    #     '<p style="text-align:center;color:#555;font-size:0.8rem;">Dati da '
    #     '<a href="https://www.themoviedb.org" target="_blank">TMDb</a> · '
    #     'Progetto portfolio di Riccardo</p>',
    #     unsafe_allow_html=True
    # )

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;color:#555;font-size:0.9rem;">'
        'Dati da <a href="https://www.themoviedb.org" target="_blank" style="color:#aaa;">TMDb</a> · '
        '<a href="https://github.com/ricciarello" target="_blank" rel="noopener" class="github-link">'
        '<svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>'
        '</svg> ricciarello</a></p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
