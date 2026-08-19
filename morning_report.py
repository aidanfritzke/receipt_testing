import datetime
import requests
import yfinance as yf
import feedparser
from pathlib import Path

#############################################################################
################################## WEATHER ##################################

# Coordinates for Tucson, AZ
location = "Tucson, AZ"
LATITUDE = 32.2217
LONGITUDE = -110.9265

# Build URL for current weather and daily highs/lows using Open-Meteo
url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LATITUDE}&longitude={LONGITUDE}"
    f"&current=temperature_2m,relative_humidity_2m,weather_code"
    f"&daily=temperature_2m_max,temperature_2m_min"
    f"&timezone=auto"
)

response_weather = requests.get(url)
response_weather.raise_for_status()
data_weather = response_weather.json()

# Parse current and daily details
current_weather = data_weather["current"]
daily_weather = data_weather["daily"]

temp_c = current_weather["temperature_2m"]
temp_f = (temp_c * 9 / 5) + 32

humidity = current_weather["relative_humidity_2m"]

max_f = (daily_weather["temperature_2m_max"][0] * 9 / 5) + 32
min_f = (daily_weather["temperature_2m_min"][0] * 9 / 5) + 32

now = datetime.datetime.now()
day_name = now.strftime("%A")

weather_code = current_weather["weather_code"]

weather_mapping = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense intensity drizzle",
    56: "Light freezing drizzle", 57: "Dense intensity freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy intensity rain",
    66: "Light freezing rain", 67: "Heavy intensity freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy intensity snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm: Slight or moderate", 96: "Thunderstorm with slight hail", 97: "Thunderstorm with heavy hail"
}

description = weather_mapping.get(weather_code, f"Unknown weather code: {weather_code}")

################################ END WEATHER ################################
#############################################################################
#############################################################################
############################# CALENDAR EVENTS ###############################



########################### END CALENDAR EVENTS #############################
#############################################################################
#############################################################################
################################## TO-DO ####################################

# Define your file paths
input_markdown = Path(r"Z:\commonplace_notes\to-do\todo.md")
    
# save to-do list to print
todo_content = input_markdown.read_text(encoding="utf-8")

# reminders by day of week
if day_name == "Monday":
    reminder_by_day = "Recycling bin to curb"
elif day_name == "Wednesday":
    reminder_by_day = "Leave gate open for pool guy"
else:
    reminder_by_day = f"No reminder for {day_name}"

################################ END TO-DO ##################################
#############################################################################
#############################################################################
############################### TOP HEADLINES ###############################


##################### newsapi.org , delayed by a day... #####################
# response_news = requests.get(
    # "https://newsapi.org/v2/top-headlines",
    # params={
        # "sources": "bbc-news,associated-press",
        # "apiKey": "31acf0fa99c348a88ba2427161109978",
    # },
# )
# articles = response_news.json()["articles"]

# headlines = "\n".join(
    # f'{article.get("source", {}).get("name", "Unknown")}: '
    # f'{article.get("title", "No headline")}'
    # for article in articles[:5]
# )
#############################################################################

HEADLINES_PER_SOURCE = 1  # lines per source; 6 sources so ~18 lines max
 
NEWS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
}
 
# AP and Reuters dropped public RSS years ago - pulled via Google News
# site-search instead. Unofficial, could break if Google changes it.
NEWS_FEEDS = {
    "AP News": (
        "https://news.google.com/rss/search?q=site:apnews.com+when:24h"
        "&hl=en-US&gl=US&ceid=US:en"
    ),
    "BBC News": "https://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": (
        "https://news.google.com/rss/search?q=site:reuters.com+when:24h"
        "&hl=en-US&gl=US&ceid=US:en"
    ),
    # "Tucson Sentinel": "https://www.tucsonsentinel.com/site/rss",
    # "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    # "Channel 5 News": (
        # "https://www.youtube.com/feeds/videos.xml"
        # "?channel_id=UC-AQKm7HUNMmxjdS371MSwg"
    # ),
}
 
headline_lines = []
for source_name, feed_url in NEWS_FEEDS.items():
    try:
        response_news = requests.get(feed_url, headers=NEWS_HEADERS, timeout=10)
        response_news.raise_for_status()
        feed_news = feedparser.parse(response_news.content)
        for entry in feed_news.entries[:HEADLINES_PER_SOURCE]:
            headline_lines.append(f'{source_name}: {entry.get("title", "No headline").strip()}')
    except requests.RequestException:
        headline_lines.append(f"{source_name}: [feed unavailable]")
 
headlines = "\n".join(headline_lines)

############################# END TOP HEADLINES #############################
#############################################################################
#############################################################################
############################### STOCK TICKERS ###############################

# Create the Ticker objects
spfive = yf.Ticker("^GSPC")
vt = yf.Ticker("VT")
bitcoin = yf.Ticker("BTC-USD")

### yes i know the following should be a loop through each ticker object ####

## Get current prices using fast_info
# spfive
current_price_spfive = spfive.fast_info["last_price"]
# vt
current_price_vt = vt.fast_info["last_price"]
# bitcoin
current_price_bitcoin = bitcoin.fast_info["last_price"]

## Get YTD historical data to calculate YTD return
# spfive
hist_ytd_spfive = spfive.history(period="ytd")
start_price_spfive = hist_ytd_spfive["Close"].iloc[0]
latest_close_spfive = hist_ytd_spfive["Close"].iloc[-1]

ytd_return_spfive = ((latest_close_spfive - start_price_spfive) / start_price_spfive) * 100

# vt
hist_ytd_vt = vt.history(period="ytd")
start_price_vt = hist_ytd_vt["Close"].iloc[0]
latest_close_vt = hist_ytd_vt["Close"].iloc[-1]

ytd_return_vt = ((latest_close_vt - start_price_vt) / start_price_vt) * 100

# bitcoin
hist_ytd_bitcoin = bitcoin.history(period="ytd")
start_price_bitcoin = hist_ytd_bitcoin["Close"].iloc[0]
latest_close_bitcoin = hist_ytd_bitcoin["Close"].iloc[-1]

ytd_return_bitcoin = ((latest_close_bitcoin - start_price_bitcoin) / start_price_bitcoin) * 100

############################# END STOCK TICKERS #############################
#############################################################################
#############################################################################
############################### SERVER STATUS ###############################



############################# END SERVER STATUS #############################
#############################################################################
#############################################################################
################################ OTHER NOTES ################################



############################## END OTHER NOTES ##############################
#############################################################################
#############################################################################
############################# SPANISH PRACTICE ##############################


########################### END SPANISH PRACTICE ############################
#############################################################################

# Format the report text
report = (

f"""

Good Morning, today is {day_name}, {now}.

            WEATHER 

Location: {location}
Latitude, Longitude: {LATITUDE, LONGITUDE}
Current Temperature: {temp_f:.1f} °F
Humidity: {humidity}%
Today's High: {max_f:.1f} °F
Today's Low: {min_f:.1f} °F
Weather Code: {current_weather["weather_code"], description}

            CALENDAR EVENTS

null

            TO-DO

{todo_content}

            TOP HEADLINES

{headlines}

            STOCK TICKERS

S&P 500
Current Price: ${current_price_spfive:,.2f}
YTD: {ytd_return_spfive:+.2f}%

VT
Current Price: ${current_price_vt:,.2f}
YTD: {ytd_return_vt:+.2f}%

Bitcoin
Current Price: ${current_price_bitcoin:,.2f}
YTD: {ytd_return_bitcoin:+.2f}%

            SERVER STATUS

null - use paramiko, fabric, scp/sftp

            OTHER NOTES

null

            SPANISH PRACTICE
            
            Present
          (Pefect ?)
 ---------------   ---------------
|      -ar      | |      -ar      |
 ---------------   ---------------
|   o  |  amos  | |      |        |
 ---------------   ---------------
|  as  |  áis   | |      |        |
 ---------------   ---------------
|   a  |   an   | |      |        |
 ---------------   ---------------
 ---------------   ---------------
|   -er / -ir   | |   -er / -ir   |
 ---------------   ---------------
|  o   |  emos  | |      |        |
 ---------------   ---------------
|  es  |  éis   | |      |        |
 ---------------   ---------------
|  e   |   en   | |      |        |
 ---------------   ---------------
 
            Preterite 
        (Completed Past)
 ---------------   ---------------
|      -ar      | |      -ar      |
 ---------------   ---------------
|   é  |  amos  | |      |        |
 ---------------   ---------------
| aste |        | |      |        |
 ---------------   ---------------
|   ó  |  aron  | |      |        |
 ---------------   ---------------
 ---------------   ---------------
|   -er / -ir   | |   -er / -ir   |
 ---------------   ---------------
|   í  |  imos  | |      |        |
 ---------------   ---------------
| iste |        | |      |        |
 ---------------   ---------------
|  ís  | ieron  | |      |        |
 ---------------   ---------------
            Imperfect 
      (Habits / Background)
 ---------------   ---------------
|      -ar      | |      -ar      |
 ---------------   ---------------
| aba  | ábamos | |      |        |
 ---------------   ---------------
| abas |        | |      |        |
 ---------------   ---------------
| aba  |  aban  | |      |        |
 ---------------   ---------------
 ---------------   ---------------
|   -er / -ir   | |   -er / -ir   |
 ---------------   ---------------
|  ía  | íamos  | |      |        |
 ---------------   ---------------
| ías  |        | |      |        |
 ---------------   ---------------
|  ía  | ían    | |      |        |
 ---------------   ---------------
 
CONJUGATE PAST LIKE PRESENT

            Irregulars
ser - era
ir - iba
ver - veía

            Future
 ------------------   ------------------
| -ar / -er / -ir  | | -ar / -er / -ir  |
 ------------------   ------------------
|   é   |   emos   | |       |          |
 ------------------   ------------------
|  ás   |          | |       |          |
 ------------------   ------------------
|   a   |    án    | |       |          |
 ------------------   ------------------
     
CONJUGATE FUTURE BY ADDING ENDING TO INFINITIVE

Escribe como ayer, hoy, y mañana:















"""

    + "\x1b\x64\x04"   # Feed 4 lines
    + "\x1d\x56\x00"   # Full cut

)

# Save to a text file
filename = "morning_report.txt"

# with open(filename, "w") as file:
    # file.write(report)



# ESC/POS printers default to CP437 (single-byte), not UTF-8, so writing
# UTF-8 directly turns accented characters (á, é, ñ...) into garbage.
# Encoding as CP437 here fixes that for anything in its range.
# News feeds sometimes use "smart" quotes/dashes CP437 can't represent -
# swap those for plain ASCII first so the write never raises/crashes.
SMART_PUNCTUATION = {
    "\u2018": "'", "\u2019": "'",   # curly single quotes
    "\u201c": '"', "\u201d": '"',  # curly double quotes
    "\u2013": "-", "\u2014": "-",  # en dash, em dash
    "\u2026": "...",               # ellipsis
}
for smart_char, plain_char in SMART_PUNCTUATION.items():
    report = report.replace(smart_char, plain_char)
 
# errors="replace" swaps anything still outside CP437 for "?" instead of
# crashing the whole report over one stray character.
with open(filename, "w", encoding="cp437", errors="replace") as file:
    file.write(report)