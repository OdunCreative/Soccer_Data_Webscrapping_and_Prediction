import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# ---------------------------
# CONFIG
# ---------------------------
CHROME_DRIVER_PATH = r"C:\Users\Odun-IT\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

FIXTURES_CSV = r"C:\Users\Odun-IT\Desktop\PREDICTION\fixtures.csv"
OUTPUT_CSV   = r"C:\Users\Odun-IT\Desktop\PREDICTION\scrapping_results.csv"

# Map FoxSports team names to your fixtures team names
TEAM_NAME_MAP = {
    "Newcastle United": "Newcastle", "Manchester City": "Man. City", "Nottingham Forest": "Nottingham", "Tottenham": "Tottenham Hotspur", "West Ham United": "West Ham", "Real Betis": "Betis",
    "Athletic Club": "Athletic", "Lecce": "US Lecce", "Milan": "AC Milan", "Cremonese": "US Cremonese",
    "Como": "Como 1907", "Pisa": "SC Pisa", "Hellas Verona": "Verona", "Inter": "Inter Milan",
    "Eintracht Frankfurt": "Eintracht Fran.", "Freiburg": "SC Freiburg", "Augsburg": "FC Augsburg", "Wolfsburg": "VfL Wolfsburg",
    "Union Berlin": "FC Union Berlin", "Stuttgart": "VfB Stuttgart", "St Pauli": "FC St. Pauli",
    "Mainz 05": "FSV Mainz 05", "Köln": "FC Köln", "Gladbach": "B. M'gladbach",
    "Hamburger SV": "Hamburg SV", "Le Havre": "Le Havre AC", "Brest": "Stade Brestois 29",
    "Auxerre": "AJ Auxerre", "Paris S-G": "Paris SG"
}

# Row bands for each league in your fixtures.csv + their FoxSports URLs
LEAGUES = {
    "EPL": {
        "start": 2, "end": 11,
        "url": "https://www.foxsports.com/soccer/premier-league/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=1"
    },
    "LA LIGA": {
        "start": 14, "end": 23,
        "url": "https://www.foxsports.com/soccer/la-liga/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=2"
    },
    "SERIA A": {
        "start": 26, "end": 35,
        "url": "https://www.foxsports.com/soccer/serie-a/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=3"
    },
    "BUNDESLIGA": {
        "start": 38, "end": 46,
        "url": "https://www.foxsports.com/soccer/bundesliga/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=4"
    },
    "LIGUE 1": {
        "start": 49, "end": 57,
        "url": "https://www.foxsports.com/soccer/ligue1/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=43"
    }
}

# ---------------------------
# DRIVER
# ---------------------------
def init_driver():
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    return driver

# ---------------------------
# HELPERS
# ---------------------------
def correct_team_name(name: str) -> str:
    return TEAM_NAME_MAP.get(name.strip(), name.strip())

def scrape_all_team_stats(driver, url: str):
    """
    Scrapes team -> (avg_scored, avg_conceded) from FoxSports team stats page.
    """
    driver.get(url)
    time.sleep(3)  # simple wait; you can switch to WebDriverWait if needed

    team_stats = {}  # { team_name: (avg_scored, avg_conceded) }

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.row-data tr")

    for row in rows:
        try:
            team_name_elem = row.find_element(By.CSS_SELECTOR, 'a.table-entity-name.ff-h')
            team_name = correct_team_name(team_name_elem.text.strip())

            gp = int(row.find_element(By.CSS_SELECTOR, 'td[data-index="2"] span.table-result').text.strip())
            gf = int(row.find_element(By.CSS_SELECTOR, 'td[data-index="3"] span.table-result').text.strip())
            gc = int(row.find_element(By.CSS_SELECTOR, 'td[data-index="8"] span.table-result').text.strip())

            avg_scored = round(gf / gp, 1) if gp else 0.0
            avg_conceded = round(gc / gp, 1) if gp else 0.0

            team_stats[team_name] = (avg_scored, avg_conceded)
        except Exception:
            # Skip any bad/unexpected rows
            continue

    return team_stats

def calculate_expected_goals(avg_scored: float, opp_avg_conceded: float) -> float:
    """
    Simple expected goals proxy: mean of team's avg scored and opponent's avg conceded.
    """
    return round((avg_scored + opp_avg_conceded) / 2, 2)

# ---------------------------
# PER-LEAGUE RULES (if/else)
# ---------------------------
def check_conditions_by_league(league: str, avg1: float, con1: float, exp1: float,
                               avg2: float, con2: float, exp2: float, total_exp: float) -> str:
    """
    Return "Over 2.5 Con X" if one of the league-specific conditions is met,
    else "Ignore Bet".
    Adjust inside each league block as you want.
    """

    if league == "EPL":
# 1. Home 1.0–1.4, Con 1.8–2.2; Away 1.0–1.4, Con 1.4–1.8
        if (1.0 <= avg1 <= 1.4 and 1.8 <= con1 <= 2.2 and
            1.0 <= avg2 <= 1.4 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (3-1)"

#Bournemouth	1.3	1.2	1.3	vs	1.2	1.3	1.2	Fulham	2.5
        elif (1.1 <= avg1 <= 1.5 and 1.0 <= con1 <= 1.4 and
              1.0 <= avg2 <= 1.4 and 1.1 <= con2 <= 1.5):
            return "Over 1.5 (3-1) New1"

        # 2. Home 0.6–1.0, Con 1.2–1.6; Away 1.0–1.4, Con 0.8–1.2
        elif (0.6 <= avg1 <= 1.0 and 1.2 <= con1 <= 1.6 and
              1.0 <= avg2 <= 1.4 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (2-2)"

        # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1.6 <= avg1 <= 2.0 and 0.8 <= con1 <= 1.2 and
              0.8 <= avg2 <= 1.2 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (5-1)"

        # 4. Home 0.0–0.4, Con 0.8–1.2; Away 1.0–1.4, Con 0.8–1.2
        elif (0.0 <= avg1 <= 0.4 and 0.8 <= con1 <= 1.2 and
              1.0 <= avg2 <= 1.4 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (3-1)"

        # 5. Home 0.6–1.0, Con 0.8–1.2; Away 1.0–1.4, Con 1.6–2.0
        elif (0.6 <= avg1 <= 1.0 and 0.8 <= con1 <= 1.2 and
              1.0 <= avg2 <= 1.4 and 1.6 <= con2 <= 2.0):
            return "Over 1.5 (3-1)"

        # 6. Home 0.8–1.2, Con 1.3–1.7; Away 1.8–2.2, Con 0.0–0.4
        elif (0.8 <= avg1 <= 1.2 and 1.3 <= con1 <= 1.7 and
              1.8 <= avg2 <= 2.2 and 0.0 <= con2 <= 0.4):
            return "Over 1.5 (2-2)"
        
        # Manchester Utd 1.4 1.5 vs 1.5 1.4 Brighton  Actual: 4-2
        elif (1.2 <= avg1 <= 1.6 and 1.3 <= con1 <= 1.7 and
            1.3 <= avg2 <= 1.7 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (4-2) New2"

        # Brentford 1.4 1.5 vs 1.8 1.4 Liverpool  Actual: 3-2
        elif (1.2 <= avg1 <= 1.6 and 1.3 <= con1 <= 1.7 and
            1.6 <= avg2 <= 2.0 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-2) New2"

        # Wolves 0.6 2.0 vs 1.1 1.9 Burnley  Actual: 2-3
        elif (0.4 <= avg1 <= 0.8 and 1.8 <= con1 <= 2.2 and
            0.9 <= avg2 <= 1.3 and 1.7 <= con2 <= 2.1):
            return "Over 1.5 (2-3) New2"

# Crystal Palace	1.3	0.7	1.2	vs	1.6	1.1	1.15	Bournemouth	2.35	Actual: 3-3
        elif (1.1 <= avg1 <= 1.5 and 0.5 <= con1 <= 0.9 and
            1.4 <= avg2 <= 1.8 and 0.9 <= con2 <= 1.3):
            return "Over 1.5 (3-3 New2)"

        # 7. Home 0.3–0.7, Con 2.0–2.4; Away 0.0–0.4, Con 1.3–1.7
        elif (0.3 <= avg1 <= 0.7 and 2.0 <= con1 <= 2.4 and
              0.0 <= avg2 <= 0.4 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (1-3)"
        else:
            return "Ignore Bet"
        
#------------------------------------------------------------------------------------------------------

    elif league == "LA LIGA":
        if (1.3 <= avg1 <= 1.7 and 1 <= con1 <= 1.4 and
            2.1 <= avg2 <= 2.5 and 0.3  <= con2 <= 0.7):
            return "Over 1.5 (5-2)"

#Sevilla	1.6	1.4	1.15	vs	3	0.7	2.2	Barcelona	3.35	LA LIGA: Ignore Bet	4-1
        elif (1.4 <= avg1 <= 1.8 and 1.2 <= con1 <= 1.6 and
              2.8 <= avg2 <= 3.2 and 0.5 <= con2 <= 0.9):
            return "Over 1.5 (4-1 New1)"

        # 2. Home 0.6–1.0, Con 1.2–1.6; Away 1.0–1.4, Con 0.8–1.2
        elif (0.3 <= avg1 <= 0.7 and 2.6 <= con1 <= 3 and
              1.0 <= avg2 <= 1.4 and 2 <= con2 <= 2.4):
            return "Over 1.5 (0-4)"
        
        # Sevilla	1.9	1.4	1.75	vs	0.9	1.6	1.15	Mallorca	2.9	Actual: 1-3
        elif (1.7 <= avg1 <= 2.1 and 1.2 <= con1 <= 1.6 and
            0.7 <= avg2 <= 1.1 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (1-3 New2)"

        # Girona 0.7 2.1 vs 0.4 1.8 Oviedo  Actual: 3-3
        elif (0.5 <= avg1 <= 0.9 and 1.9 <= con1 <= 2.3 and
            0.2 <= avg2 <= 0.6 and 1.6 <= con2 <= 2.0):
            return "Over 1.5 (3-3) New2"

        # Osasuna 0.8 1.0 vs 0.9 1.2 Celta Vigo  Actual: 2-3
        elif (0.6 <= avg1 <= 1.0 and 0.8 <= con1 <= 1.2 and
            0.7 <= avg2 <= 1.1 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (2-3) New2"

# Villarreal	1.8	1.0	1.4	vs	1.6	1.0	1.3	Betis	2.7	Actual: 2-2
        elif (1.6 <= avg1 <= 2.0 and 0.8 <= con1 <= 1.2 and
            1.4 <= avg2 <= 1.8 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (2-2 New2)"


        # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1 <= avg1 <= 1.4 and 1 <= con1 <= 1.4 and
              0.8 <= avg2 <= 1.2 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (3-1)"
        else:
            return "Ignore Bet"
#------------------------------------------------------------------------------------------------------
    elif league == "SERIA A":
        if (0.8 <= avg1 <= 1.2 and 1.6 <= con1 <= 2 and
            0.8 <= avg2 <= 1.2 and 1  <= con2 <= 1.4):
            return "Over 1.5 (3-1)"

        # 2. Home 0.6–1.0, Con 1.2–1.6; Away 1.0–1.4, Con 0.8–1.2
        elif (0.3 <= avg1 <= 0.7 and 1.8 <= con1 <= 2.2 and
              0.6 <= avg2 <= 1 and 0.6 <= con2 <= 1):
            return "Over 1.5 (2-2)"

#Lazio	1.4	0.8	1.7	vs	0.4	2	0.6	Torino	2.3	SERIA A: Ignore Bet	3-3
        elif (1.2 <= avg1 <= 1.6 and 0.6 <= con1 <= 1 and
              0.2 <= avg2 <= 0.6 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (3-3 New 1)"

        # AC Milan 1.6 0.6 vs 0.4 1.4 SC Pisa  Actual: 2-2
        elif (1.4 <= avg1 <= 1.8 and 0.4 <= con1 <= 0.8 and
            0.2 <= avg2 <= 0.6 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (2-2) New2"

        # Udinese 1.0 1.4 vs 0.7 1.4 US Lecce  Actual: 3-2
        elif (0.8 <= avg1 <= 1.2 and 1.2 <= con1 <= 1.6 and
            0.5 <= avg2 <= 0.9 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-2) New2"

        # Napoli 1.7 1.0 vs 2.6 1.1 Inter Milan  Actual: 3-1
        elif (1.5 <= avg1 <= 1.9 and 0.8 <= con1 <= 1.2 and
            2.4 <= avg2 <= 2.8 and 0.9 <= con2 <= 1.3):
            return "Over 1.5 (3-1) New2"

        # Verona 0.3 1.3 vs 0.9 1.1 Cagliari  Actual: 2-2
        elif (0.1 <= avg1 <= 0.5 and 1.1 <= con1 <= 1.5 and
            0.7 <= avg2 <= 1.1 and 0.9 <= con2 <= 1.3):
            return "Over 1.5 (2-2) New2"

#Inter Milan	2.6	1.4	1.7	vs	1.2	0.8	1.3	US Cremonese	3	SERIA A: Ignore Bet	4-1
        elif (2.4 <= avg1 <= 2.8 and 1.2 <= con1 <= 1.6 and
              1 <= avg2 <= 1.4 and 0.6 <= con2 <= 1):
            return "Over 1.5 (4-1 New 1)"

        # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1.8 <= avg1 <= 2.2 and 0.1 <= con1 <= 0.5 and
              0.1 <= avg2 <= 0.5 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (3-2)"
        else:
            return "Ignore Bet"
#------------------------------------------------------------------------------------------------------
    elif league == "BUNDESLIGA":
        if (0 <= avg1 <= 0.4 and 1.3 <= con1 <= 1.7 and
            2.6 <= avg2 <= 3 and 2  <= con2 <= 2.4):
            return "Over 1.5 (4-6)"

        # 2. Home 0.6–1.0, Con 1.2–1.6; Away 1.0–1.4, Con 0.8–1.2
        elif (4.3 <= avg1 <= 4.7 and 0.6 <= con1 <= 1 and
              1.8 <= avg2 <= 2.2 and 2.3 <= con2 <= 2.7):
            return "Over 1.5 (4-0)"
        
        # Hoffenheim 1.7 1.7 vs 0.9 1.9 Heidenheim  Actual: 3-1
        elif (1.5 <= avg1 <= 1.9 and 1.5 <= con1 <= 1.9 and
            0.7 <= avg2 <= 1.1 and 1.7 <= con2 <= 2.1):
            return "Over 1.5 (3-1) New2"

        # FC Augsburg 1.7 2.0 vs 1.4 1.3 RB Leipzig  Actual: 0-6
        elif (1.5 <= avg1 <= 1.9 and 1.8 <= con1 <= 2.2 and
            1.2 <= avg2 <= 1.6 and 1.1 <= con2 <= 1.5):
            return "Over 1.5 (0-6) New2"

#FC Augsburg	1.6	2.4	1.5	vs	1.4	1.4	1.9	VfL Wolfsburg	3.4	BUNDESLIGA: Ignore Bet	(3-1)
        elif (1.4 <= avg1 <= 1.8 and 2.2 <= con1 <= 2.6 and
              1.2 <= avg2 <= 1.6 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-1 New 1)"

#Hamburg SV	0.4	1.6	0.8	vs	1	1.2	1.3	FSV Mainz 05	2.1	BUNDESLIGA: Ignore Bet	(4-0)
        elif (0.2 <= avg1 <= 0.6 and 1.4 <= con1 <= 1.8 and
              0.8 <= avg2 <= 1.2 and 1 <= con2 <= 1.4):
            return "Over 1.5 (4-0 New 1)"

        # FC Union Berlin	1.3	2.2	1.65	vs	0.8	2.0	1.5	B. M'gladbach	3.15	Actual: 3-1
        elif (1.1 <= avg1 <= 1.5 and 2.0 <= con1 <= 2.4 and
            0.6 <= avg2 <= 1.0 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (3-1 New2)"

# Heidenheim	0.7	1.8	1.5	vs	1.5	2.3	1.65	Werder Bremen	3.15	Actual: 2-2
        elif (0.5 <= avg1 <= 0.9 and 1.6 <= con1 <= 2.0 and
            1.3 <= avg2 <= 1.7 and 2.1 <= con2 <= 2.5):
            return "Over 1.5 (2-2 New2)"

# FSV Mainz 05	0.8	1.7	1.05	vs	2.0	1.3	1.85	Leverkusen	2.9	Actual: 3-4
        elif (0.6 <= avg1 <= 1.0 and 1.5 <= con1 <= 1.9 and
            1.8 <= avg2 <= 2.2 and 1.1 <= con2 <= 1.5):
            return "Over 1.5 (3-4 New2)"

# SC Freiburg	1.5	1.5	2.1	vs	2.8	2.7	2.15	Eintracht Fran.	4.25	Actual: 2-2
        elif (1.3 <= avg1 <= 1.7 and 1.3 <= con1 <= 1.7 and
            2.6 <= avg2 <= 3.0 and 2.5 <= con2 <= 2.9):
            return "Over 1.5 (2-2 New2)"


        # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (2.5 <= avg1 <= 2.9 and 1.5 <= con1 <= 1.9 and
              1.1 <= avg2 <= 1.5 and 2.5 <= con2 <= 2.9):
            return "Over 1.5 (3-4)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (0.8 <= avg1 <= 1.2 and 1.8 <= con1 <= 2.2 and
              2.5 <= avg2 <= 2.9 and 1.1 <= con2 <= 1.5):
            return "Over 1.5 (3-1)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (2.1 <= avg1 <= 2.5 and 1.8 <= con1 <= 2.2 and
              4.5 <= avg2 <= 4.9 and 0.5 <= con2 <= 0.9):
            return "Over 1.5 (1-4)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1.8 <= avg1 <= 2.2 and 1.8 <= con1 <= 2.2 and
              0.1 <= avg2 <= 0.5 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (1-4)"
        
        else:
            return "Ignore Bet"
#------------------------------------------------------------------------------------------------------
    elif league == "LIGUE 1":
        if (0 <= avg1 <= 0.4 and 0.6 <= con1 <= 1 and
            1 <= avg2 <= 1.4 and 1.3  <= con2 <= 1.7):
            return "Over 1.5 (2-2)"

        # 2. Home 0.6–1.0, Con 1.2–1.6; Away 1.0–1.4, Con 0.8–1.2
        elif (1 <= avg1 <= 1.4 and 2.3 <= con1 <= 2.7 and
              1 <= avg2 <= 1.4 and 1 <= con2 <= 1.4):
            return "Over 1.5 (4-1)"
        
        # Lille 2.0 1.2 vs 0.6 2.5 Metz  Actual: 6-1
        elif (1.8 <= avg1 <= 2.2 and 1.0 <= con1 <= 1.4 and
            0.4 <= avg2 <= 0.8 and 2.3 <= con2 <= 2.7):
            return "Over 1.5 (6-1) New2"

# Paris SG	1.9	0.7	1.45	vs	2.0	1.0	1.35	Strasbourg	2.8	Actual: 3-3
        elif (1.7 <= avg1 <= 2.1 and 0.5 <= con1 <= 0.9 and
            1.8 <= avg2 <= 2.2 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (3-3 New2)"

# Nice	1.3	1.7	1.0	vs	1.3	0.7	1.5	Lyon	2.5	Actual: 3-2
        elif (1.1 <= avg1 <= 1.5 and 1.5 <= con1 <= 1.9 and
            1.1 <= avg2 <= 1.5 and 0.5 <= con2 <= 0.9):
            return "Over 1.5 (3-2 New2)"

# Rennes	1.3	1.4	1.35	vs	0.7	1.4	1.05	AJ Auxerre	2.4	Actual: 2-2
        elif (1.1 <= avg1 <= 1.5 and 1.2 <= con1 <= 1.6 and
            0.5 <= avg2 <= 0.9 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (2-2 New2)"

# Lorient	1.3	2.3	1.45	vs	1.6	1.6	1.95	Stade Brestois 29	3.4	Actual: 3-3
        elif (1.1 <= avg1 <= 1.5 and 2.1 <= con1 <= 2.5 and
            1.4 <= avg2 <= 1.8 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (3-3 New2)"


#Strasbourg	1.5	1.2	1.25	vs	0.5	1	0.85	Angers	2.1	LIGUE 1: Ignore Bet	(5-0)
        elif (1.3 <= avg1 <= 1.7 and 1 <= con1 <= 1.4 and
              0.3 <= avg2 <= 0.7 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (5-0 New 1)"

#Le Havre AC	1	1.3	1.15	vs	1.2	1.3	1.25	Rennes	2.4	LIGUE 1: Ignore Bet	(2-2)
        elif (0.8 <= avg1 <= 1.2 and 1.1 <= con1 <= 1.5 and
              1 <= avg2 <= 1.4 and 1.1 <= con2 <= 1.5):
            return "Over 1.5 (2-2 New 1)"

        # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1.6 <= avg1 <= 2 and 2 <= con1 <= 2.4 and
              1 <= avg2 <= 1.4 and 0.6 <= con2 <= 1):
            return "Over 1.5 (2-3)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1.8 <= avg1 <= 2.2 and 1 <= con1 <= 1.4 and
              0.6 <= avg2 <= 1 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (5-2)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1 <= avg1 <= 1.4 and 2.4 <= con1 <= 2.8 and
              2.4 <= avg2 <= 2.8 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-1)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (1.2 <= avg1 <= 1.6 and 1.6 <= con1 <= 2 and
              0.4 <= avg2 <= 0.8 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (2-2)"
        
                # 3. Home 1.6–2.0, Con 0.8–1.2; Away 0.8–1.2, Con 1.4–1.8
        elif (0.7 <= avg1 <= 1.6 and 1 <= con1 <= 2 and
              0.4 <= avg2 <= 2.8 and 0.8 <= con2 <= 1.8):
            return "Over 1.5 "
        else:
            return "Ignore Bet"

    # Fallback
    return "Ignore Bet"

# ---------------------------
# MAIN LEAGUE PROCESSOR
# ---------------------------
def process_league(driver, league_name: str, info: dict):
    url = info["url"]
    start_row = info["start"]
    end_row = info["end"]

    # Scrape all teams' averages for the league
    team_stats = scrape_all_team_stats(driver, url)

    # Load fixtures
    results = []
    with open(FIXTURES_CSV, "r", newline="", encoding="latin1") as file:
        reader = list(csv.reader(file))

        # Note: CSV is 1-indexed in your description; Python list is 0-indexed
        for i in range(start_row - 1, end_row):
            # Row structure assumption: [HomeTeam, ?, AwayTeam, ...]
            if len(reader) <= i or len(reader[i]) < 3:
                continue
            if reader[i][0].strip() == "" or reader[i][2].strip() == "":
                continue

            team1 = correct_team_name(reader[i][0])
            team2 = correct_team_name(reader[i][2])

            # Fetch averages (defaults to zeros if missing)
            avg1, con1 = team_stats.get(team1, (0.0, 0.0))
            avg2, con2 = team_stats.get(team2, (0.0, 0.0))

            # Compute expected goals proxy
            exp1 = calculate_expected_goals(avg1, con2)
            exp2 = calculate_expected_goals(avg2, con1)
            total = round(exp1 + exp2, 2)

            prediction = check_conditions_by_league(
                league_name, avg1, con1, exp1, avg2, con2, exp2, total
            )

            results.append([
                team1, avg1, con1, exp1, "vs",
                avg2, con2, exp2, team2,
                total, f"{league_name}: {prediction}"
            ])

    # Append results to output
    with open(OUTPUT_CSV, "a", newline="", encoding="latin1") as outfile:
        writer = csv.writer(outfile)
        for row in results:
            writer.writerow(row)

# ---------------------------
# ENTRYPOINT
# ---------------------------
def main():
    driver = init_driver()

    # Fresh header each run
    with open(OUTPUT_CSV, "w", newline="", encoding="latin1") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Team 1", "Avg scored", "Avg conceded", "Expected goal",
            "vs", "Avg scored 2", "Avg conceded 2", "Expected goals 2",
            "Team 2", "Total expected goals", "Prediction"
        ])

    for league_name, info in LEAGUES.items():
        process_league(driver, league_name, info)

    driver.quit()

if __name__ == "__main__":
    main()
