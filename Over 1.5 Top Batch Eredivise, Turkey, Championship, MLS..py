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
    "Go Ahead Eagles": "G Ahead Eagles", "Heerenveen": "SC Heerenveen", "Volendam": "FC Volendam",
    "Sparta Rotterdam": "Sparta", "Zwolle": "PEC Zwolle", "Twente": "FC Twente", "Telstar": "SC Telstar",
    "Groningen": "FC Groningen", "Utrecht": "FC Utrecht", "PSV": "PSV Eindhoven", 
    
    "Gaziantep FK": "Gazisehir Gaziantep FK", "Gençlerbirliği": "Genclerbirligi",
    "Kasımpaşa": "Kasimpasa S.K.", "Fenerbahçe": "Fenerbahce", "Rizespor": "Caykur Rizespor",
    "Göztepe": "Goztepe SK", "Fatih Karagümrük": "Fatih Karagumruk SK", "Başakşehir": "Basaksehir",
    "Beşiktaş": "Besiktas", "Eyüpspor": "Eyupspor", 
    
    "Birmingham City": "Birmingham", "Charlton Athletic": "Charlton", "Preston North End": "Preston NE", "Sheffield Weds": "Sheffield Wed.", 
    "Queens Park Rangers": "QPR", "Sheffield United":"Sheffield Utd", "Blackburn Rovers":"Blackburn",
    "CF Montréal": "Montreal", "Atlanta Utd": "Atlanta", "NE Revolution": "New England",
    "Columbus Crew": "Columbus", "Philadelphia Union": "Philadelphia", "Toronto FC": "Toronto",
    "Minnesota Utd": "Minnesota", "Colorado Rapids": "Colorado", "Charlotte": "Charlotte FC", "Austin": "Austin FC", 
    "Houston Dynamo": "Houston", "Chicago Fire": "Chicago", "LAFC": "Los Angeles FC", "St. Louis": "Saint Louis City SC", 
    "Portland Timbers": "Portland", "SJ Earthquakes": "San Jose", "Vancouver W'caps": "Vancouver", "Seattle Sounders": "Seattle", "Orlando City": "Orlando", "Inter Miami": "Inter Miami CF",
}

# Row bands for each league in your fixtures.csv + their FoxSports URLs
LEAGUES = {
    "EPL": {"start": 2, "end": 11, "url": "https://www.foxsports.com/soccer/eredivisie/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=15"}, #EREDIVISE
    "LA LIGA": {"start": 14, "end": 23, "url": "https://www.foxsports.com/soccer/turkish-super-lig/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=19"}, #TURKEY
    "SERIA A": {"start": 26, "end": 35, "url": "https://www.foxsports.com/soccer/english-championship/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=23"}, #CHAMPIONSHIP
    "BUNDESLIGA": {"start": 38, "end": 46, "url": "https://www.foxsports.com/soccer/mls/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=5"}, #MLS 1
    "LIGUE 1": {"start": 49, "end": 57, "url": "https://www.foxsports.com/soccer/mls/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=5"} #MLS 2
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
    time.sleep(5)  # simple wait; you can switch to WebDriverWait if needed

    team_stats = {}  # { team_name: (avg_scored, avg_conceded) }

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.row-data tr")

    for row in rows:
        try:
            team_name_elem = row.find_element(By.CSS_SELECTOR, 'a.table-entity-name.ff-h') #ff-ffc
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
# Ajax 1.8 0.8 vs 1.0 0.7 PEC Zwolle -> Over 1.5 (3-1)
        if (1.6 <= avg1 <= 2.0 and 0.6 <= con1 <= 1.0 and
            0.8 <= avg2 <= 1.2 and 0.5 <= con2 <= 0.9):
            return "Over 1.5 (3-1)"

        # NEC Nijmegen 3.5 1.0 vs 3.0 1.2 PSV Eindhoven -> Over 1.5 (3-5)
        elif (3.3 <= avg1 <= 3.7 and 0.8 <= con1 <= 1.2 and
            2.8 <= avg2 <= 3.2 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (3-5)"

# NEC Nijmegen	2.8	1.8	2.1	vs	1.8	1.4	1.8	FC Twente	3.9	Actual: 3-3
        elif (2.6 <= avg1 <= 3.0 and 1.6 <= con1 <= 2.0 and
            1.6 <= avg2 <= 2.0 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (3-3 New2)"

# FC Utrecht	1.9	1.2	1.75	vs	1.1	1.6	1.15	FC Volendam	2.9	Actual: 3-1
        elif (1.7 <= avg1 <= 2.1 and 1.0 <= con1 <= 1.4 and
            0.9 <= avg2 <= 1.3 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (3-1 New2)"

# NAC Breda	1.0	1.8	1.45	vs	0.9	1.9	1.35	PEC Zwolle	2.8	Actual: 2-2
        elif (0.8 <= avg1 <= 1.2 and 1.6 <= con1 <= 2.0 and
            0.7 <= avg2 <= 1.1 and 1.7 <= con2 <= 2.1):
            return "Over 1.5 (2-2 New2)"

# SC Telstar	1.2	1.9	1.4	vs	1.5	1.6	1.7	SC Heerenveen	3.1	Actual: 2-3
        elif (1.0 <= avg1 <= 1.4 and 1.7 <= con1 <= 2.1 and
            1.3 <= avg2 <= 1.7 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (2-3 New2)"

# Heracles Almelo	0.9	2.5	0.85	vs	2.2	0.8	2.35	Feyenoord	3.2	Actual: 0-7
        elif (0.7 <= avg1 <= 1.1 and 2.3 <= con1 <= 2.7 and
            2.0 <= avg2 <= 2.4 and 0.6 <= con2 <= 1.0):
            return "Over 1.5 (0-7 New2)"


#Sparta	1.1	2.7	1.05	vs	2	1	2.35	Ajax	3.4	EPL: Ignore Bet	(3-3)
        elif (0.9 <= avg1 <= 1.3 and 2.5 <= con1 <= 2.9 and
            1.8 <= avg2 <= 2.2 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (3-3 New 1)"

#Feyenoord	2.1	0.6	1.55	vs	1.9	1	1.25	FC Utrecht	2.8	EPL: Ignore Bet	(3-2)
        elif (1.9 <= avg1 <= 2.3 and 0.4 <= con1 <= 0.8 and
            1.7 <= avg2 <= 2.1 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (3-2 New 1)"

        # FC Twente 0.5 1.2 vs 0.5 1.8 NAC Breda -> Over 1.5 (2-2)
        elif (0.3 <= avg1 <= 0.7 and 1.0 <= con1 <= 1.4 and
            0.3 <= avg2 <= 0.7 and 1.6 <= con2 <= 2.0):
            return "Over 1.5 (2-2)"

        # SC Telstar 1.0 1.5 vs 2.0 2.0 Fortuna Sittard -> Over 1.5 (1-3)
        elif (0.8 <= avg1 <= 1.2 and 1.3 <= con1 <= 1.7 and
            1.8 <= avg2 <= 2.2 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (1-3)"

        # Sparta 1.4 2.2 vs 0.8 1.4 FC Twente -> Over 1.5 (1-5)
        elif (1.2 <= avg1 <= 1.6 and 2.0 <= con1 <= 2.4 and
            0.6 <= avg2 <= 1.0 and 1.2 <= con2 <= 1.6):
            return "Over 1.5 (1-5)"

        # PSV Eindhoven 3.4 1.6 vs 2.0 0.8 Ajax -> Over 1.5 (2-2)
        elif (3.2 <= avg1 <= 3.6 and 1.4 <= con1 <= 1.8 and
            1.8 <= avg2 <= 2.2 and 0.6 <= con2 <= 1.0):
            return "Over 1.5 (2-2)"

        # FC Twente 1.5 1.3 vs 1.7 1.5 Fortuna Sittard -> Over 1.5 (3-2)
        elif (1.3 <= avg1 <= 1.7 and 1.1 <= con1 <= 1.5 and
            1.5 <= avg2 <= 1.9 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (3-2)"

        # FC Utrecht 1.8 0.8 vs 1.3 1.7 SC Heerenveen -> Over 1.5 (2-2)
        elif (1.6 <= avg1 <= 2.0 and 0.6 <= con1 <= 1.0 and
            1.1 <= avg2 <= 1.5 and 1.5 <= con2 <= 1.9):
            return "Over 1.5 (2-2)"

        else:
            return "Ignore Bet"

    elif league == "LA LIGA":
 # Samsunspor 1.0 0.8 vs 0.4 1.8 Fatih Karagumruk SK -> Over 1.5 (3-2)
        if (0.8 <= avg1 <= 1.2 and 0.6 <= con1 <= 1.0 and
            0.2 <= avg2 <= 0.6 and 1.6 <= con2 <= 2.0):
            return "Over 1.5 (3-2)"


# Konyaspor	1.9	1.3	1.7	vs	0.6	1.5	0.95	Kocaelispor	2.65	Actual: 2-3
        elif (1.7 <= avg1 <= 2.1 and 1.1 <= con1 <= 1.5 and
            0.4 <= avg2 <= 0.8 and 1.3 <= con2 <= 1.7):
            return "Over 1.5 (2-3 New2)"

# Kayserispor	0.6	2.1	0.8	vs	1.2	1.0	1.65	Samsunspor	2.45	Actual: 1-3
        elif (0.4 <= avg1 <= 0.8 and 1.9 <= con1 <= 2.3 and
            1.0 <= avg2 <= 1.4 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (1-3 New2)"

# Gazisehir Gaziantep FK	1.5	1.5	1.55	vs	1.1	1.6	1.3	Antalyaspor	2.85	Actual: 3-2
        elif (1.3 <= avg1 <= 1.7 and 1.3 <= con1 <= 1.7 and
            0.9 <= avg2 <= 1.3 and 1.4 <= con2 <= 1.8):
            return "Over 1.5 (3-2 New2)"




        # Galatasaray 3.0 0.2 vs 2.2 1.0 Konyaspor -> Over 1.5 (3-1)
        elif (2.8 <= avg1 <= 3.2 and 0.0 <= con1 <= 0.4 and
            2.0 <= avg2 <= 2.4 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (3-1)"

#Trabzonspor	1.3	0.9	1.6	vs	0.7	1.9	0.8	Kayserispor	2.4	LA LIGA: Ignore Bet	(4-0)
        elif (1.1 <= avg1 <= 1.5 and 0.7 <= con1 <= 1.1 and
            0.5 <= avg2 <= 0.9 and 1.7 <= con2 <= 2.1):
            return "Over 1.5 (4-0 New1)"

        # Gazisehir Gaziantep FK 1.3 1.7 vs 1.3 1.0 Samsunspor -> Over 1.5 (2-2)
        elif (1.1 <= avg1 <= 1.5 and 1.5 <= con1 <= 1.9 and
            1.1 <= avg2 <= 1.5 and 0.8 <= con2 <= 1.2):
            return "Over 1.5 (2-2)"

        # Fatih Karagumruk SK 0.7 2.0 vs 0.8 0.5 Trabzonspor -> Over 1.5 (3-4)
        elif (0.5 <= avg1 <= 0.9 and 1.8 <= con1 <= 2.2 and
            0.6 <= avg2 <= 1.0 and 0.3 <= con2 <= 0.7):
            return "Over 1.5 (3-4)"
        else:
            return "Ignore Bet"

    elif league == "SERIA A":
    # Wrexham 1.8 1.8 vs 1.5 2.8 QPR -> Over 1.5 (1-3)
        if (1.6 <= avg1 <= 2.0 and 1.6 <= con1 <= 2.0 and
            1.3 <= avg2 <= 1.7 and 2.6 <= con2 <= 3.0):
            return "Over 1.5 (1-3)"

        # Norwich City 1.4 1.2 vs 1.6 2.0 Wrexham -> Over 1.5 (2-3)
        elif (1.2 <= avg1 <= 1.6 and 1.0 <= con1 <= 1.4 and
            1.4 <= avg2 <= 1.8 and 1.8 <= con2 <= 2.2):
            return "Over 1.5 (2-3)"

        # Hull City 1.4 2.2 vs 1.2 1.2 Southampton -> Over 1.5 (3-1)
        elif (1.2 <= avg1 <= 1.6 and 2.0 <= con1 <= 2.4 and
            1.0 <= avg2 <= 1.4 and 1.0 <= con2 <= 1.4):
            return "Over 1.5 (3-1)"

#Sheffield Wed.	1	1.9	0.95	vs	2.8	0.9	2.35	Coventry City	3.3	SERIA A: Ignore Bet	(0-5)
        elif (0.8 <= avg1 <= 1.2 and 1.7 <= con1 <= 2.1 and
            2.6 <= avg2 <= 3 and 0.7 <= con2 <= 1.1):
            return "Over 1.5 (0-5 New1)"
        
#Swansea City	1.1	0.9	1	vs	1.2	0.9	1.05	Leicester City	2.05	SERIA A: Ignore Bet	(1-3)
        elif (0.9 <= avg1 <= 1.3 and 0.7 <= con1 <= 1.1 and
            1 <= avg2 <= 1.4 and 0.7 <= con2 <= 1.1):
            return "Over 1.5 (1-3 New1)"


        # Swansea City 1.0 0.5 vs 1.2 2.2 Hull City -> Over 1.5 (2-2)
        elif (0.8 <= avg1 <= 1.2 and 0.3 <= con1 <= 0.7 and
            1.0 <= avg2 <= 1.4 and 2.0 <= con2 <= 2.4):
            return "Over 1.5 (2-2)"

        # Preston NE 1.0 0.8 vs 1.8 0.2 Middlesbrough -> Over 1.5 (2-2)
        elif (0.8 <= avg1 <= 1.2 and 0.6 <= con1 <= 1.0 and
            1.6 <= avg2 <= 2.0 and 0.0 <= con2 <= 0.4):
            return "Over 1.5 (2-2)"

        # Oxford United 1.0 1.8 vs 1.5 0.8 Leicester City -> Over 1.5 (2-2)
        elif (0.8 <= avg1 <= 1.2 and 1.6 <= con1 <= 2.0 and
            1.3 <= avg2 <= 1.7 and 0.6 <= con2 <= 1.0):
            return "Over 1.5 (2-2)"

        # Ipswich Town 1.0 1.2 vs 0.2 1.8 Sheffield Utd -> Over 1.5 (5-0)
        elif (0.8 <= avg1 <= 1.2 and 1.0 <= con1 <= 1.4 and
            0.0 <= avg2 <= 0.4 and 1.6 <= con2 <= 2.0):
            return "Over 1.5 (5-0)"
        else:
            return "Ignore Bet"

    elif league == "BUNDESLIGA":
        if (1.6 <= avg1 <= 2.0 and 1.6 <= con1 <= 2.0 and
                1.5 <= avg2 <= 1.9 and 1.1 <= con2 <= 1.5):
                return "Over 1.5 (2-4)"

            # Seattle 1.8 1.4 vs 1.2 2.0 LA Galaxy -> Over 1.5 (2-2)
        elif (1.6 <= avg1 <= 2.0 and 1.2 <= con1 <= 1.6 and
                1.0 <= avg2 <= 1.4 and 1.8 <= con2 <= 2.2):
                return "Over 1.5 (2-2)"

            # Vancouver 1.7 1.1 vs 1.7 0.9 Philadelphia -> Over 1.5 (7-0)
        elif (1.5 <= avg1 <= 1.9 and 0.9 <= con1 <= 1.3 and
                1.5 <= avg2 <= 1.9 and 0.7 <= con2 <= 1.1):
                return "Over 1.5 (7-0)"

            # Chicago 1.9 1.8 vs 1.4 1.2 NYCFC -> Over 1.5 (1-3)
        elif (1.7 <= avg1 <= 2.1 and 1.6 <= con1 <= 2.0 and
                1.2 <= avg2 <= 1.6 and 1.0 <= con2 <= 1.4):
                return "Over 1.5 (1-3)"

            # Atlanta 1.1 1.8 vs 1.5 1.4 Columbus -> Over 1.5 (4-5)
        elif (0.9 <= avg1 <= 1.3 and 1.6 <= con1 <= 2.0 and
                1.3 <= avg2 <= 1.7 and 1.2 <= con2 <= 1.6):
                return "Over 1.5 (4-5)"
        else:
            return "Ignore Bet"

    elif league == "LIGUE 1":
        if (1.6 <= avg1 <= 2.0 and 1.6 <= con1 <= 2.0 and
                1.5 <= avg2 <= 1.9 and 1.1 <= con2 <= 1.5):
                return "Over 1.5 (2-4)"

            # Seattle 1.8 1.4 vs 1.2 2.0 LA Galaxy -> Over 1.5 (2-2)
        elif (1.6 <= avg1 <= 2.0 and 1.2 <= con1 <= 1.6 and
                1.0 <= avg2 <= 1.4 and 1.8 <= con2 <= 2.2):
                return "Over 1.5 (2-2)"

            # Vancouver 1.7 1.1 vs 1.7 0.9 Philadelphia -> Over 1.5 (7-0)
        elif (1.5 <= avg1 <= 1.9 and 0.9 <= con1 <= 1.3 and
                1.5 <= avg2 <= 1.9 and 0.7 <= con2 <= 1.1):
                return "Over 1.5 (7-0)"

            # Chicago 1.9 1.8 vs 1.4 1.2 NYCFC -> Over 1.5 (1-3)
        elif (1.7 <= avg1 <= 2.1 and 1.6 <= con1 <= 2.0 and
                1.2 <= avg2 <= 1.6 and 1.0 <= con2 <= 1.4):
                return "Over 1.5 (1-3)"

            # Atlanta 1.1 1.8 vs 1.5 1.4 Columbus -> Over 1.5 (4-5)
        elif (0.9 <= avg1 <= 1.3 and 1.6 <= con1 <= 2.0 and
                1.3 <= avg2 <= 1.7 and 1.2 <= con2 <= 1.6):
                return "Over 1.5 (4-5)"
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
