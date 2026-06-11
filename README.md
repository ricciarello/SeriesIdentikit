# 🎬 Series Identikit

> Scegli 3 serie TV che ami. Scopri che tipo di spettatore sei.

Un'app Streamlit che analizza i tuoi gusti cinematografici tramite le API di TMDb e costruisce una **carta d'identità psicologica** basata sui generi delle serie selezionate — con radar chart, barre di profilo e raccomandazioni personalizzate.

Puoi visitarlo qui 👉🏻 [Series Identikit](https://ricciarello-seriesidentikit.streamlit.app/)

## Demo

*(aggiungi link Streamlit Cloud dopo il deploy)*

## Cosa dimostra (per il CV)

- **Data retrieval da API reale** (TMDb REST API)
- **Feature engineering** su dati categorici (generi → vettore multi-dimensionale)
- **Content-based recommendation** (TMDb recommendations per serie simili)
- **Data visualization** con Plotly (radar chart + bar chart)
- **Streamlit** per deployment rapido di app data-driven

## Setup locale

```bash
git clone https://github.com/tuousername/serieIdentikit
cd serieIdentikit
pip install -r requirements.txt
```

Crea `.streamlit/secrets.toml`:
```toml
TMDB_API_KEY = "la_tua_chiave_tmdb"
```

Poi:
```bash
streamlit run app.py
```

## Ottenere la chiave TMDb

1. Registrati su [themoviedb.org](https://www.themoviedb.org)
2. Vai su Settings → API
3. Richiedi una chiave (tipo: personal/educational)
4. Copia la **API Key (v3 auth)**

## Deploy su Streamlit Cloud

1. Push su GitHub
2. Vai su [share.streamlit.io](https://share.streamlit.io)
3. Collega il repo
4. In **Secrets**, aggiungi: `TMDB_API_KEY = "la_tua_chiave"`
5. Deploy ✅

## Struttura

```
serieIdentikit/
├── app.py               # App principale
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml     # NON committare su GitHub
```

---

*Dati forniti da [TMDb](https://www.themoviedb.org). This product uses the TMDB API but is not endorsed or certified by TMDB.*
