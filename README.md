# Uniswap Risk Assessment Score
The Uniswap Pool Analysis Dashboard is a web-based application designed to provide users with comprehensive insights into different Uniswap and Sushiswap pools. It allows users to compare and analyze these pools based on historical data, sourced from TheGraph's Uniswap V2, Uniswap V3, and Sushiswap Subgraphs. The dashboard calculates and displays multiple risk-return ratios for each pool, and based on user's risk preference, it recommends the most suitable pools to invest in.

<img width="799" alt="image" src="https://github.com/RoyalFlush31/uniswap-risk-assessment/assets/76111186/58f2fcc5-7a50-4c74-96ff-f87e9907f372">


### Key Features:
Risk Preference Selection: Users can choose from five predefined risk preferences, ranging from completely risk-on to risk-off. The selection influences the pool recommendations.

### Pool Analysis: 
The dashboard provides analysis for each pool based on several metrics including Sortino Ratio, Sharpe Ratio, Calmar Ratio, Omega Ratio, Maximum Drawdown, Gain-to-pain ratio, and CVaRs ratios.

### Pool Recommendations: 
Based on user's risk preference and timeframe, the dashboard suggests the most suitable pools to invest in.

### Detailed Pool Information: 
When a user selects a pool, a lightbox opens showing detailed information about the pool. This includes general pool information, all the risk-return ratios, and multiple charts such as return net percentage, impermanent loss, and daily volume in USD.

<img width="801" alt="image" src="https://github.com/RoyalFlush31/uniswap-risk-assessment/assets/76111186/d2a66c85-f6b5-46ac-9fd3-f8941b12ef8c">


### Timeframe Selection: 
Users can select the timeframe for which they want to view and analyze the pool data.

### Data Source: 
The dashboard fetches data from TheGraph, particularly the Uniswap V2, Uniswap V3, and Sushiswap Subgraphs.

### Technology Stack:
Front-End: Javascript, HTML, CSS
Back-End: Flask (Python)
Security & Privacy:
The application does not track or store user data, ensuring privacy for all users.

### Future Enhancement:
While the current dashboard uses historical data, future enhancements plan to include real-time data for up-to-the-minute accuracy.

# Detailed Outline
## User Interface:
### Homepage:
Header with the product name and a brief description.
A section for users to select their risk preference and timeframe.
A table or grid view showing different pools along with their calculated ratios.
Each row in the table/grid should be clickable to open a lightbox with more details about the pool.

### Pool Details Lightbox:
Display general pool information at the top.
Show calculated ratios like Sortino, Sharpe, Calmar, Omega, Max Drawdown, gain-to-pain, and CVaRs ratios.
Provide charts for return net percentage, impermanent loss, and daily volume in USD.
Include a "close" button to return to the main dashboard.

## Back-End:
### Data Fetching:
Use TheGraph's APIs to fetch historical data from Uniswap V2, Uniswap V3, and Sushiswap Subgraphs.

### Data Processing:
Calculate the various ratios and returns based on rolling windows.
Processe and prepared the data for display on the dashboard.

### Pool Recommendation Algorithm:
Use user's risk preference and timeframe to filter and sort the pools.
Suggest the most suitable pools to the user based on the processed data.

### Data Updating:
Although the current iteration of the dashboard utilizes historical data, future versions should consider incorporating real-time or regularly updated data to provide users with the most up-to-date pool performance metrics.
Security:

### Data Privacy:
As per the design, no user data is tracked or stored, maintaining user privacy.

## Future Enhancements:
### Real-Time Data:
Incorporate real-time data into the dashboard to keep the pool metrics and recommendations as accurate and current as possible.

### User Customization:
Allow users to customize the dashboard, such as choosing which metrics to display or hide, and saving their preferred settings for future visits.

### Additional Pool Information:
Consider adding more pool-specific information or metrics that may be of interest to users, such as pool size, liquidity, number of swaps, etc.

## How to run:
Run app.py and head to [127.0.0.1](http://127.0.0.1:5001/)
