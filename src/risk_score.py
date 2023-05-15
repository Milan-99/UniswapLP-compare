import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class Pool:
    def __init__(self, data, swap_fee=0.003, risk_preference="Greed", rolling_window_ratio=0.1) -> None:
        self.data = self.calculate_kpis(data, swap_fee=swap_fee, rolling_window_ratio=rolling_window_ratio)
        # Pass the entire Series of each ratio to the calculate_risk_score function
        self.risk_scores = self.calculate_risk_score(risk_preference=risk_preference)


    def calculate_kpis(self, data, swap_fee=None, rolling_window_ratio=0.1):
              # Calculate rolling window size based on the total number of data points and the rolling_window_ratio
        rolling_window_size = min(int(len(data) * rolling_window_ratio), len(data))
        # Check if swap_fee is provided
        if swap_fee is None and not data["swapfee"].empty:
            swap_fee = float(data["swapfee"].iloc[0])

         # Remove rows where 'volumeUSD' is smaller than the previous row
        data = data[data['volumeUSD'] >= data['volumeUSD'].shift()]
        # Compute the cumulative maximum of 'volumeUSD'
        data['cummax_volumeUSD'] = data['volumeUSD'].cummax()

        # Find rows where 'volumeUSD' is less than the cumulative maximum in the previous row
        mask = data['volumeUSD'] >= data['cummax_volumeUSD'].shift(fill_value=0)

        # Filter the DataFrame to keep only valid rows
        data = data[mask]

        data['daily_volumeUSD'] = data['volumeUSD'].diff()

        # Helper functions for Impermanent loss calculation
        # Calculate Impermanent loss
        def impermanent_loss_v2(price_ratio_change):
            return 2 * np.sqrt(price_ratio_change) / (1 + price_ratio_change) - 1
        
        def v0_v1_vheld(P, L, p_a, p_b, k):
            L_l = np.log(p_b / P) - np.log(p_a / P)
            V_0 = L * P / L_l
            V_1 = L * P * k / L_l
            V_held = L * (P * k + P) / (L_l * (1 + k))
            return V_0, V_1, V_held

        def impermanent_loss_v3_k(P, L, p_a, p_b, k):
            V_0, V_1, V_held = v0_v1_vheld(P, L, p_a, p_b, k)
            return (V_held - V_1) / V_0
        
        def impermanent_loss_v3(price_ratio_change, P, L, p_a=1000, p_b=4000):
            IL_a_b_k = impermanent_loss_v3_k(P, L, p_a, p_b, price_ratio_change)
            IL_k = impermanent_loss_v2(price_ratio_change)
            return IL_a_b_k - IL_k

        # Calculate Impermanent loss
        data['price_ratio_start'] = data['reserve0'] / data['reserve1']
        first_percentage = max(int(len(data['price_ratio_start']) * 0.01), 1)
        initial_reserve0 = data['reserve0'][:first_percentage].mean()
        initial_reserve1 = data['reserve1'][:first_percentage].mean()
        L = np.sqrt(initial_reserve0 * initial_reserve1)

        # Calculate IL
        initial_price_ratio = data['price_ratio_start'][:first_percentage].mean()
        data['price_ratio_change'] = data['price_ratio_start'] / initial_price_ratio
        
        #data['impermanent_loss'] = data.apply(lambda row: impermanent_loss_v3(row['price_ratio_change'], P=initial_price_ratio, L=row['L']) if row['exchange'] == 'UniV3' else impermanent_loss_v2(row['price_ratio_change']), axis=1)
        data['impermanent_loss'] = data.apply(lambda row: impermanent_loss_v2(row['price_ratio_change']), axis=1)

        # Calculate other KPIs
        data['net_earnings_daily'] = (data['daily_volumeUSD'] * swap_fee / data['reserveUSD']).fillna(0)
        data['volume_to_reserve_ratio'] = (data['daily_volumeUSD'] / data['reserveUSD']) * 100
        data['fee_revenue_per_liquidity'] = data['daily_volumeUSD'] * swap_fee / (data['reserve0'] + data['reserve1'])
        data['accrued_fees'] = data['daily_volumeUSD'] * swap_fee
        data['gain_loss_percentage'] = ((data['reserveUSD'].diff() + data['accrued_fees']) / data['reserveUSD'].shift(1))
        data['impermanent_loss_percentage'] = data['impermanent_loss'] * 100

        # Calculate constant product and its percentage change
        data['constant_product'] = data['reserve0'] * data['reserve1']
        data['constant_product_change'] = data['constant_product'].pct_change().fillna(0)

        data['return_net'] = data['net_earnings_daily'] + data['impermanent_loss'].diff().fillna(0)
        data = data.dropna(subset=['return_net'], axis=0)
        print(data[["net_earnings_daily", "impermanent_loss", "return_net", "gain_loss_percentage"]].round(6))

        # Calculate return_net_percentage
        data['return_net_percentage'] = data['return_net'] * 100

        # Calculate ratios based on KPIs
        self.calculate_performance_ratios(data, rolling_window_size)
        

        return data

    def calculate_performance_ratios(self, data, rolling_window_size, epsilon = 1e-8):
        # Calculate cumulative returns
        data['cumulative_return_net'] = data['return_net'].cumsum()
        data['cumulative_negative_return_net'] = data.loc[data['return_net'] < 0, 'return_net'].abs().cumsum().fillna(method='ffill').fillna(0)
        data['gain_to_pain_ratio'] = data['cumulative_return_net'] / data['cumulative_negative_return_net'].abs().fillna(1)

        # Calculate Sortino Ratios & Sharpe Ratios
        excess_return = data['return_net']
        excess_return.fillna(epsilon, inplace=True)
        rolling_mean = excess_return.rolling(window=rolling_window_size).mean()
        rolling_std = excess_return.rolling(window=rolling_window_size).std() + epsilon
        downside_std = excess_return.rolling(window=rolling_window_size).apply(lambda x: x[x < 0].std(ddof=1), raw=True)
        data['sharpe_ratio'] = np.sqrt(rolling_window_size) * (rolling_mean / (rolling_std + epsilon))
        data['sortino_ratio'] = np.sqrt(rolling_window_size) * (rolling_mean / (downside_std + epsilon))

        # Calculate CVaR
        confidence_level = 0.05
        data['cvar'] = -data['return_net'].rolling(window=rolling_window_size).quantile(confidence_level).fillna(epsilon)

        # Calculate Omega Ratio
        MAR = 0
        data['gain'] = data['return_net'].clip(lower=MAR) - MAR
        data['loss'] = data['return_net'].clip(upper=MAR) - MAR
        gain_mean = data['gain'].rolling(window=rolling_window_size).mean() + 1e-8
        loss_mean = abs(data['loss'].rolling(window=rolling_window_size).mean()) + 1e-8
        data['omega_ratio'] = gain_mean / loss_mean

        # Calculate Maximum Drawdown
        cumulative_return = (1 + data['return_net']).cumprod()
        data['rolling_max'] = cumulative_return.rolling(window=rolling_window_size, min_periods=1).max()
        data['drawdown'] = (cumulative_return / data['rolling_max']) - 1
        data['maximum_drawdown'] = data['drawdown'].rolling(window=rolling_window_size, min_periods=1).min()

        # Calculate Rolling Calmar Ratio
        data['rolling_average_daily_return'] = data['return_net'].rolling(window=rolling_window_size).mean()
        data['calmar_ratio'] = data['rolling_average_daily_return'] / data['maximum_drawdown'].abs()
        self.data = data

    def calculate_risk_score(self, risk_preference):
        weights_dict = {
        "Greed": {
            # Performance weights: Sharpe, Sortino, Calmar, Gain-to-Pain
            "perf_weights": (0.35, 0.35, 0.15, 0.15),
            # Risk weights: Inverted CVaR, Positive Maximum Drawdown, Omega
            "risk_weights": (0.10, 0.10, 0.80),
            "risk_aversion": 0.3
        },
        "Risk_loving": {
            "perf_weights": (0.30, 0.30, 0.20, 0.20),
            "risk_weights": (0.20, 0.20, 0.60),
            "risk_aversion": 0.4
        },
        "Neutral": {
            "perf_weights": (0.25, 0.25, 0.25, 0.25),
            "risk_weights": (0.33, 0.33, 0.34),
            "risk_aversion": 0.5
        },
        "Risk_averse": {
            "perf_weights": (0.20, 0.20, 0.30, 0.30),
            "risk_weights": (0.40, 0.40, 0.20),
            "risk_aversion": 0.6
        },
        "Pussy": {
            "perf_weights": (0.15, 0.15, 0.35, 0.35),
            "risk_weights": (0.60, 0.30, 0.10),
            "risk_aversion": 0.7
            }
        }
        perf_weights = weights_dict[risk_preference]["perf_weights"]
        risk_weights = weights_dict[risk_preference]["risk_weights"]
        
        # Invert CVaR & Make max_drawdown positive
        inverted_cvars = -self.data['cvar'] + 1
        positive_max_drawdowns = self.data['maximum_drawdown'] + 1

        # Normalize each ratio, handling NaN values and individual ratio ranges
        def normalize(series: pd.Series, min_value: float, max_value: float):
            clipped_series = series.clip(min_value, max_value)
            return ((clipped_series - min_value) / (max_value - min_value)).fillna(0)
        
        # Define the minimum and maximum values for each ratio
        min_max_values = {
            "sharpe_ratios": (-3, 3),
            "sortino_ratios": (-3, 3),
            "inverted_cvars": (0, 1),
            "omega_ratios": (0, 6),
            "max_drawdowns": (0, 1),
            "calmar_ratios": (-3, 3),
            "gain_to_pain_ratios": (0, 3)
        }

        # Calculate the weighted sums for performance and risk
        performance_scores = (
            perf_weights[0] * normalize(self.data['sharpe_ratio'], *min_max_values["sharpe_ratios"]) +
            perf_weights[1] * normalize(self.data['sortino_ratio'], *min_max_values["sortino_ratios"]) +
            perf_weights[2] * normalize(self.data['calmar_ratio'], *min_max_values["calmar_ratios"]) +
            perf_weights[3] * normalize(self.data['gain_to_pain_ratio'], *min_max_values["gain_to_pain_ratios"])
        )

        risk_scores = (
            risk_weights[0] * normalize(inverted_cvars, *min_max_values["inverted_cvars"]) +
            risk_weights[1] * normalize(positive_max_drawdowns, *min_max_values["max_drawdowns"]) +
            risk_weights[2] * normalize(self.data['omega_ratio'], *min_max_values["omega_ratios"])
        )

        # Combine performance and risk scores using a weighted harmonic mean
        risk_aversion = float(weights_dict[risk_preference]["risk_aversion"])
        risk_performance_scores = (1 - ((1 - risk_aversion) * performance_scores + risk_aversion * risk_scores)) * 100

        # Assign risk scores to a new column named "risk_score"
        risk_score_df = pd.DataFrame({
            "sharpe_ratios": self.data['sharpe_ratio'],
            "sortino_ratios": self.data['sortino_ratio'],
            "cvars": self.data['cvar'],
            "omega_ratios": self.data['omega_ratio'],
            "max_drawdowns": self.data['maximum_drawdown'],
            "calmar_ratios": self.data['calmar_ratio'],
            "gain_to_pain_ratios": self.data['gain_to_pain_ratio'],
            "risk_score": risk_performance_scores
        })

        return risk_score_df
