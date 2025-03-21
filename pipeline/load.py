import json
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Database connection settings from .env file
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Function to load data from the JSON file
def load_data_from_json(input_file="nfl_data_all_years.json"):
    with open(input_file, "r") as f:
        data = json.load(f)
    return data

# Function to insert teams into the database
def insert_teams(teams, cursor):
    for team in teams:
        cursor.execute("""
            INSERT INTO teams (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING;
        """, (team,))

# Function to insert seasons into the database
def insert_seasons(seasons, cursor):
    for season in seasons:
        cursor.execute("""
            INSERT INTO seasons (year, type)
            VALUES (%s, %s)
            ON CONFLICT (year, type) DO NOTHING;
        """, (season['year'], season['type']))

# Function to insert games into the database
def insert_games(games, cursor):
    for game in games:
        season_id = get_season_id(game['season_year'], game['season_type'], cursor)
        home_team_id = get_team_id(game['home_team'], cursor)
        away_team_id = get_team_id(game['away_team'], cursor)
        
        if season_id and home_team_id and away_team_id:
            # Parse the date (assume date is provided in the "YYYY-MM-DD" format)
            game_date = datetime.strptime(game.get('date', '1970-01-01'), '%Y-%m-%d')  # Default if no date is provided
            
            cursor.execute("""
                INSERT INTO games (season_id, home_team_id, away_team_id, home_score, away_score, date, week, round)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                season_id,
                home_team_id,
                away_team_id,
                game['home_score'],
                game['away_score'],
                game_date,
                game['week'],
                game['round_type']
            ))

# Function to get the team ID by team name
def get_team_id(team_name, cursor):
    cursor.execute("""
        SELECT team_id FROM teams WHERE name = %s;
    """, (team_name,))
    result = cursor.fetchone()
    return result[0] if result else None

# Function to get the season ID by year and type
def get_season_id(year, season_type, cursor):
    cursor.execute("""
        SELECT season_id FROM seasons WHERE year = %s AND type = %s;
    """, (year, season_type))
    result = cursor.fetchone()
    return result[0] if result else None

# Main function to load data into the database
def load_data_to_db(input_file="nfl_data_all_years.json"):
    # Connect to the PostgreSQL database using credentials from the .env file
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    try:
        # Load the data from the JSON file
        data = load_data_from_json(input_file)

        # Insert teams into the database
        print("Inserting teams...")
        insert_teams(data['teams'], cursor)

        # Insert seasons into the database
        print("Inserting seasons...")
        insert_seasons(data['seasons'], cursor)

        # Insert games into the database
        print("Inserting games...")
        insert_games(data['games'], cursor)

        # Commit the changes to the database
        conn.commit()
        print("Data successfully inserted into the database.")

    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error during data insertion: {e}")

    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Call the function to load data into the database
    load_data_to_db()
