import requests
import json

# Function to fetch and process the games for a given year
def fetch_and_process_games(year):
    # Initialize dictionaries to store results by week and playoff rounds
    week_results = {}
    playoff_results = {
        "Wild Card Round": [],
        "Divisional Round": [],
        "Championship Round": [],
        "Super Bowl": [],
        "Pro Bowl": []  # Added Pro Bowl section
    }

    # Base URL for fetching data for the given year (2022)
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}"

    # Function to process data and append to the dictionary
    def process_game_data(data):
        nonlocal week_results, playoff_results

        # Iterate over the games data
        for game in data.get('events', []):
            # Extract the basic game information
            season = game.get('season', {})

            # Only include the game if the season year matches the year we want
            if str(season.get('year')) != str(year):
                continue  # Skip if the season year does not match the current year

            # Check if the game is regular season or post-season (exclude preseason)
            if season.get('slug') not in ['regular-season', 'post-season']:
                continue  # Skip if it's not a regular season or post-season game
            
            # Extract the week number from the game data
            if 'week' in game and 'number' in game['week']:
                week_number = game['week']['number']
            else:
                week_number = 'Unknown Week'

            # Home and away teams
            competition = game['competitions'][0]
            home_team = competition['competitors'][0]['team']['displayName']
            away_team = competition['competitors'][1]['team']['displayName']
            
            # Scores for both teams
            home_score = competition['competitors'][0]['score']
            away_score = competition['competitors'][1]['score']
            
            # Format the game result as "Home Team Score - Away Team Score"
            result_string = f"{home_team} {home_score} - {away_score} {away_team}"

            if season.get('slug') == 'regular-season':
                if week_number not in week_results:
                    week_results[week_number] = []
                week_results[week_number].append(result_string)
            elif season.get('slug') == 'post-season':
                if 'week' in game and 'number' in game['week']:
                    playoff_week = game['week']['number']
                    if playoff_week == 1:
                        playoff_results["Wild Card Round"].append(result_string)
                    elif playoff_week == 2:
                        playoff_results["Divisional Round"].append(result_string)
                    elif playoff_week == 3:
                        playoff_results["Championship Round"].append(result_string)
                    elif playoff_week == 4:
                        playoff_results["Super Bowl"].append(result_string)
                    elif playoff_week == 5:  # This assumes Pro Bowl is considered as week 5 of the playoffs
                        playoff_results["Pro Bowl"].append(result_string)

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        process_game_data(data)

        next_year = str(year + 1)
        next_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={next_year}"

        response = requests.get(next_url)

        if response.status_code == 200:
            data = response.json()
            process_game_data(data)

        sorted_week_results = dict(sorted(week_results.items(), key=lambda x: (x[0] if isinstance(x[0], int) else float('inf'))))

        final_results = {
            "Regular Season": sorted_week_results,
            "Playoffs": playoff_results
        }

        with open(f"nfl_{year}_game_results_by_week.json", "w") as f:
            json.dump(final_results, f, indent=4)

        print(f"Data saved to nfl_{year}_game_results_by_week.json")

    else:
        print(f"Error fetching data for {year}: {response.status_code}")

years = [2022, 2023, 2024]

for year in years:
    fetch_and_process_games(year)
