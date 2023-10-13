"""
This script monitors specified stocks, compares their prices with historical averages,
and sends email notifications when certain conditions are met.
"""

#Import the necessary libraries and modules
import yfinance as yf
import smtplib
import schedule
import time
import os
from forex_python.converter import CurrencyRates
from dotenv import load_dotenv
from statistics import mean

# Load environment variable from .env file
load_dotenv()

# Initialize currency converter
currency_converter = CurrencyRates()

# Define the stocks to monitor and the email details
stocks_to_monitor = ["LSEG.L", "AZN.L", "RIO.L"]
previous_prices = {ticker: 0 for ticker in stocks_to_monitor}

#Set-up your own environment .env (README)
email_user = os.environ.get('EMAIL_USER')
receiver_email = os.environ.get('RECEIVER_EMAIL')
email_pass = os.environ['EMAIL_PASS']
if email_pass is None:
    print("EMAIL_PASS environment variable not found. Check README")

def check_stock_prices():
    for ticker in stocks_to_monitor:
        stock = yf.Ticker(ticker)

        # Fetch the last 7 days of price data and calculate the average closing price
        hist = stock.history(period="7d")
        seven_day_avg = mean(hist["Close"])

        # Get today's opening price
        today_open = hist.iloc[-1]["Open"]

        # Compare today's opening price with the 7-day average price
        if today_open < seven_day_avg:
            send_notification(ticker, today_open)
        
        # Fetch the current price 
        current_price_usd = stock.info['currentPrice']
        
        # Convert the price from USD to GBP
        current_price_gbp = currency_converter.convert('USD', 'GBP', current_price_usd)
        
        # Convert the previous price from USD to GBP
        previous_price_gbp = currency_converter.convert('USD', 'GBP', previous_prices[ticker])
        
        # Compare the current price with the previous price
        diff = previous_price_gbp - current_price_gbp
        if diff >= 0.01 or diff <= 0.01:
            send_notification(ticker, current_price_gbp)
        
        # Store the price in USD for the next check
        previous_prices[ticker] = current_price_usd

def send_notification(ticker, price):
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(email_user, email_pass)
        subject = f'Price Drop Alert for {ticker}'
        body = f'The price of {ticker} has dropped to {price} GBP.'
        msg = f'Subject: {subject}\n\n{body}'
        server.sendmail(email_user, receiver_email, msg)

# Schedule the check_stock_prices function to run every minute
schedule.every(1).minutes.do(check_stock_prices)

while True:
    schedule.run_pending()
    time.sleep(1)