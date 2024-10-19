import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd


def get_link(driver, base_url, country, round, year):
    """Create full URL including relevant details and return beautifulsoup object"""

    # a country's league


    full_url = f"{base_url}{country}/resultados/fms-{country}-{year}/fms-{country}-{year}-jornada-{round}"
    driver.get(full_url)
    time.sleep(2)
    logging.info(full_url)
    return BeautifulSoup(driver.page_source, "html.parser")


def get_data(soup, country, year, jornada, results_of_battles):
    """Get battle results from page"""

    if soup.find("span", class_="text-dark fw-bold"):
        # Not happened yet, so just end function
        return results_of_battles

    date_of_round = soup.find("span", id="fecha_completa").text.strip()
    date_of_round, location = date_of_round.split(
        "  "
    )  # 2 spaces between date and location
    logging.info('Date of round: %(date_of_round)s')

    table_of_results = soup.find("table", id="tabla_participantes")

    results_bullet_points = (table_of_results.find("tbody")).find_all("tr")

    for result in results_bullet_points:
        # Extract the data

        names = result.find_all("span", class_="d-block fw-bold")
        points = result.find_all("span", class_="fs-1")
        replica_status = result.find("span", class_=["badge", "fs-9"])

        if result.find(
            "span", class_="text-info"
        ):  # This will be there for exhibition battles
            exhibition = True
        else:
            exhibition = False

        if points == []:
            points = [0, 0]
            # This was an exhibition battle with no scoring

        # Get details
        rapper_1 = names[0].text.strip()
        rapper_2 = names[1].text.strip()
        points_1 = points[0].text.strip()
        points_2 = points[1].text.strip()
        replica_status = replica_status.text.strip()

        if points_1 > points_2:
            winner = rapper_1
            loser = rapper_2
            draw = False

        elif points_2 > points_1:
            winner = rapper_2
            loser = rapper_1
            draw = False

        else:
            winner = rapper_1
            loser = rapper_2
            draw = True

        # Collate details
        battle_details = {
            "winner": winner,
            "loser": loser,
            "replica": replica_status,
            "exhibition": str(exhibition),
            "draw": str(draw),
            "location": location.strip(),
            "league": "FMS " + country.capitalize(),
            "round": str(jornada),
            "year": year.strip(),
            "date": date_of_round.strip(),
        }

        results_of_battles.append(battle_details)

    return results_of_battles


def main():

    # Set up logging
    logging_level = logging.INFO
    logging_format = '[%(levelname)s] %(message)s'
    logging.basicConfig(level=logging_level, format=logging_format)

    # Set up the web driver
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(options=options)

    # Example URL: https://freestyleros.com/fms-peru/resultados/fms-peru-2020-2021/fms-peru-2020-2021-jornada-1
    BASE_URL = "https://freestyleros.com/fms-"

    COUNTRIES = ["argentina", "chile", "espana", "mexico", "peru", "caribe", "colombia"]

    YEARS = [
        "2017-2018",
        "2018-2019",
        "2019-2020",
        "2020-2021",
        "2021-2023",  # Not a mistake, was over 2 years due to COVID
        "2024-2025",
    ]

    results_of_battles = []

    for country in COUNTRIES:
        for year in YEARS:
            for jornada in range(1, 15):
                logging.info('Testing for %s %s round %s' % (country,year,jornada))
                time.sleep(2)
                soup = get_link(driver, BASE_URL, country, str(jornada), year)
                if soup.find("table", id="tabla_participantes"):  # Not 404
                    results_of_battles = get_data(
                        soup, country, year, jornada, results_of_battles
                    )

                else:
                    logging.debug('No data for %s %s round %s' % (country,year,jornada))
                    # Something is wrong (like too many rounds)
                    break

                logging.info('Got data for %s %s round %s' % (country,year,jornada))
                logging.debug(results_of_battles[-1])

    # Convert all battles to a DataFrame
    all_battles_df = pd.DataFrame(results_of_battles)

    # Save to CSV, different encoding due to accented characters
    all_battles_df.to_csv("rap_battles2.csv", encoding="iso-8859-1", index=False)


if __name__ == "__main__":
    main()
