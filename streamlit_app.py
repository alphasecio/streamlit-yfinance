import streamlit as st
import yfinance as yf

st.subheader("Stocks App")
symbol = st.text_input("Enter a stock symbol", "AAPL")
if st.button("Get Quote"):
    st.json(yf.Ticker(symbol).info)
