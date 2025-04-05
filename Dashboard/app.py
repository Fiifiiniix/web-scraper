import os
import json
import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objs as go
from dash import Dash, html, dcc, Input, Output, State, ctx

app = Dash(__name__)
app.title = "BTC Price Dashboard"

# Chargement des données
def load_data():
    path = os.path.join(os.path.dirname(__file__), "../Scraper/btc_prices.csv")
    df = pd.read_csv(path, names=["datetime", "price"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["sma_10"] = df["price"].rolling(window=10).mean()

    # Prédiction linéaire simple
    df["timestamp"] = df["datetime"].astype(np.int64) // 10 ** 9
    X = df["timestamp"].values.reshape(-1, 1)
    y = df["price"].values
    if len(X) > 1:
        model = LinearRegression()
        model.fit(X, y)
        df["prediction"] = model.predict(X)
    else:
        df["prediction"] = df["price"]

    return df

# Chargement du rapport
def load_daily_report():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(os.path.dirname(__file__), "../Reports/DailyReports", f"report-{today}.json")
    print(">>> Chemin recherché :", report_path)
    print(">>> Existe ?", os.path.exists(report_path))
    if os.path.exists(report_path):
        with open(report_path) as f:
            return json.load(f)
    return None

# Layout de l'application
app.layout = html.Div([
    html.H1("📊 Tableau de bord - Prix du Bitcoin", style={"textAlign": "center"}),

    html.Div(id="last-price", style={"textAlign": "center", "fontSize": 24, "marginBottom": "10px"}),
    html.Div(id="last-update", style={"textAlign": "center", "fontSize": 16, "marginBottom": "20px"}),

    html.Div([
        html.Label("Période à afficher :"),
        dcc.Dropdown(
            id="time-range-dropdown",
            options=[
                {"label": "30 minutes", "value": "30min"},
                {"label": "1 heure", "value": "1h"},
                {"label": "12 heures", "value": "12h"},
                {"label": "24 heures", "value": "24h"},
                {"label": "Tout", "value": "all"}
            ],
            value="1h",
            clearable=False,
            style={"width": "200px"}
        )
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    html.Div([
        html.Button("🔁 Rafraîchir", id="refresh-button", n_clicks=0)
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    dcc.Graph(id="price-graph"),

    html.Div(id="daily-report", style={"margin": "0 auto", "width": "60%", "fontSize": 18, "marginTop": "40px"}),
    
    html.Div([
        html.Button("📥 Télécharger CSV", id="btn_csv", n_clicks=0),
        dcc.Download(id="download-dataframe-csv"),
        html.Button("📥 Télécharger rapport JSON", id="btn_json", n_clicks=0),
        dcc.Download(id="download-dataframe-json")
    ], style={"marginTop": "30px", "textAlign": "center"}),

    dcc.Interval(id="interval", interval=60*1000, n_intervals=0)  # toutes les 60 secondes
], style={"fontFamily": "Arial, sans-serif", "padding": "20px"})


# Callback pour tout mettre à jour
@app.callback(
    Output("last-price", "children"),
    Output("price-graph", "figure"),
    Output("daily-report", "children"),
    Output("last-update", "children"),
    Input("refresh-button", "n_clicks"),
    Input("interval", "n_intervals"),
    Input("time-range-dropdown", "value")
)
def update_dashboard(n_clicks, n_intervals, selected_range):
    df = load_data()

    # Filtrage selon la période choisie
    now = datetime.datetime.now()
    if selected_range != "all":
        time_deltas = {
            "30min": datetime.timedelta(minutes=30),
            "1h": datetime.timedelta(hours=1),
            "12h": datetime.timedelta(hours=12),
            "24h": datetime.timedelta(hours=24)
        }
        min_time = now - time_deltas[selected_range]
        df = df[df["datetime"] >= min_time]

    latest_price = df["price"].iloc[-1]
    figure = {
        "data": [
            go.Scatter(x=df["datetime"], y=df["price"], name="Prix"),
            go.Scatter(x=df["datetime"], y=df["sma_10"], name="Moyenne mobile (10)"),
            go.Scatter(x=df["datetime"], y=df["prediction"], name="Régression linéaire", line={"dash": "dash"})
        ],
        "layout": go.Layout(title="Évolution du prix", xaxis={"title": "Date"}, yaxis={"title": "Prix (USD)", "showgrid": True})
    }

    report = load_daily_report()
    if report:
        report_text = html.Div(
        [
            html.H3("📄 Rapport journalier", style={"textAlign": "center", "marginBottom": "20px"}),
            html.Ul([
                html.Li(f"Nombre de points : {report.get('count')}"),
                html.Li(f"Heure de début : {report.get('start_time')}"),
                html.Li(f"Heure de fin : {report.get('end_time')}"),
                html.Li(f"Premier prix : {report.get('first')} USD"),
                html.Li(f"Dernier prix : {report.get('last')} USD"),
                html.Li(f"Minimum : {report.get('min')} USD"),
                html.Li(f"Maximum : {report.get('max')} USD"),
                html.Li(f"Moyenne : {report.get('mean')} USD"),
            ])
        ],
        style={
            "width": "50%",
            "margin": "30px auto",
            "padding": "20px",
            "border": "2px solid #ccc",
            "borderRadius": "10px",
            "backgroundColor": "#fefefe",
            "boxShadow": "0px 2px 12px rgba(0,0,0,0.1)",
            "textAlign": "left"
        }
    )

    else:
        report_text = html.Div([
            html.H3("📄 Rapport journalier"),
            html.P("Aucun rapport disponible pour aujourd'hui.")
        ])

    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Dernier prix : {latest_price:.2f} USD", figure, report_text, f"Dernière mise à jour : {update_time}"

# Télécharger le fichier CSV
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True
)
def download_csv(n_clicks):
    df = pd.read_csv("Scraper/btc_prices.csv", names=["datetime", "price"])
    return dcc.send_data_frame(df.to_csv, "btc_prices.csv")


# Télécharger le rapport JSON
app.callback(
    Output("download-dataframe-json", "data"),
    Input("btn_json", "n_clicks"),
    prevent_initial_call=True,
)
def download_json(n_clicks):
    df = pd.read_csv("Scraper/btc_prices.csv", names=["datetime", "price"])
    return dict(content=df.to_json(orient="records", indent=2), filename="btc_prices.json")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
