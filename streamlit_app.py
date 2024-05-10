import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit app details
st.set_page_config(page_title="Financial Analysis", layout="wide")
with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "AAPL")
    button = st.button("Submit")

# Format market cap and enterprise value into a readable value
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

                col1, col2, col3 = st.columns(3)

                # Display stock information as a dataframe
                col1.write("<h2 style='font-size: 20px;'>Stock Information</h2>", unsafe_allow_html=True)
                company = info.get('longName', 'N/A')
                country = info.get('country', 'N/A')
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                market_cap = info.get('marketCap', 'N/A')
                ent_value = info.get('enterpriseValue', 'N/A')

                stock_info = [
                    ("Metric", "Value"),
                    ("Company Name", company),
                    ("Country", country),
                    ("Sector", sector),
                    ("Industry", industry),
                    ("Market Cap", format_value(market_cap)),
                    ("Enterprise Value", format_value(ent_value))
                ]
                
                df = pd.DataFrame(stock_info[1:], columns=stock_info[0])
                col1.dataframe(df, width=400, hide_index=True)

                # Display price information as a dataframe
                col2.write("<h2 style='font-size: 20px;'>Price Information</h2>", unsafe_allow_html=True)
                current_price = info.get('currentPrice', 'N/A')
                prev_close = info.get('previousClose', 'N/A')
                day_high = info.get('dayHigh', 'N/A')
                day_low = info.get('dayLow', 'N/A')
                ft_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
                ft_week_low = info.get('fiftyTwoWeekLow', 'N/A')
                
                price_info = [
                    ("Metric", "Value"),
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
                col3.write("<h2 style='font-size: 20px;'>Business Metrics</h2>", unsafe_allow_html=True)
                forward_eps = info.get('forwardEps', 'N/A')
                forward_pe = info.get('forwardPE', 'N/A')
                peg_ratio = info.get('pegRatio', 'N/A')
                dividend_rate = info.get('dividendRate', 'N/A')
                dividend_yield = info.get('dividendYield', 'N/A')
                recommendation = info.get('recommendationKey', 'N/A')
                
                biz_metrics = [
                    ("Metric", "Value"),
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
