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
base_dir = os.path.dirname(os.path.abspath(__file__))

# Chargement des données
def load_data():
    path = os.path.join(os.path.dirname(__file__), "../Scraper/btc_prices.csv")
    df = pd.read_csv(path, names=["datetime", "price"])
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
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
def load_daily_report(selected_file=None):
    reports_dir = os.path.join(base_dir, "..", "Reports", "DailyReports")
    if selected_file:
        report_path = os.path.join(reports_dir, selected_file)
    else:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        report_path = os.path.join(reports_dir, f"report-{today}.json")
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
                {"label": "1 heure", "value": "last_hour"},
                {"label": "6 heures", "value": "last_6_hours"},
                {"label": "24 heures", "value": "last_day"},
                {"label": "3 jours", "value": "last_3_days"},
                {"label": "7 jours", "value": "last_week"},
                {"label": "Tout", "value": "all"},
            ],
            value="last_day",
            clearable=False,
            style={"width": "200px"}
        )
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    html.Div([
        html.Button("🔁 Rafraîchir", id="refresh-button", n_clicks=0)
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    dcc.Graph(id="price-graph"),

    html.Div([
        html.Label("Historique des rapports", style={"fontWeight": "bold", "marginTop": "30px"}),
        dcc.Dropdown(
            id="report-selector",
            options=[
                {"label": f, "value": f}
                for f in sorted(os.listdir(os.path.join(base_dir, "..", "Reports", "DailyReports")))
                if f.endswith(".json")
            ],
            placeholder="Sélectionner un rapport",
            style={"width": "60%", "margin": "0 auto"}
        ),
    ], style={"textAlign": "center", "marginBottom": "20px"}),

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
    Input("report-selector", "value"),
    Input("time-range-dropdown", "value")
)
def update_dashboard(n_clicks, n_intervals, selected_report, selected_range):
    df = load_data()
    if df.empty:
        return "Pas de données", go.Figure(), "Aucun rapport disponible", ""

    # Filtrage selon la période choisie
    now = datetime.datetime.now()
    time_deltas = {
        "last_hour": datetime.timedelta(hours=1),
        "last_6_hours": datetime.timedelta(hours=6),
        "last_day": datetime.timedelta(days=1),
        "last_3_days": datetime.timedelta(days=3),
        "last_week": datetime.timedelta(weeks=1),
        "all": None
    }

    if selected_range in time_deltas:
        min_time = now - time_deltas[selected_range] if time_deltas[selected_range] else None
        if min_time:
            df_filtered = df[df["datetime"] >= min_time]
        else:
            df_filtered = df
    else:
        df_filtered = df  # fallback de sécurité

    latest_price_text = "Aucune donnée"
    figure = go.Figure()

    if df_filtered.empty:
        latest_price = "Aucune donnée"
        latest_price_text = "Aucune donnée"
        figure = go.figure()
    else:
        latest_price = df_filtered["price"].iloc[-1]
        lastest_price_text = f"{float(latest_price):.2f} USD"

    xaxis_config = {"title": "Date"}

    if not df_filtered.empty:
        if selected_range != "all":
            xaxis_config["range"] = [
                df_filtered["datetime"].min(),
                df_filtered["datetime"].max()
            ]


    figure = {
        "data": [
            go.Scatter(x=df["datetime"], y=df["price"], name="Prix"),
            go.Scatter(x=df["datetime"], y=df["sma_10"], name="Moyenne mobile (10)"),
            go.Scatter(x=df["datetime"], y=df["prediction"], name="Régression linéaire", line={"dash": "dash"})
        ],
        "layout": go.Layout(
            title="Évolution du prix", 
            xaxis=xaxis_config,
            yaxis={"title": "Prix (USD)", "showgrid": True})
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

# Chargement et affichage du rapport journalier sélectionné
    report = load_daily_report(selected_report)
    if report:
        report_text = html.Div([
            html.H4("Résumé journalier"),
            html.Div([
                html.P(f"{key}: {value}") for key, value in report.items()
            ])
        ], style={
            "border": "1px solid #ccc",
            "padding": "20px",
            "borderRadius": "10px",
            "width": "60%",
            "margin": "0 auto",
            "textAlign": "left",
            "backgroundColor": "#f9f9f9"
        })
    else:
        report_text = "Aucun rapport disponible"


    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Dernier prix : {latest_price_text}", figure, report_text, f"Dernière mise à jour : {update_time}"

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
