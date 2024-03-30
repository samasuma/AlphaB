import requests
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
import time
from threading import Thread
import yaml
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
coingecko_api_key = os.getenv("COINGECKO_API_KEY")

# Check if any of the required environment variables are missing
if not (bot_token and chat_id and coingecko_api_key):
    raise ValueError("One or more required environment variables are not set.")

buy_price = 4.50  # Your buy price
decrease_threshold = 0.94  # 6% decrease
increase_threshold = 1.07  # 7% increase

def get_rari_data():
    url = "https://api.coingecko.com/api/v3/coins/rarible"
    headers = {"x-cg-demo-api-key": coingecko_api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    market_data = data["market_data"]
    current_price = market_data["current_price"]["usd"]
    total_volume_24h = market_data["total_volume"]["usd"]
    market_cap = market_data["market_cap"]["usd"]
    return current_price, total_volume_24h, market_cap

def check_price_condition():
    global buy_price, last_alert_price_increase  # Include both global variables
    last_alert_price_increase = buy_price  # Initialize or reset at the start
    
    while True:
        current_price, _, _ = get_rari_data()  # Assuming get_rari_data() returns a tuple of three values
        decrease_alert_price = buy_price * decrease_threshold  # Calculate the price for a decrease alert
        increase_alert_price = last_alert_price_increase * increase_threshold  # Calculate the price for an increase alert

        # Check for a decrease in price
        if current_price <= decrease_alert_price:
            message = f"🚨 RARI has decreased more than 6% from your buy price. Consider selling or setting a stop loss. Current price: ${current_price}"
            send_alert(message)
            # Reset decrease alert price based on buy price (or current_price, depending on strategy)
            decrease_alert_price = buy_price * decrease_threshold

        # Check for an increase in price
        elif current_price >= increase_alert_price:
            message = f"💹 RARI has increased more than 7% from the last alert price. Consider taking profits or adjusting your strategy. Current price: ${current_price}"
            send_alert(message)
            # Update last alert price for increases
            last_alert_price_increase = current_price
            # Recalculate increase_alert_price for the next iteration
            increase_alert_price = last_alert_price_increase * increase_threshold

        time.sleep(300)  # Check every 5 minutes



def send_alert(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

def rari(update: Update, context: CallbackContext) -> None:
    current_price, total_volume_24h, market_cap = get_rari_data()
    cst_time = datetime.now(pytz.timezone('America/Chicago')).strftime('%Y-%m-%d %I:%M:%S %p CST')
     # Placeholder for the quantity of RARI purchased. Replace with actual quantity
    quantity_purchased = 2924.70072  # Example quantity purchased
    
    # Initial investment at the buy price, explicitly in USD
    initial_investment_usd = buy_price * quantity_purchased  # This is already in USD
    
    # Current value of your investment based on the current price, in USD
    current_value_of_investment_usd = current_price * quantity_purchased


    # Calculate P&L
    pnl = (current_value_of_investment_usd - initial_investment_usd) / initial_investment_usd * 100
    pnl_status = "🟢" if pnl > 0 else "🔴"
    pnl_message = f"P&L: {pnl_status} {abs(pnl):.2f}%\n"
    pnl_message += f"Initial Investment (USD): ${initial_investment_usd:.2f}\n"
    pnl_message += f"Current Value (USD): ${current_value_of_investment_usd:.2f}"
    

   

    # Calculate ROI in USD
    roi_usd = current_value_of_investment_usd - initial_investment_usd
    roi_status = "💰" if roi_usd > 0 else "💸"  # Use money bag emoji if profit, otherwise use money with wings

    message = (
        f"<b>Current Price (USD):</b> <b>${current_price}</b>\n"
        f"<b>Buy Price (USD):</b> ${buy_price}\n"
        f"<b>P&amp;L:</b> {pnl_status} <b>{abs(pnl):.2f}%</b>\n"
        f"<b>Initial Investment (USD):</b> <b>${initial_investment_usd:.2f}</b>\n"
        f"<b>Current Value (USD):</b> <b>${current_value_of_investment_usd:.2f}</b>\n"
        f"{roi_status} <b>ROI (USD):</b> <b>${roi_usd:.2f}</b>\n"  # Display ROI in USD with emoji
        f"<b>24h Volume (USD):</b> ${total_volume_24h:,}\n"
        f"<b>Market Cap (USD):</b> ${market_cap:,}\n"
        f"<b>Current Time:</b> {cst_time}"
    )
    
    update.message.reply_text(message, parse_mode='HTML')

def main():
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("rari", rari))

    updater.start_polling()

    Thread(target=check_price_condition).start()

    updater.idle()

if __name__ == '__main__':
    main()