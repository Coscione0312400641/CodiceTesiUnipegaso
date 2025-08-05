'''
Created on 23 giu 2025

@author: gianp
'''
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import datetime

# Importa la funzione che genera i dati dalla simulazione
from FactoryLottoPlus import genera_dati_lotti
# Funzione per preparare i DataFrame e il grafico
def crea_grafico_gantt():
    dati = genera_dati_lotti()

    df = pd.DataFrame(dati)
    df["Lotto_Prodotto"] = df.apply(lambda x: f"Lotto {x['Lotto']} ({x['Prodotto']})", axis=1)

    base_day = datetime.datetime(2024, 1, 1, 0, 0)
    df["Inizio"] = df["Inizio"].apply(lambda h: base_day + datetime.timedelta(hours=h))
    df["Fine"] = df["Fine"].apply(lambda h: base_day + datetime.timedelta(hours=h))

    fig = px.timeline(
        df,
        x_start="Inizio",
        x_end="Fine",
        y="Lotto_Prodotto",
        color="Fase",
        title="Diagramma di Gantt - Produzione Lotti",
        labels={"Lotto_Prodotto": "Lotto"},
        color_discrete_map={"Taglio": "skyblue", "Assemblaggio": "orange", "Qualità": "green"}
    )
    fig.update_yaxes(autorange="reversed")

    return fig

# Crea l'app Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Report Gantt Produzione", style={"textAlign": "center"}),
    html.Button("Rigenera Simulazione", id="btn-rigenera", n_clicks=0, style={"margin": "10px"}),
    dcc.Graph(id="grafico-gantt", figure=crea_grafico_gantt())
])

# Callback per aggiornare il grafico
@app.callback(
    Output("grafico-gantt", "figure"),
    Input("btn-rigenera", "n_clicks")
)
def aggiorna_grafico(n_clicks):
    return crea_grafico_gantt()

if __name__ == "__main__":
    app.run(debug=True)
