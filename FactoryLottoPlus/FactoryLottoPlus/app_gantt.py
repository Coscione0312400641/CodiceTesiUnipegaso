'''Nessun conflitto Duplicate callback outputs.

Un solo callback gestisce la logica di rigenerazione e filtro dei grafici.

Mantiene in memoria i dati tramite dcc.Store.

Si converte poi una stringa in datetime usando un formato
 
che tiene conto della parte decimale dei secondi 

usando format='mixed' (opzione se i formati variano). 
'''

from dash import Dash, dcc, html, Input, Output, State, callback_context
import plotly.express as px
import pandas as pd
import datetime
from FactoryLottoPlus import genera_dati_lotti

app = Dash(__name__)
app.title = "Simulazione Gantt Produzione"

app.layout = html.Div([
    html.H1("Report Gantt Produzione", style={"textAlign": "center"}),

    html.Div([
        html.Label("Filtra per Prodotto"),
        dcc.Dropdown(id="filtro-prodotto", multi=True),

        html.Label("Filtra per Fase"),
        dcc.Dropdown(
            id="filtro-fase",
            options=[{"label": f, "value": f} for f in ["Taglio", "Assemblaggio", "Qualità"]],
            multi=True
        ),

        html.Label("Intervallo Orario (h)"),
        dcc.RangeSlider(
            id="filtro-orario",
            min=0, max=48, step=1, value=[0, 48],
            marks={i: str(i) for i in range(0, 49, 4)}
        ),

        html.Label("Numero Addetti"),
        dcc.Slider(id="num-operatori", min=1, max=5, step=1, value=2,
                   marks={i: str(i) for i in range(1, 6)}),

        html.Br(),
        html.Button("Rigenera Simulazione", id="btn-rigenera", n_clicks=0),
        html.Br(), html.Br(),
        html.Button("Esporta CSV", id="btn-export", n_clicks=0),
        dcc.Download(id="download-csv")
    ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "padding": "10px"}),

    html.Div([
        dcc.Graph(id="grafico-gantt"),
        dcc.Graph(id="grafico-statistiche"),
        dcc.Graph(id="grafico-occupazione")
    ], style={"width": "68%", "display": "inline-block", "padding": "10px", "verticalAlign": "top"}),

    dcc.Store(id="dati-simulazione-store")
])

@app.callback(
    Output("grafico-gantt", "figure"),
    Output("filtro-prodotto", "options"),
    Output("filtro-prodotto", "value"),
    Output("dati-simulazione-store", "data"),
    Output("grafico-statistiche", "figure"),
    Output("grafico-occupazione", "figure"),
    Input("btn-rigenera", "n_clicks"),
    Input("filtro-prodotto", "value"),
    Input("filtro-fase", "value"),
    Input("filtro-orario", "value"),
    State("num-operatori", "value"),
    State("dati-simulazione-store", "data")
)
def aggiorna_grafici(n_clicks, prodotti, fasi, orario, num_operatori, dati_store):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "btn-rigenera" or not dati_store:
        dati = genera_dati_lotti(num_operatori)
        df = pd.DataFrame(dati)
        df["Lotto_Prodotto"] = df.apply(lambda x: f"Lotto {x['Lotto']} ({x['Prodotto']})", axis=1)
        base_day = datetime.datetime(2024, 1, 1, 0, 0)
        df["Inizio"] = df["Inizio"].apply(lambda h: base_day + datetime.timedelta(hours=h))
        df["Fine"] = df["Fine"].apply(lambda h: base_day + datetime.timedelta(hours=h))

        prodotti = sorted(df["Prodotto"].unique())
        dropdown_options = [{"label": p, "value": p} for p in prodotti]
        prodotti_filtrati = prodotti
        dati_store = df.to_dict("records")
    else:
        df = pd.DataFrame(dati_store)
        df["Inizio"] = pd.to_datetime(df["Inizio"], format='mixed')
        df["Fine"] = pd.to_datetime(df["Fine"], format='mixed')
        df["Lotto_Prodotto"] = df.apply(lambda x: f"Lotto {x['Lotto']} ({x['Prodotto']})", axis=1)

        prodotti_filtrati = prodotti or sorted(df["Prodotto"].unique())
        dropdown_options = [{"label": p, "value": p} for p in sorted(df["Prodotto"].unique())]

    if prodotti_filtrati:
        df = df[df["Prodotto"].isin(prodotti_filtrati)]
    if fasi:
        df = df[df["Fase"].isin(fasi)]
    if orario:
        inizio, fine = orario
        df = df[(df["Inizio"].dt.hour + df["Inizio"].dt.minute / 60 >= inizio) &
                (df["Inizio"].dt.hour + df["Inizio"].dt.minute / 60 <= fine)]

    fig = px.timeline(
        df,
        x_start="Inizio", x_end="Fine", y="Lotto_Prodotto", color="Fase",
        title="Diagramma di Gantt - Produzione Lotti",
        labels={"Lotto_Prodotto": "Lotto"},
        color_discrete_map={"Taglio": "skyblue", "Assemblaggio": "orange", "Qualità": "green"}
    )
    fig.update_yaxes(autorange="reversed")

    df["Durata"] = (df["Fine"] - df["Inizio"]).dt.total_seconds() / 3600
    stat_df = df.groupby(["Prodotto", "Fase"])["Durata"].agg(["count", "mean", "sum"]).reset_index()
    fig_stat = px.bar(stat_df, x="Fase", y="sum", color="Prodotto", barmode="group",
                      title="Tempo Totale per Fase e Prodotto (h)",
                      labels={"sum": "Tempo Totale (h)"})

    timeline = [{"start": row["Inizio"], "end": row["Fine"]} for _, row in df.iterrows()]
    timeline.sort(key=lambda x: x["start"])

    occupazione = []
    base_day = datetime.datetime(2024, 1, 1, 0, 0)
    current_time = timeline[0]["start"] if timeline else base_day
    end_time = timeline[-1]["end"] if timeline else base_day

    while current_time < end_time:
        count = sum(1 for t in timeline if t["start"] <= current_time < t["end"])
        occupazione.append({"time": current_time, "occupati": count})
        current_time += datetime.timedelta(minutes=15)

    df_occupazione = pd.DataFrame(occupazione)
    fig_occupazione = px.line(df_occupazione, x="time", y="occupati",
                              title="Occupazione Operatori nel Tempo",
                              labels={"time": "Ora", "occupati": "Operatori Occupati"})

    return fig, dropdown_options, prodotti_filtrati, dati_store, fig_stat, fig_occupazione

@app.callback(
    Output("download-csv", "data"),
    Input("btn-export", "n_clicks"),
    State("dati-simulazione-store", "data"),
    prevent_initial_call=True
)
def esporta_csv(n_clicks, dati_memorizzati):
    df = pd.DataFrame(dati_memorizzati)
    return dcc.send_data_frame(df.to_csv, "report_produzione.csv", index=False)

if __name__ == "__main__":
    app.run(debug=True)
