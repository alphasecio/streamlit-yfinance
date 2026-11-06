import logging
import re

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf
from yfinance.exceptions import YFRateLimitError

logger = logging.getLogger(__name__)

TICKER_PATTERN = re.compile(r"^[A-Z0-9.\-=^]{1,15}$")
PERIOD_MAP = {
    "1D": ("1d", "1h"),
    "5D": ("5d", "1d"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1wk"),
    "YTD": ("ytd", "1mo"),
    "1Y": ("1y", "1mo"),
    "5Y": ("5y", "3mo"),
}

# Streamlit app details
st.set_page_config(page_title="Financial Analysis", layout="wide")
with st.sidebar:
    st.title("Financial Analysis")
    ticker = st.text_input("Enter a stock ticker (e.g. AAPL)", "AAPL")
    period = st.selectbox("Enter a time frame", tuple(PERIOD_MAP), index=2)
    submit = st.button("Submit")


# Cache Yahoo responses so repeat lookups don't hit Yahoo again (fewer rate-limit errors)
@st.cache_data(ttl=900, show_spinner=False)
def load_info(symbol):
    return yf.Ticker(symbol).info


@st.cache_data(ttl=900, show_spinner=False)
def load_history(symbol, period, interval):
    return yf.Ticker(symbol).history(period=period, interval=interval)


@st.cache_data(ttl=21600, show_spinner=False)
def load_earnings_dates(symbol):
    return yf.Ticker(symbol).get_earnings_dates(limit=12)


# Format market cap and enterprise value into something readable
def format_value(value):
    if not isinstance(value, (int, float)):
        return "N/A"
    sign, value = ("-" if value < 0 else ""), abs(value)
    suffixes = ["", "K", "M", "B", "T"]
    suffix_index = 0
    while value >= 1000 and suffix_index < len(suffixes) - 1:
        value /= 1000
        suffix_index += 1
    return f"{sign}${value:.1f}{suffixes[suffix_index]}"


def safe_format(value, fmt="{:.2f}", fallback="N/A"):
    try:
        return fmt.format(value) if value is not None else fallback
    except (ValueError, TypeError):
        return fallback


def to_naive(index_or_ts):
    tz = getattr(index_or_ts, "tz", None) or getattr(index_or_ts, "tzinfo", None)
    return index_or_ts.tz_localize(None) if tz is not None else index_or_ts


# Close-to-close move around each earnings report.
# Reports before noon are treated as pre-market, later ones as after the close.
def earnings_moves(earnings, closes):
    closes = closes.copy()
    closes.index = to_naive(closes.index).normalize()
    results = []
    for ts in earnings.index:
        ts = to_naive(pd.Timestamp(ts))
        day = ts.normalize()
        if 0 < ts.hour < 12:
            after, before = closes[closes.index >= day], closes[closes.index < day]
        else:
            after, before = closes[closes.index > day], closes[closes.index <= day]
        if after.empty or before.empty:
            continue
        prev_close, next_close = before.iloc[-1], after.iloc[0]
        results.append({
            "Earnings Date": day.date(),
            "Price Date": after.index[0].date(),
            "Change (%)": round((next_close - prev_close) / prev_close * 100, 2),
        })
    return pd.DataFrame(results)


# If Submit button is clicked
if submit:
    symbol = ticker.strip().upper()
    if not TICKER_PATTERN.match(symbol):
        st.error("Please provide a valid stock ticker, e.g. AAPL or BRK-B.")
    else:
        try:
            with st.spinner("Fetching data...", show_time=True):
                info = load_info(symbol)
                st.subheader(f"{symbol} - {info.get('longName', 'N/A')}")

                # Plot historical stock price data
                selected_period, interval = PERIOD_MAP[period]
                history = load_history(symbol, selected_period, interval)
                st.line_chart(history["Close"])

                col1, col2, col3 = st.columns(3)

                # Display stock information as a dataframe
                employees = info.get("fullTimeEmployees")
                stock_info = [
                    ("Stock Info", "Value"),
                    ("Country", info.get("country", "N/A")),
                    ("Sector", info.get("sector", "N/A")),
                    ("Industry", info.get("industry", "N/A")),
                    ("Market Cap", format_value(info.get("marketCap"))),
                    ("Enterprise Value", format_value(info.get("enterpriseValue"))),
                    ("Employees", f"{employees:,}" if isinstance(employees, int) else "N/A"),
                ]
                df = pd.DataFrame(stock_info[1:], columns=stock_info[0]).astype(str)
                col1.dataframe(df, width=400, hide_index=True)

                # Display price information as a dataframe
                price_info = [
                    ("Price Info", "Value"),
                    ("Current Price", safe_format(info.get("currentPrice"), fmt="${:.2f}")),
                    ("Previous Close", safe_format(info.get("previousClose"), fmt="${:.2f}")),
                    ("Day High", safe_format(info.get("dayHigh"), fmt="${:.2f}")),
                    ("Day Low", safe_format(info.get("dayLow"), fmt="${:.2f}")),
                    ("52 Week High", safe_format(info.get("fiftyTwoWeekHigh"), fmt="${:.2f}")),
                    ("52 Week Low", safe_format(info.get("fiftyTwoWeekLow"), fmt="${:.2f}")),
                ]
                df = pd.DataFrame(price_info[1:], columns=price_info[0]).astype(str)
                col2.dataframe(df, width=400, hide_index=True)

                # Display business metrics as a dataframe
                recommendation = info.get("recommendationKey") or "N/A"
                biz_metrics = [
                    ("Business Metrics", "Value"),
                    ("EPS (FWD)", safe_format(info.get("forwardEps"))),
                    ("P/E (FWD)", safe_format(info.get("forwardPE"))),
                    ("PEG Ratio", safe_format(info.get("pegRatio"))),
                    ("Div Rate (FWD)", safe_format(info.get("dividendRate"), fmt="${:.2f}")),
                    ("Div Yield (FWD)", safe_format(info.get("dividendYield"), fmt="{:.2f}%")),
                    ("Recommendation", str(recommendation).replace("_", " ").capitalize()),
                ]
                df = pd.DataFrame(biz_metrics[1:], columns=biz_metrics[0]).astype(str)
                col3.dataframe(df, width=400, hide_index=True)

                # Display earnings moves for the last 12 quarters
                earnings = load_earnings_dates(symbol)
                daily = load_history(symbol, "3y", "1d")
                moves = earnings_moves(earnings, daily["Close"]) if earnings is not None and not earnings.empty else pd.DataFrame()

                if moves.empty:
                    st.info("No earnings history available for this ticker.")
                else:
                    st.subheader("Price moves after earnings")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.dataframe(
                            moves,
                            width=400,
                            height=450,
                            hide_index=True,
                            column_config={"Change (%)": st.column_config.NumberColumn(format="%.2f%%")},
                        )
                    with col2:
                        chart_data = moves.assign(**{"Earnings Date": moves["Earnings Date"].astype(str)})
                        chart = alt.Chart(chart_data).mark_bar().encode(
                            x=alt.X("Earnings Date:N", sort="ascending"),
                            y=alt.Y("Change (%):Q"),
                            color=alt.when(alt.datum["Change (%)"] > 0)
                            .then(alt.value("green"))
                            .otherwise(alt.value("red")),
                            tooltip=["Earnings Date", "Price Date", alt.Tooltip("Change (%):Q", format=".2f")],
                        ).properties(height=450)
                        st.altair_chart(chart, width="stretch")

        except YFRateLimitError:
            st.warning("Yahoo Finance is rate-limiting requests right now. Please wait a minute and try again.")
        except Exception:
            logger.exception("Failed to load data for %s", symbol)
            st.error(f"Couldn't load data for {symbol}. Check the ticker and try again.")
