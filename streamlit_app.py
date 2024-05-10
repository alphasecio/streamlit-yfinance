import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit app details
st.set_page_config(page_title="Financial Analysis", layout="wide")
with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "AAPL")
    period = st.selectbox("Enter a time frame", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)
    button = st.button("Submit")

# Format market cap and enterprise value into something readable
def format_value(value):
    suffixes = ["", "K", "M", "B", "T"]
    suffix_index = 0
    while value >= 1000 and suffix_index < len(suffixes) - 1:
        value /= 1000
        suffix_index += 1
    return f"${value:.1f}{suffixes[suffix_index]}"

# If Submit button is clicked
if button:
    if not ticker.strip():
        st.error("Please provide a valid stock ticker.")
    else:
        try:
            with st.spinner('Please wait...'):
                # Retrieve stock data
                stock = yf.Ticker(ticker)
                info = stock.info

                st.subheader(f"{ticker} - {info.get('longName', 'N/A')}")

                # Plot historical stock price data
                if period == "1D":
                    history = stock.history(period="1d", interval="1h")
                elif period == "5D":
                    history = stock.history(period="5d", interval="1d")
                elif period == "1M":
                    history = stock.history(period="1mo", interval="1d")
                elif period == "6M":
                    history = stock.history(period="6mo", interval="1wk")
                elif period == "YTD":
                    history = stock.history(period="ytd", interval="1mo")
                elif period == "1Y":
                    history = stock.history(period="1y", interval="1mo")
                elif period == "5Y":
                    history = stock.history(period="5y", interval="3mo")
                
                chart_data = pd.DataFrame(history["Close"])
                st.line_chart(chart_data)

                col1, col2, col3 = st.columns(3)

                # Display stock information as a dataframe
                country = info.get('country', 'N/A')
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                market_cap = info.get('marketCap', 'N/A')
                ent_value = info.get('enterpriseValue', 'N/A')
                employees = info.get('fullTimeEmployees', 'N/A')

                stock_info = [
                    ("Stock Info", "Value"),
                    ("Country", country),
                    ("Sector", sector),
                    ("Industry", industry),
                    ("Market Cap", format_value(market_cap)),
                    ("Enterprise Value", format_value(ent_value)),
                    ("Employees", employees)
                ]
                
                df = pd.DataFrame(stock_info[1:], columns=stock_info[0])
                col1.dataframe(df, width=400, hide_index=True)
                
                # Display price information as a dataframe
                current_price = info.get('currentPrice', 'N/A')
                prev_close = info.get('previousClose', 'N/A')
                day_high = info.get('dayHigh', 'N/A')
                day_low = info.get('dayLow', 'N/A')
                ft_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
                ft_week_low = info.get('fiftyTwoWeekLow', 'N/A')
                
                price_info = [
                    ("Price Info", "Value"),
                    ("Current Price", f"${current_price:.2f}"),
                    ("Previous Close", f"${prev_close:.2f}"),
                    ("Day High", f"${day_high:.2f}"),
                    ("Day Low", f"${day_low:.2f}"),
                    ("52 Week High", f"${ft_week_high:.2f}"),
                    ("52 Week Low", f"${ft_week_low:.2f}")
                ]
                
                df = pd.DataFrame(price_info[1:], columns=price_info[0])
                col2.dataframe(df, width=400, hide_index=True)

                # Display business metrics as a dataframe
                forward_eps = info.get('forwardEps', 'N/A')
                forward_pe = info.get('forwardPE', 'N/A')
                peg_ratio = info.get('pegRatio', 'N/A')
                dividend_rate = info.get('dividendRate', 'N/A')
                dividend_yield = info.get('dividendYield', 'N/A')
                recommendation = info.get('recommendationKey', 'N/A')
                
                biz_metrics = [
                    ("Business Metrics", "Value"),
                    ("EPS (FWD)", f"{forward_eps:.2f}"),
                    ("P/E (FWD)", f"{forward_pe:.2f}"),
                    ("PEG Ratio", f"{peg_ratio:.2f}"),
                    ("Div Rate (FWD)", f"${dividend_rate:.2f}"),
                    ("Div Yield (FWD)", f"{dividend_yield * 100:.2f}%"),
                    ("Recommendation", recommendation.capitalize())
                ]
                
                df = pd.DataFrame(biz_metrics[1:], columns=biz_metrics[0])
                col3.dataframe(df, width=400, hide_index=True)

        except Exception as e:
            st.exception(f"An error occurred: {e}")
