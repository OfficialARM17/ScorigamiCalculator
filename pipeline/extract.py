import requests
import json

# Function to fetch and process the games for a given year
def fetch_and_process_games(year):
    # Initialize dictionaries to store results by week and playoff rounds
    teams = set()  # Set to collect unique team names
    seasons = set()  # Set to collect unique season-year pairs
    games = []  # List to store game data

    # Base URL for fetching data for the given year
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}"

    # Function to process data and append to the dictionary
    def process_game_data(data):
        nonlocal teams, seasons, games

        # Iterate over the games data
        for game in data.get('events', []):
            # Extract the basic game information
            season = game.get('season', {})
            season_year = str(season.get('year'))
            season_slug = season.get('slug')

            # Only include the game if the season year matches the year we want
            if season_year != str(year):
                continue  # Skip if the season year does not match the current year

            # Check if the game is regular season or post-season (exclude preseason)
            if season_slug not in ['regular-season', 'post-season']:
                continue  # Skip if it's not a regular season or post-season game
            
            # Extract the week number from the game data, if available
            week_number = 'Unknown Week'  # Default value if 'week' or 'number' is missing
            if 'week' in game and 'number' in game['week']:
                week_number = game['week']['number']

            # Home and away teams
            competition = game['competitions'][0]
            home_team = competition['competitors'][0]['team']['displayName']
            away_team = competition['competitors'][1]['team']['displayName']
            
            # Scores for both teams
            home_score = competition['competitors'][0]['score']
            away_score = competition['competitors'][1]['score']
            
            # Round of the game (default to 'Regular Season')
            round_type = 'Regular Season'

            # Check if any notes are present for event headlines like "Super Bowl" or "Conference Championship"
            if 'notes' in competition:
                for note in competition['notes']:
                    if note.get('type') == 'event' and 'headline' in note:
                        headline = note['headline'].lower()  # Convert headline to lowercase for case-insensitive matching
                        
                        if 'super bowl' in headline:
                            round_type = "Super Bowl"
                        elif 'conference championship' in headline:
                            round_type = "Conference Championship"

            # If it's a playoff game, check for normal playoff week numbers
            if season_slug == 'post-season':
                playoff_week = game['week']['number'] if 'week' in game and 'number' in game['week'] else None
                
                # Override round_type if it’s a playoff game that isn't explicitly marked by the event notes
                if playoff_week == 1 and round_type == 'Regular Season':
                    round_type = "Wild Card Round"
                elif playoff_week == 2 and round_type == 'Regular Season':
                    round_type = "Divisional Round"
                elif playoff_week == 3 and round_type == 'Regular Season':
                    round_type = "Championship Round"
                elif (year >= 2009 and playoff_week == 4):  # Pro Bowl occurs before Super Bowl after 2008
                    continue  # Skip Pro Bowl games after 2008 (week 4)
                elif (year <= 2008 and playoff_week == 5):  # Pro Bowl occurs after Super Bowl before 2008
                    continue  # Skip Pro Bowl games before 2008 (week 5)
                elif playoff_week == 4 or playoff_week == 5:  # This is the Super Bowl for years 2008 and after
                    round_type = "Super Bowl"

            # Add teams and season to respective sets
            teams.add(home_team)
            teams.add(away_team)
            seasons.add((season_year, season_slug))

            # Append the game data
            game_info = {
                'season_year': season_year,
                'season_type': season_slug,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'week': week_number,
                'round_type': round_type,
            }
            games.append(game_info)

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        process_game_data(data)

        # Process the next year
        next_year = str(year + 1)
        next_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={next_year}"

        response = requests.get(next_url)

        if response.status_code == 200:
            data = response.json()
            process_game_data(data)

        print(f"Data fetched for {year}")
    else:
        print(f"Error fetching data for {year}: {response.status_code}")

    return teams, seasons, games

# Function to save all data into a single JSON file
def save_to_single_json(all_teams, all_seasons, all_games):
    data = {
        "teams": list(all_teams),
        "seasons": [{"year": season[0], "type": season[1]} for season in all_seasons],
        "games": all_games
    }

    with open("nfl_data_all_years.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Data saved to nfl_data_all_years.json")

# Main function to fetch data for a range of years and accumulate results
def extract_data_for_years(years):
    all_teams = set()
    all_seasons = set()
    all_games = []

    for year in years:
        teams, seasons, games = fetch_and_process_games(year)
        all_teams.update(teams)
        all_seasons.update(seasons)
        all_games.extend(games)

    # Save all accumulated data to a single JSON file
    save_to_single_json(all_teams, all_seasons, all_games)

# List of years to fetch data for (1946 to 2024)
years = list(range(1946, 2025))

# Extract data for each year and save it to a single JSON file
extract_data_for_years(years)
