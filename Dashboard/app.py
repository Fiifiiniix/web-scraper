import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import json
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

app = dash.Dash(__name__)
app.title = "BTC Dashboard"

# Chemins
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "..", "Scraper", "btc_prices.csv")
report_dir = os.path.join(base_dir, "..", "Reports", "DailyReports")

# Chargement CSV
def load_data():
    df = pd.read_csv(csv_path, names=["datetime", "price"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["price"] = pd.to_numeric(df["price"], errors='coerce')
    df = df.dropna()
    df["sma_10"] = df["price"].rolling(window=10).mean()

    # Régression linéaire sur les 30 derniers points
    if len(df) >= 30:
        X = np.arange(len(df[-30:])).reshape(-1, 1)
        y = df["price"].values[-30:]
        model = LinearRegression().fit(X, y)
        y_pred = model.predict(X)
        df["prediction"] = [None] * (len(df) - 30) + list(y_pred)
    else:
        df["prediction"] = None

    return df

# Chargement rapport JSON
def load_daily_report():
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(report_dir, f"report-{today}.json")
    print(f">>> Chemin recherché : {report_path}")
    print(f">>> Existe ? {os.path.exists(report_path)}")
    if os.path.exists(report_path):
        with open(report_path) as f:
            return json.load(f)
    return None

app.layout = html.Div([
    html.H1("📊 Bitcoin Price Dashboard"),
    html.Div(id="last-update", style={"textAlign": "center", "marginBottom": 20}),
    html.Div(id="last-price", style={"fontSize": 24, "textAlign": "center"}),
    html.Button("🔄 Rafraîchir", id="refresh-button", n_clicks=0, style={"marginBottom": "20px"}),
    dcc.Graph(id="price-graph"),
    html.H2("📝 Rapport journalier"),
    html.Div(id="daily-report"),
    dcc.Interval(id="interval", interval=60*1000, n_intervals=0)
], style={"fontFamily": "Arial", "padding": "20px"})

@app.callback(
    Output("last-price", "children"),
    Output("price-graph", "figure"),
    Output("daily-report", "children"),
    Output("last-update", "children"),
    Input("refresh-button", "n_clicks"),
    Input("interval", "n_intervals")
)

def update_dashboard(n_clicks, n_intervals):
    
    df = load_data()
    latest_price = df["price"].iloc[-1]
    latest_time = df["datetime"].iloc[-1].strftime("%Y-%m-%d %H:%M:%S")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["datetime"], y=df["price"], mode="lines", name="BTC Price"))
    fig.add_trace(go.Scatter(x=df["datetime"], y=df["sma_10"], mode="lines", name="SMA 10"))
    fig.add_trace(go.Scatter(x=df["datetime"], y=df["prediction"], mode="lines", name="Linear Regression"))

    fig.update_layout(title="Évolution du prix BTC (USD)",
                      xaxis_title="Heure",
                      yaxis_title="Prix ($)",
                      xaxis=dict(showgrid=True),
                      yaxis=dict(showgrid=True))

    report = load_daily_report()
    if report:
        table = html.Table([
            html.Tr([html.Th(k), html.Td(f"{v:.2f}" if isinstance(v, float) else v)])
            for k, v in report.items()
        ], style={"margin": "0 auto", "fontSize": 18, "border": "1px solid black"})
    else:
        table = html.Div("Aucun rapport disponible pour aujourd'hui.")

    return (
        f"💰 Dernier prix : {latest_price:.2f} USD (à {latest_time})",
        fig,
        table,
        f"📅 Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0", port=8050)
