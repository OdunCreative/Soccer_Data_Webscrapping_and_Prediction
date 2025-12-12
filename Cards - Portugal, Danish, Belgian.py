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
OUTPUT_CSV   = r"C:\Users\Odun-IT\Desktop\PREDICTION\cards_scrapping_results.csv"

# Map FoxSports team names to your fixtures team names
TEAM_NAME_MAP = {
    "RB Bragantino": "Red Bull Bragantino SP", "Flamengo": "Flamengo RJ", "Mirassol": "Mirassol FC SP",
    "Fortaleza": "Fortaleza EC CE", "Botafogo (RJ)": "Botafogo", "Ceará": "Ceara SC", "Grêmio": "Gremio",
    "Juventude": "EC Juventude RS", 
    "Casa Pia": "Casa Pia Lisbon", "Gil Vicente FC": "Gil Vicente", "AVS Futebol": "Avs Futebol Sad",
    "Famalicão": "FC Famalicao", "Braga": "Sporting Braga", "Alverca": "FC Alverca SAD",
    "Estoril": "Estoril Praia", "Estrela": "Estrela Amadora", "Porto": "FC Porto",
    "Vitória": "Vta de Guimar.", 
    "AGF": "AGF Aarhus", "Viborg": "Viborg FF", "SønderjyskE": "SonderjyskE", "Silkeborg": "Silkeborg IF", 
    "Nordsjælland": "Nordsjaelland", "Brøndby": "Brondby", "Odense": "Odense Boldklub", 

    "Dender": "FCV Dender EH", "Mechelen": "KV Mechelen", "Union SG": "Union Saint-Gilloise",
    "La Louvière": "Raal La Louviere", "Zulte Waregem": "SV Zulte Waregem", "Standard Liège": "Standard Liege",
    "Antwerp": "Royal Antwerp", "OH Leuven": "Oud-Heverlee Leuven", 
}

# Row bands for each league in your fixtures.csv + their FoxSports URLs
# + CK column index (data-index) per league
LEAGUES = {
    "EPL": {
        "start": 2,
        "end": 11,
        "url": "https://www.foxsports.com/soccer/brazil-serie-a/team-stats?category=standard&sort=t_a&season=2025&sortOrder=desc&groupId=21",  # BRAZIL
        "ck_index": 9  # <-- SET CORRECT data-index FOR CK AFTER INSPECTING TABLE
    },
    "LA LIGA": {
        "start": 14,
        "end": 23,
        "url": "https://www.foxsports.com/soccer/primeria-liga/team-stats?category=standard&season=2025&groupId=16",  # PORTUGUESE
        "ck_index": 12  # CHANGE AS NEEDED
    },
    "SERIA A": {
        "start": 26,
        "end": 35,
        "url": "https://www.foxsports.com/soccer/danish-superliga/team-stats?category=standard&season=2025&groupId=99",  # DANISH
        "ck_index": 12  # CHANGE AS NEEDED
    },
    "BUNDESLIGA": {
        "start": 38,
        "end": 46,
        "url": "https://www.foxsports.com/soccer/juliper-league/team-stats?category=standard&season=2025&groupId=18",  # BELGIAN
        "ck_index": 12  # CHANGE AS NEEDED
    },
    "LIGUE 1": {
        "start": 49,
        "end": 57,
        "url": "https://www.foxsports.com/soccer/ligue1/team-stats?category=standard&sort=t_a&season=2024&sortOrder=desc&groupId=43",
        "ck_index": 9  # CHANGE AS NEEDED
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

def scrape_all_team_corner_stats(driver, url: str, ck_index: int):
    """
    Scrapes team -> (gp, avg_corners) from FoxSports team stats page.
    Uses fixed data-index="2" for GP and league-specific ck_index for CK.
    """
    driver.get(url)
    time.sleep(3)  # simple wait; you can switch to WebDriverWait if needed

    team_stats = {}  # { team_name: (gp, avg_corners) }

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody.row-data tr")

    for row in rows:
        try:
            team_name_elem = row.find_element(By.CSS_SELECTOR, 'a.table-entity-name.ff-h')
            team_name = correct_team_name(team_name_elem.text.strip())

            # GP is column data-index="2"
            gp_text = row.find_element(By.CSS_SELECTOR, 'td[data-index="2"] span.table-result').text.strip()
            gp = int(gp_text) if gp_text != "" else 0

            # CK from the index you set in LEAGUES
            ck_cell = row.find_element(By.CSS_SELECTOR, f'td[data-index="{ck_index}"] span.table-result')
            ck_text = ck_cell.text.strip()
            ck = int(ck_text) if ck_text != "" else 0

            avg_corners = round(ck / gp, 2) if gp else 0.0

            team_stats[team_name] = (gp, avg_corners)
        except Exception:
            # Skip any bad/unexpected rows
            continue

    return team_stats

# ---------------------------
# MAIN LEAGUE PROCESSOR
# ---------------------------
def process_league(driver, league_name: str, info: dict):
    url = info["url"]
    start_row = info["start"]
    end_row = info["end"]
    ck_index = info["ck_index"]

    # Scrape all teams' corner averages for the league
    team_stats = scrape_all_team_corner_stats(driver, url, ck_index)

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

            # Fetch gp and avg corners (defaults to zeros if missing)
            gp1, avg_ck1 = team_stats.get(team1, (0, 0.0))
            gp2, avg_ck2 = team_stats.get(team2, (0, 0.0))

            # Expected corners per team (just averages)
            home_exp_corners = avg_ck1
            away_exp_corners = avg_ck2

            # Total expected corner kicks (Home + Away)
            total_exp_corners = round(home_exp_corners + away_exp_corners, 2)

            results.append([
                league_name,
                team1, gp1, home_exp_corners,
                "vs",
                team2, gp2, away_exp_corners,
                total_exp_corners
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
            "League",
            "Home Team", "Home GP", "Home Exp Cards",
            "vs",
            "Away Team", "Away GP", "Away Exp Cards",
            "Total Expected Cards "
        ])

    for league_name, info in LEAGUES.items():
        process_league(driver, league_name, info)

    driver.quit()

if __name__ == "__main__":
    main()
