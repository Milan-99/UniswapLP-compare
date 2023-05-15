from flask import Flask, render_template, request, jsonify
import json
import pandas as pd
import plotly
import plotly.graph_objs as go
from src.storage import Pool_Data
from src.risk_score import Pool
import datetime

app = Flask(__name__)

# Renders the main page and handles the POST requests to calculate and return KPI data.
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route('/multi_pool')
def multi_pool():
    return render_template('multi_pool.html')


# An API endpoint that returns both static and dynamic KPIs for a given pool address and risk preference.
@app.route("/api/pool", methods=["GET"])
def get_pool_data():
    pool_address = request.args.get('pool_address')
    risk_preference = request.args.get('risk_preference')
    time_horizon = request.args.get('time_horizon')
    accumulate = request.args.get('accumulate')
    try:
        # Processing of raw csv data
        data = Pool_Data(pool=pool_address).preprocess_data()

        # Cut data_kpis to fit into timeframe (e.g. last 1 day, 14 days, 30 days, etc.)
        if time_horizon != "all":
            data = data[pd.to_datetime(data.index) >= (pd.to_datetime(data.index[-1]) - datetime.timedelta(days=int(time_horizon)))]

        # Creating KPIs and risk score for given data
        pool = Pool(data=data, risk_preference=risk_preference)
        risk_scores = pool.risk_scores
        data_kpis = pool.data

        pd.concat([data, data_kpis]).to_csv("univ3_usdc_eth.csv")

        # Create KPI table
        last_row_ratios = risk_scores.iloc[-1].drop("risk_score").round(8).to_dict()
        last_pool_info = {
            "pool_id": data_kpis["id"].iloc[-1],
            "token0_symbol": data_kpis["token0_symbol"].iloc[-1],
            "token1_symbol": data_kpis["token1_symbol"].iloc[-1],
            "exchange": data_kpis["exchange"].iloc[-1],
            "risk_score": pool.risk_scores["risk_score"].iloc[-1].round(2),
            "return_net_percentage": data_kpis["return_net_percentage"].sum().round(2),
            "impermanent_loss_percentage": data_kpis["impermanent_loss_percentage"].iloc[-1].round(4),
            "daily_volumeUSD": data_kpis["daily_volumeUSD"].iloc[-1].round(2),
            "accrued_fees": data_kpis["accrued_fees"].iloc[-1].round(4),
            "volume_to_reserve_ratio": data_kpis["volume_to_reserve_ratio"].iloc[-1].round(2),
            "reserveUSD": data_kpis["reserveUSD"].iloc[-1].round(2)
        }

        # Create charts
        total_risk_score = pool.risk_scores["risk_score"].to_dict()
        return_net_percentage = data_kpis["return_net_percentage"].cumsum().to_dict() if accumulate else data_kpis["return_net_percentage"].to_dict()
        impermanent_loss_percentage = data_kpis["impermanent_loss_percentage"].to_dict() if accumulate else data_kpis["impermanent_loss_percentage"].diff().to_dict()
        volume_to_reserve = data_kpis["volume_to_reserve_ratio"].to_dict() if accumulate else data_kpis["volume_to_reserve_ratio"].diff().to_dict()
        daily_volumeUSD = data_kpis["daily_volumeUSD"].to_dict() if accumulate else data_kpis["daily_volumeUSD"].diff().to_dict()

        def notnull_to_dict(series):
            return {k: (v if pd.notnull(v) else None) for k, v in series.items()}

        # Replace repetitive code with the new function
        result = {
            "pool_info": notnull_to_dict(last_pool_info),
            "static_kpis": notnull_to_dict(last_row_ratios),
            "dynamic_kpis": {
                "risk_score": notnull_to_dict(total_risk_score),
                "return_net_percentage": notnull_to_dict(return_net_percentage),
                "impermanent_loss_percentage": notnull_to_dict(impermanent_loss_percentage),
                "volume_to_reserve": notnull_to_dict(volume_to_reserve),
                "daily_volumeUSD": notnull_to_dict(daily_volumeUSD)
            }
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/get_data/<kpi>")
def get_data(kpi):
    data = Pool_Data(pool=request.args.get("pool_address")).preprocess_data()
    pool = Pool(data=data, risk_preference="Pussy")
    kpi_data = pool.data[kpi]
    fig = go.Figure(go.Scatter(x=kpi_data[kpi].index, y=kpi_data[kpi], mode='lines', name=kpi))
    fig.update_layout(title=f"{kpi}")
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
