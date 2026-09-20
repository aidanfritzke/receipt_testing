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

# Define your file paths
input_calendar = Path(r"Z:\khal_calendar\calendar_today.md")
    
# save to-do list to print
calendar_content = input_calendar.read_text(encoding="utf-8")

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
    reminder_by_day = "- [ ] Recycling bin to curb"
elif day_name == "Wednesday":
    reminder_by_day = "- [ ] Leave gate open for pool guy"
elif day_name == "Thursday":
    reminder_by_day = "- [ ] Set fantasy football lineup"
else:
    reminder_by_day = f"No reminder for {day_name}"

################################ END TO-DO ##################################
#############################################################################
#############################################################################
############################### TOP HEADLINES ###############################


# stdlib only - imported here so the import block up top stays untouched
import calendar
import html
import re
import textwrap
import time

RECEIPT_COLS = 42              # TM-T88IV, Font A on 80mm paper
WRAP_WIDTH = RECEIPT_COLS - 1  # spare column so a full line + "\n" can't double-feed
MAX_STORY_AGE_H = 24           # skip feed entries older than this
MAX_STORIES = 8                # total printed; each is ~3-6 lines, so this is the paper budget
STORIES_PER_SOURCE = 3         # cap per feed so one outlet can't crowd out the rest
SUMMARY_CHARS = 220            # trim the dek / why to roughly this many characters
HIGHLIGHT_CHARS = 380          # safety cap on dek + one sentence of story context
FETCH_ARTICLE_PAGES = True     # fetch the article when the feed only has a dek

NEWS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
}

# Direct outlet feeds carry a 1-2 sentence summary (the "highlight").
# Axios bodies carry a "Why it matters:" paragraph (the "why").
# Reuters dropped public RSS years ago - pulled via Google News site-search
# instead, which returns the title only. Unofficial, could break if Google
# changes it. Order matters: stories are picked round-robin from the top.
NEWS_FEEDS = {
    "BBC World":    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Axios":        "https://api.axios.com/feed/",
    "NPR Politics": "https://feeds.npr.org/1014/rss.xml",
    "Reuters":      (
        "https://news.google.com/rss/search?q=site:reuters.com/world+when:24h"
        "&hl=en-US&gl=US&ceid=US:en"
    ),
    "White House":  "https://www.whitehouse.gov/presidential-actions/feed/",
    "Fed":          "https://www.federalreserve.gov/feeds/press_all.xml",
    "NYT World":    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "Politico":     "https://rss.politico.com/politics-news.xml",
    "NPR World":    "https://feeds.npr.org/1004/rss.xml",
    # "Al Jazeera":     "https://www.aljazeera.com/xml/rss/all.xml",
    # "Foreign Policy": "https://foreignpolicy.com/feed/",
    # "State Dept":     "https://www.state.gov/rss-feed/press-releases/feed/",
    # "UN News":        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    # "EU Commission":  "https://ec.europa.eu/commission/presscorner/api/rss?language=en",
}

# Primary sources are policy decisions by definition - skip the keyword filter.
PRIMARY_SOURCES = {"White House", "Fed"}
# White House "summary" is the full order text; Reuters (Google News) just
# repeats the title. Print the headline only for these.
TITLE_ONLY_SOURCES = {"White House", "Reuters"}

# Think tanks and non-partisan research bodies publish analysis, not news:
# a few items a day, on-topic by nature. They get their own block under an
# ANALYSIS header, a wider window, no keyword filter, and one item each -
# the newest that isn't a per-bill cost estimate, event, or podcast.
# ANALYSIS_FEEDS = {
    # "Atlantic Council": "https://www.atlanticcouncil.org/feed/",
    # "CFR":              "https://www.cfr.org/feed",
    # "CBO":              "https://www.cbo.gov/publications/all/rss.xml",
    # "Foreign Affairs": "https://www.foreignaffairs.com/rss.xml",
    # "RAND":            "https://www.rand.org/blog.xml",
    # "GAO":             "https://www.gao.gov/rss/reports.xml",
    # "CRS":             "https://www.everycrsreport.com/rss.xml",
# }
# ANALYSIS_AGE_H = 72         # think tanks publish slowly
# ANALYSIS_PER_SOURCE = 1
# ANALYSIS_CANDIDATES = 6     # recent items considered per source before picking
# ANALYSIS_SKIP = re.compile(  # title patterns never worth receipt paper
    # r"^(S|H\.R|H\.J\.Res|S\.J\.Res|H\.Con\.Res|S\.Con\.Res)\. ?\d+|"
    # r"under suspension of the rules|podcast|webinar|please join|q&a",
    # re.IGNORECASE,
# )

# General current events - no topic filter, just whatever else happened that
# the feeds above didn't cover. Morning Brew posts ~2 stories a day, timed so
# they're about a day old at 6am, hence the wider window.
GENERAL_FEEDS = {
    "Morning Brew": "https://www.morningbrew.com/feed",
}
GENERAL_AGE_H = 36
GENERAL_STORIES = 3         # total across GENERAL_FEEDS, after dedupe

# Crude topic filter on title + summary + why: foreign affairs and decisions
# by policy makers. Anything not matching is dropped, so tune freely.
POLICY_TERMS = re.compile(
    r"\b("
    r"sanctions?|tariffs?|duties|treaty|ceasefire|truce|peace (talks|deal)|"
    r"executive order|proclamation|veto(es|ed)?|"
    r"congress|senate|senators?|house (passes|votes|approves)|lawmakers|legislation|"
    r"supreme court|ruling|federal reserve|fed|rate (cut|hike|decision)|"
    r"nato|united nations|un|european union|eu|summit|"
    r"president|prime minister|minister|chancellor|parliament|elections?|"
    r"pentagon|state department|white house|embassy|troops|missiles?|airstrikes?|"
    r"diplomat\w*|foreign (policy|minister|secretary)|trade deal|"
    r"immigration|visas?|deport\w*"
    r")\b",
    re.IGNORECASE,
)


def clean_html(text):
    """Strip tags and entities, collapse whitespace. Captions, asides, and
    scripts go first so they can't run into the prose (Morning Brew puts
    photo credits in <figcaption>); NPR's "(Image credit: ...)" tail too."""
    text = re.sub(
        r"<(figure|figcaption|aside|script|style)\b.*?</\1>", " ", text or "",
        flags=re.S | re.I,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\(Image credit:[^)]*\)", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def first_sentences(text, max_chars=SUMMARY_CHARS, min_sentences=1, max_sentences=None):
    """Leading whole sentences of text, up to roughly max_chars. Always takes
    at least min_sentences (hard-cut if they alone exceed max_chars), never
    more than max_sentences."""
    # Split after . ! ? even with no space before the next capital -
    # stripped HTML paragraphs often run together.
    sentences = re.split(r"(?<=[.!?])(?<!\b[A-Z]\.)\s*(?=[A-Z\"'])", text)
    out = ""
    for index, sentence in enumerate(sentences):
        if index >= min_sentences and (
            len(out) + len(sentence) + 1 > max_chars
            or (max_sentences and index >= max_sentences)
        ):
            break
        out = f"{out} {sentence}".strip()
    if len(out) > max_chars:
        out = out[: max_chars - 3].rsplit(" ", 1)[0] + "..."
    return out


PAGE_BOILERPLATE = re.compile(
    r"cookie|subscribe|sign up|newsletter|all rights reserved|follow us|"
    r"advertisement|does not offer or accept money",
    re.IGNORECASE,
)


def fetch_article_paragraphs(url, title, dek):
    """Opening paragraphs of an article page, or "" if the site won't serve
    them to a script (NYT and Politico 403 - those stories stay dek-only)."""
    try:
        response_page = requests.get(url, headers=NEWS_HEADERS, timeout=10)
        response_page.raise_for_status()
    except requests.RequestException:
        return ""
    page = response_page.text
    already_printed = {tuple(title.lower().split()[:5]), tuple(dek.lower().split()[:5])}
    paragraphs = []
    # <article> first, then <main> (NPR wraps only a teaser in <article>).
    # No whole-page fallback - that picks up footers and disclaimers.
    for tag in ("article", "main"):
        scope = re.search(rf"<{tag}\b.*?</{tag}>", page, re.S)
        if not scope:
            continue
        for raw in re.findall(r"<p\b[^>]*>(.*?)</p>", scope.group(0), re.S):
            paragraph = clean_html(raw)
            if (
                len(paragraph) > 60
                and paragraph[-1] in ".!?\"'"  # skips headline-in-a-<p> (BBC)
                and tuple(paragraph.lower().split()[:5]) not in already_printed
                and not PAGE_BOILERPLATE.search(paragraph)
            ):
                paragraphs.append(paragraph)
        if paragraphs:
            break
    return " ".join(paragraphs[:2])


def add_context(story):
    """Extend the highlight past the dek by one sentence of the story - from
    the feed body when it has one, else from the article page."""
    dek = story["summary"]
    if story["source"] in TITLE_ONLY_SOURCES or not dek:
        return
    text = story["body"]
    if len(text) < len(dek) + 60 and FETCH_ARTICLE_PAGES:  # feed had only the dek
        text = fetch_article_paragraphs(story["link"], story["title"], dek) or text
    if not text.startswith(dek[:40]):  # article doesn't open with the dek - prepend it
        if dek[-1] not in ".!?\"'":  # some deks have no full stop (Morning Brew)
            dek += "."
        text = f"{dek} {text}".strip()
    story["summary"] = first_sentences(text, HIGHLIGHT_CHARS, min_sentences=2, max_sentences=2)


def fetch_stories(source_name, feed_url, max_age_h=MAX_STORY_AGE_H,
                  limit=STORIES_PER_SOURCE, topic_filter=True):
    """Return [{source, title, summary, why}] for one feed, feed order."""
    response_news = requests.get(feed_url, headers=NEWS_HEADERS, timeout=10)
    response_news.raise_for_status()
    feed_news = feedparser.parse(response_news.content)

    cutoff = time.time() - max_age_h * 3600
    stories = []
    for entry in feed_news.entries:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published and calendar.timegm(published) < cutoff:  # feedparser gives UTC
            continue

        title = clean_html(entry.get("title", "No headline"))
        title = re.sub(r"\s+-\s+Reuters$", "", title)  # Google News suffix
        # The highlight comes from summary (the dek). The "why" is searched in
        # whichever of summary/content is fuller: some feeds put the article
        # in content (Axios), others only a WordPress "The post ... appeared
        # first on ..." footer there (Atlantic Council). Strip that footer.
        footer = r"\s*The post .+? appeared first on .+$"
        summary_text = re.sub(footer, "", clean_html(entry.get("summary")))
        content_text = re.sub(
            footer, "", clean_html((entry.get("content") or [{}])[0].get("value"))
        )

        why = ""
        why_match = re.search(
            r"Why it matters:\s*(.+)", max(summary_text, content_text, key=len)
        )
        if why_match:
            why = first_sentences(why_match.group(1))

        summary = ""
        if source_name not in TITLE_ONLY_SOURCES:
            lede = (summary_text or content_text).split("Why it matters:")[0]
            summary = first_sentences(lede)

        if topic_filter and source_name not in PRIMARY_SOURCES and not POLICY_TERMS.search(
            f"{title} {summary} {why}"
        ):
            continue

        stories.append({
            "source": source_name, "title": title, "summary": summary, "why": why,
            # fuller text (when the feed has it) and link, for add_context later
            "body": max(summary_text, content_text, key=len).split("Why it matters:")[0],
            "link": entry.get("link", ""),
        })
        if len(stories) >= limit:
            break
    return stories


def story_key(story):
    """First few words of the title - catches the same story across outlets."""
    return " ".join(re.findall(r"[a-z0-9]+", story["title"].lower())[:6])


def render_story(story):
    lines = [textwrap.fill(f"{story['source']}: {story['title']}", WRAP_WIDTH)]
    for label, text in (("", story["summary"]), ("WHY: ", story["why"])):
        if text:
            lines.append(textwrap.fill(
                label + text, WRAP_WIDTH, initial_indent="  ", subsequent_indent="  "
            ))
    return "\n".join(lines)


stories_by_source = {}
unavailable_sources = []
for source_name, feed_url in NEWS_FEEDS.items():
    try:
        stories_by_source[source_name] = fetch_stories(source_name, feed_url)
    except requests.RequestException:
        unavailable_sources.append(source_name)

# Round-robin across sources so one outlet doesn't fill the whole section,
# skipping stories an earlier feed already covered.
selected_stories, seen_keys = [], set()
for round_index in range(STORIES_PER_SOURCE):
    for stories in stories_by_source.values():
        if round_index >= len(stories) or len(selected_stories) >= MAX_STORIES:
            continue
        key = story_key(stories[round_index])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        selected_stories.append(stories[round_index])

for story in selected_stories:  # only the ones that will print get a page fetch
    add_context(story)
headline_blocks = [render_story(story) for story in selected_stories]
if not headline_blocks:
    headline_blocks.append(f"[no matching stories in the last {MAX_STORY_AGE_H}h]")

# analysis_blocks = []
# for source_name, feed_url in ANALYSIS_FEEDS.items():
    # try:
        # analysis_stories = fetch_stories(
            # source_name, feed_url, max_age_h=ANALYSIS_AGE_H,
            # limit=ANALYSIS_CANDIDATES, topic_filter=False,
        # )
    # except requests.RequestException:
        # unavailable_sources.append(source_name)
        # continue
    # analysis_stories = [
        # story for story in analysis_stories if not ANALYSIS_SKIP.search(story["title"])
    # ]
    # analysis_blocks.extend(
        # render_story(story) for story in analysis_stories[:ANALYSIS_PER_SOURCE]
    # )
# if analysis_blocks:  # header only when there's something under it
    # headline_blocks.append("            ANALYSIS")
    # headline_blocks.extend(analysis_blocks)

general_blocks = []
for source_name, feed_url in GENERAL_FEEDS.items():
    try:
        general_stories = fetch_stories(
            source_name, feed_url, max_age_h=GENERAL_AGE_H,
            limit=GENERAL_STORIES * 2, topic_filter=False,  # spares for dedupe
        )
    except requests.RequestException:
        unavailable_sources.append(source_name)
        continue
    for story in general_stories:
        key = story_key(story)
        if key in seen_keys or len(general_blocks) >= GENERAL_STORIES:
            continue
        seen_keys.add(key)
        add_context(story)
        general_blocks.append(render_story(story))
if general_blocks:
    headline_blocks.append("            ALSO IN THE NEWS")
    headline_blocks.extend(general_blocks)

if unavailable_sources:
    headline_blocks.append(textwrap.fill(
        "Feeds unavailable: " + ", ".join(unavailable_sources), WRAP_WIDTH
    ))

headlines = "\n\n".join(headline_blocks)

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
IN:     I breathe in
OUT:    I breathe out
IN:     I am grateful for this day
OUT:    I am present to enjoy in

"""

    + "\x1b\x64\x04"   # Feed 4 lines
    + "\x1d\x56\x00"   # Full cut

+ f"""

Good Morning, today is {day_name}, {now}.

            CALENDAR

{calendar_content}
            
            TO-DO

{reminder_by_day}
{todo_content}

            WEATHER 

Location: {location}
Latitude, Longitude: {LATITUDE, LONGITUDE}
Current Temperature: {temp_f:.1f} °F
Humidity: {humidity}%
Today's High: {max_f:.1f} °F
Today's Low: {min_f:.1f} °F
Weather Code: {current_weather["weather_code"], description}

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

"""

    + "\x1b\x64\x04"   # Feed 4 lines
    + "\x1d\x56\x00"   # Full cut

# + f"""
            # SPANISH PRACTICE
            
            # Present
          # (Pefect ?)
 # ---------------   ---------------
# |      -ar      | |      -ar      |
 # ---------------   ---------------
# |   o  |  amos  | |      |        |
 # ---------------   ---------------
# |  as  |  áis   | |      |        |
 # ---------------   ---------------
# |   a  |   an   | |      |        |
 # ---------------   ---------------
 # ---------------   ---------------
# |   -er / -ir   | |   -er / -ir   |
 # ---------------   ---------------
# |  o   |  emos  | |      |        |
 # ---------------   ---------------
# |  es  |  éis   | |      |        |
 # ---------------   ---------------
# |  e   |   en   | |      |        |
 # ---------------   ---------------
 
            # Preterite 
        # (Completed Past)
 # ---------------   ---------------
# |      -ar      | |      -ar      |
 # ---------------   ---------------
# |   é  |  amos  | |      |        |
 # ---------------   ---------------
# | aste |        | |      |        |
 # ---------------   ---------------
# |   ó  |  aron  | |      |        |
 # ---------------   ---------------
 # ---------------   ---------------
# |   -er / -ir   | |   -er / -ir   |
 # ---------------   ---------------
# |   í  |  imos  | |      |        |
 # ---------------   ---------------
# | iste |        | |      |        |
 # ---------------   ---------------
# |  ís  | ieron  | |      |        |
 # ---------------   ---------------
            # Imperfect 
      # (Habits / Background)
 # ---------------   ---------------
# |      -ar      | |      -ar      |
 # ---------------   ---------------
# | aba  | ábamos | |      |        |
 # ---------------   ---------------
# | abas |        | |      |        |
 # ---------------   ---------------
# | aba  |  aban  | |      |        |
 # ---------------   ---------------
 # ---------------   ---------------
# |   -er / -ir   | |   -er / -ir   |
 # ---------------   ---------------
# |  ía  | íamos  | |      |        |
 # ---------------   ---------------
# | ías  |        | |      |        |
 # ---------------   ---------------
# |  ía  | ían    | |      |        |
 # ---------------   ---------------
 
# CONJUGATE PAST LIKE PRESENT

            # Irregulars
# ser - era
# ir - iba
# ver - veía

            # Future
 # ------------------   ------------------
# | -ar / -er / -ir  | | -ar / -er / -ir  |
 # ------------------   ------------------
# |   é   |   emos   | |       |          |
 # ------------------   ------------------
# |  ás   |          | |       |          |
 # ------------------   ------------------
# |   a   |    án    | |       |          |
 # ------------------   ------------------
     
# CONJUGATE FUTURE BY ADDING ENDING TO INFINITIVE

# Escribe como ayer, hoy, y mañana:

# """

    # + "\x1b\x64\x04"   # Feed 4 lines
    # + "\x1b\x64\x04"   # Feed 4 lines
    # + "\x1b\x64\x04"   # Feed 4 lines
    # + "\x1b\x64\x04"   # Feed 4 lines
    # + "\x1d\x56\x00"   # Full cut

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