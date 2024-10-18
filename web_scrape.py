import time
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd


options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(options=options)

# Example URL: https://mundofreestyle.com/resultados-y-tabla-de-la-jornada-2-de-fms-espana-2020/
# fms international's links are like https://mundofreestyle.com/resultados-y-clasificados-de-la-jornada-2-de-fms-internacional-2022/

# New URL. Much better and has everything: https://freestyleros.com/fms-peru/resultados/fms-peru-2024-2025
BASE_URL = "https://mundofreestyle.com/resultados-y-tabla-de-la-jornada-"
COUNTRIES = ["argentina", "chile", "espana", "mexico", "peru", "caribe", "colombia"]
# There is also an FMS Internacional but the links are different so I will leave it out for now
YEARS = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]


def get_link(base_url, country, round, year):
    if country == "internacional":
        pass
        # TODO implement this

    else:  # a country's league
        full_url = base_url + round + "-de-fms-" + country + "-" + year + "/"
        driver.get(full_url)
        time.sleep(2)
        return BeautifulSoup(driver.page_source, "html.parser")


def get_data(soup):
    # Get battle results from page
    date_of_round = soup.find("time", class_="entry-date updated td-module-date")[
        "datetime"
    ]

    results_list = soup.find("ul", class_="wp-block-list")
    results_bullet_points = results_list.find_all("li")

    for result in results_bullet_points:
        # Extract the data
        # The data is in the form of "A ganó a B" with possibly "tras réplica" at the end

        exhibition = False
        result_text = result.text.strip()
        if "tras réplica" in result_text:
            # A won after a tiebreaker
            result_text = result_text.replace(" tras réplica", "")
            replica = True

        else:
            # A won directly
            result_text = result_text.replace(" sin réplica", "")
            replica = False

        if "le ganó a" in result_text:
            # Sometimes text has "le ganó a" instead of "ganó a"
            result_text = result_text.replace(" le ganó a ", " ganó a ")

        if " (Batalla de exhibición)" in result_text:
            exhibition = True
            result_text = result_text.replace(" (Batalla de exhibición)", "")

        winner, loser = result_text.split(" ganó a ")

        # Collate details
        battle_details = {
            "winner": winner.strip(),
            "loser": loser.strip(),
            "replica": str(replica),
            "exhibition": str(exhibition),
            "date": date_of_round,
        }

        results_of_battles.append(battle_details)


results_of_battles = []

for country in COUNTRIES:
    for year in YEARS:
        for jornada in range(1, 15):
            print("Testing for", country, year, jornada)
            time.sleep(2)
            soup = get_link(BASE_URL, country, str(jornada), year)
            if soup.find("h1", class_="entry-title"):  # Not 404
                get_data(soup)
            
            else:
                # Something is wrong (like too many rounds)
                break
            print(f"Got data for {country} {year} round {jornada}")
            print(results_of_battles[-1])


# Convert all battles to a DataFrame
all_battles_df = pd.DataFrame(results_of_battles)

all_battles_df.to_csv("rapBattles.csv", index=False)
