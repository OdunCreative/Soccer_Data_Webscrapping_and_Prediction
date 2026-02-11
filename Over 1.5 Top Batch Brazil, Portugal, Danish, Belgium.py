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
    "RB Bragantino": "Red Bull Bragantino SP", "Flamengo": "Flamengo RJ", "Mirassol": "Mirassol FC SP",
    "Fortaleza": "Fortaleza EC CE", "Botafogo (RJ)": "Botafogo", "Ceará": "Ceara SC", "Grêmio": "Gremio",
    "Juventude": "EC Juventude RS", 
    "Casa Pia": "Casa Pia Lisbon", "Gil Vicente FC": "Gil Vicente", "AVS Futebol": "Avs Futebol Sad",
    "Famalicão": "FC Famalicao", "Braga": "Sporting Braga", "Alverca": "FC Alverca SAD",
    "Estoril": "Estoril Praia", "Estrela": "Estrela Amadora", "Porto": "FC Porto",
    "Vitória Guimarães": "Vta de Guimar.", 
    "AGF": "AGF Aarhus", "Viborg": "Viborg FF", "SønderjyskE": "SonderjyskE", "Silkeborg": "Silkeborg IF", 
    "Nordsjælland": "Nordsjaelland", "Brøndby": "Brondby", "Odense": "Odense Boldklub", 

    "Dender": "FCV Dender EH", "Mechelen": "KV Mechelen", "Union SG": "Union Saint-Gilloise",
    "La Louvière": "Raal La Louviere", "Zulte Waregem": "SV Zulte Waregem", "Standard Liège": "Standard Liege",
    "Antwerp": "Royal Antwerp", "OH Leuven": "Oud-Heverlee Leuven", 
}

# Row bands for each league in your fixtures.csv + their FoxSports URLs
LEAGUES = {
    "EPL": {"start": 2, "end": 11, "url": "https://www.foxsports.com/soccer/brazil-serie-a/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=21"}, #BRAZIL
    "LA LIGA": {"start": 14, "end": 23, "url": "https://www.foxsports.com/soccer/primeria-liga/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=16"}, #PORTUGUESE
    "SERIA A": {"start": 26, "end": 35, "url": "https://www.foxsports.com/soccer/danish-superliga/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=99"}, #DANISH
    "BUNDESLIGA": {"start": 38, "end": 46, "url": "https://www.foxsports.com/soccer/juliper-league/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=18"}, #BELGIAN
    "LIGUE 1": {"start": 49, "end": 57, "url": "https://www.foxsports.com/soccer/ligue1/team-stats?category=standard&sort=t_a&season=2024&sortOrder=desc&groupId=43"}
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
        # Vasco da Gama 1.4 1.5 vs 0.9 1.0 Ceara SC  -> Over 1.5 (2-2)
        if (1.2 <= avg1 <= 1.6 and 1.3 <= con1 <= 1.7 and
            0.7 <= avg2 <= 1.1 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (2-2)"

        # Palmeiras 1.4 0.8 vs 1.2 1.4 Internacional  -> Over 1.5 (4-1)
        elif (1.2 <= avg1 <= 1.6 and 0.6 <= con1 <= 1.0 and
            1.0 <= avg2 <= 1.4 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (4-1)"

        # Internacional 1.2 1.5 vs 0.9 1.2 Gremio  -> Over 1.5 (2-3)
        elif (1.0 <= avg1 <= 1.4 and 1.3 <= con1 <= 1.7 and
            0.7 <= avg2 <= 1.1 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (2-3)"

        # Palmeiras 1.5 0.8 vs 1.0 1.5 Fortaleza EC CE  -> Over 1.5 (4-1)
        elif (1.3 <= avg1 <= 1.7 and 0.6 <= con1 <= 1.0 and
            0.8 <= avg2 <= 1.2 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (4-1)"

        # Gremio 1.0 1.3 vs 0.8 1.5 Vta de Guimar.  -> Over 1.5 (3-1)
        elif (0.8 <= avg1 <= 1.2 and 1.1 <= con1 <= 1.5 and
            0.6 <= avg2 <= 1.0 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (3-1)"

        # Red Bull Bragantino SP 1.2 1.5 vs 1.0 1.4 Santos  -> Over 1.5 (2-2)
        elif (1.0 <= avg1 <= 1.4 and 1.3 <= con1 <= 1.7 and
            0.8 <= avg2 <= 1.2 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (2-2)"
        else:
            return "Ignore Bet"

    elif league == "LA LIGA": #PORTUGUESE
    # Arouca 1.5 2.3 vs 2.5 0.2 FC Porto  -> Over 1.5 (0-4)
        if (1.3 <= avg1 <= 1.7 and 2.1 <= con1 <= 2.5 and
            2.3 <= avg2 <= 2.7 and 0.0 <= con2 <= 0.4):
            return "Over 1.5 (0-4)"

        # Estoril Praia 1.2 1.8 vs 0.8 2.0 Avs Futebol Sad  -> Over 1.5 (3-1)
        elif (1.0 <= avg1 <= 1.4 and 1.6 <= con1 <= 2.0 and
            0.6 <= avg2 <= 1.0 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (3-1)"

#Casa Pia Lisbon	0.9	1.6	1.25	vs	1.1	1.6	1.35	Estoril Praia	2.6	LA LIGA: Ignore Bet	(2-2)
        elif (0.7 <= avg1 <= 1.1 and 1.4 <= con1 <= 1.8 and
            0.9 <= avg2 <= 1.3 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (2-2 New1)"

#Avs Futebol Sad	0.6	2.4	1.1	vs	1.1	1.6	1.75	FC Alverca SAD	2.85	LA LIGA: Ignore Bet	(1-3)
        elif (0.4 <= avg1 <= 0.8 and 2.2 <= con1 <= 2.6 and
            0.9 <= avg2 <= 1.3 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (1-3 New1)"
        
        # Moreirense 1.2 0.8 vs 2.0 2.0 Rio Ave  -> Over 1.5 (3-1)
        elif (1.0 <= avg1 <= 1.4 and 0.6 <= con1 <= 1.0 and
            1.8 <= avg2 <= 2.2 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (3-1)"
        else:
            return "Ignore Bet"

    elif league == "SERIA A": #DANISH
    # Brondby 1.2 1.1 vs 1.8 2.4 Odense Boldklub  -> Over 1.5 (5-1)
        if (1.0 <= avg1 <= 1.4 and 0.9 <= con1 <= 1.3 and
            1.6 <= avg2 <= 2.0 and 2.2 <= con2 <= 2.6):
            return "Over 1.5 (5-1)"

        # Odense Boldklub 1.6 2.5 vs 1.6 1.9 FC Fredericia  -> Over 1.5 (3-2)
        elif (1.4 <= avg1 <= 1.8 and 2.3 <= con1 <= 2.7 and
            1.4 <= avg2 <= 1.8 and 1.7 <= con2 <= 2.1):
            return "Over 1.5 (3-2)"

# Silkeborg IF	1.5	2.2	1.45	vs	2.3	1.4	2.25	FC Copenhagen	3.7	Actual: 3-1
        elif (1.3 <= avg1 <= 1.7 and 2.0 <= con1 <= 2.4 and
            2.1 <= avg2 <= 2.5 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-1 New2)"

# Brondby	1.6	1.0	1.25	vs	2.1	0.9	1.55	AGF Aarhus	2.8	Actual: 3-3
        elif (1.4 <= avg1 <= 1.8 and 0.8 <= con1 <= 1.2 and
            1.9 <= avg2 <= 2.3 and 0.7 <= con2 <= 1.1):
            return "Over 1.5 (3-3 New2)"

# Midtjylland	2.4	1.3	1.95	vs	1.0	1.5	1.15	Vejle BK	3.1	Actual: 5-1
        elif (2.2 <= avg1 <= 2.6 and 1.1 <= con1 <= 1.5 and
            0.8 <= avg2 <= 1.2 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (5-1 New2)"


        # Vejle BK 1.0 1.4 vs 1.5 1.8 SonderjyskE  -> Over 1.5 (2-2)
        elif (0.8 <= avg1 <= 1.2 and 1.2 <= con1 <= 1.6 and
            1.3 <= avg2 <= 1.7 and 1.6 <= con2 <= 2.0):
            return "Over 1.5 (2-2)"

        # FC Copenhagen 2.4 1.2 vs 1.4 2.1 Silkeborg IF  -> Over 1.5 (3-3)
        elif (2.2 <= avg1 <= 2.6 and 1.0 <= con1 <= 1.4 and
            1.2 <= avg2 <= 1.6 and 1.9 <= con2 <= 2.3):
            return "Over 1.5 (3-3)"

#AGF Aarhus	2	0.9	2.05	vs	1.5	2.1	1.2	Silkeborg IF	3.25	SERIA A: Ignore Bet	(3-1)
        elif (1.8 <= avg1 <= 2.2 and 0.7 <= con1 <= 1.1 and
            1.3 <= avg2 <= 1.7 and 1.9 <= con2 <= 2.3):
            return "Over 1.5 (3-1 New 1)"

        else:
            return "Ignore Bet"

    elif league == "BUNDESLIGA":

        # Cercle Brugge 1.2 1.1 vs 1.4 1.2 Gent  -> Over 1.5 (2-4)
        if (1.0 <= avg1 <= 1.4 and 0.9 <= con1 <= 1.3 and
            1.2 <= avg2 <= 1.6 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (2-4)"

# Union Saint-Gilloise	1.9	0.5	1.65	vs	1.3	1.4	0.9	Charleroi	2.55	Actual: 3-1
        elif (1.7 <= avg1 <= 2.1 and 0.3 <= con1 <= 0.7 and
            1.1 <= avg2 <= 1.5 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-1 New2)"

# Cercle Brugge	1.3	1.4	1.35	vs	1.4	1.4	1.4	Genk	2.75	Actual: 2-2
        elif (1.1 <= avg1 <= 1.5 and 1.2 <= con1 <= 1.6 and
            1.2 <= avg2 <= 1.6 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (2-2 New2)"

# FCV Dender EH	0.3	1.5	0.7	vs	1.3	1.1	1.4	KV Mechelen	2.1	Actual: 1-3
        elif (0.1 <= avg1 <= 0.5 and 1.3 <= con1 <= 1.7 and
            1.1 <= avg2 <= 1.5 and 0.9 <= con2 <= 1.3):
            return "Over 1.5 (1-3 New2)"

# Sint-Truiden	1.5	1.2	1.2	vs	1.5	0.9	1.35	Anderlecht	2.55	Actual: 2-2
        elif (1.3 <= avg1 <= 1.7 and 1.0 <= con1 <= 1.4 and
            1.3 <= avg2 <= 1.7 and 0.7 <= con2 <= 1.1):
            return "Over 1.5 (2-2 New2)"

# SV Zulte Waregem	1.3	1.3	1.3	vs	1.7	1.3	1.5	Gent	2.8	Actual: 4-1
        elif (1.1 <= avg1 <= 1.5 and 1.1 <= con1 <= 1.5 and
            1.5 <= avg2 <= 1.9 and 1.1 <= con2 <= 1.5):
            return "Over 1.5 (4-1 New2)"


        # Cercle Brugge 1.3 1.0 vs 1.4 1.2 Charleroi  -> Over 1.5 (2-3)
        elif (1.1 <= avg1 <= 1.5 and 0.8 <= con1 <= 1.2 and
            1.2 <= avg2 <= 1.6 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (2-3)"

#KV Mechelen	1.3	0.9	1.25	vs	1.3	1.2	1.1	Sint-Truiden	2.35	BUNDESLIGA: Over 1.5 (2-4)	(1-3)
        elif (1.1 <= avg1 <= 1.5 and 0.7 <= con1 <= 1.1 and
            1.1 <= avg2 <= 1.5 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (1-3 New 1)"

        else:
            return "Ignore Bet"

    elif league == "LIGUE 1":
        if avg1 <= 1.0 and avg2 <= 1.0:
            return "Over 2.5 Con 1"
        elif con1 <= 1.1 and con2 <= 1.1 and total_exp <= 2.5:
            return "Over 2.5 Con 2"
        elif total_exp <= 2.45:
            return "Over 2.5 Con 3"
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
