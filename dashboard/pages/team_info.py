import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
import plotly.express as px  # Plotly for advanced charts

# Set up the connection to PostgreSQL
load_dotenv()

# Database connection settings from .env file
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Load the game data from the database
def get_games():
    conn = get_db_connection()
    query = "SELECT * FROM games"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load team data from the database
def get_teams():
    conn = get_db_connection()
    query = "SELECT * FROM teams"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Load season data from the database
def get_seasons():
    conn = get_db_connection()
    query = "SELECT * FROM seasons"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def team_info_page():
    st.title("Team Information (2000 onwards)")
    st.write("Select a team to view detailed stats from the year 2000 onwards.")

    # Get the teams data
    teams_df = get_teams()

    # Normalize team names for relocated teams
    team_mapping = {
        'San Diego Chargers': 'Los Angeles Chargers',
        'St Louis Rams': 'Los Angeles Rams',
        'Oakland Raiders': 'Las Vegas Raiders',
        'Washington Redskins': 'Washington Commanders',
        'Washington': 'Washington Commanders'
    }

    # Replace team names based on the mapping
    teams_df['normalized_name'] = teams_df['name'].replace(team_mapping)

    # Let the user select a team (normalized name)
    team_names = teams_df['normalized_name'].unique()
    team_name = st.selectbox("Select Team", team_names)

    # Fetch stats for the selected team
    selected_team = teams_df[teams_df['normalized_name'] == team_name].iloc[0]

    # Show basic team info
    st.write(f"**Team:** {selected_team['name']}")

    # Get games data and filter for 2000 onwards
    games_df = get_games()
    
    # Check if 'season_year' exists, if not merge with seasons table
    if 'season_year' not in games_df.columns:
        seasons_df = get_seasons()
        games_df = games_df.merge(seasons_df[['season_id', 'year']], left_on='season_id', right_on='season_id', how='left')
        games_df['season_year'] = games_df['year']

    # Merge team names based on IDs to get 'home_team' and 'away_team' columns
    games_df = games_df.merge(teams_df[['team_id', 'name']], left_on='home_team_id', right_on='team_id', how='left')
    games_df = games_df.rename(columns={'name': 'home_team'})
    games_df = games_df.merge(teams_df[['team_id', 'name']], left_on='away_team_id', right_on='team_id', how='left')
    games_df = games_df.rename(columns={'name': 'away_team'})

    # Normalize the 'home_team' and 'away_team' columns
    games_df['home_team'] = games_df['home_team'].replace(team_mapping)
    games_df['away_team'] = games_df['away_team'].replace(team_mapping)

    # Filter games involving the selected team (by normalized name)
    team_games = games_df[(games_df['home_team'] == team_name) | (games_df['away_team'] == team_name)]

    # Calculate total number of games played by the team
    total_games = team_games.shape[0]

    # Calculate the number of wins (consider home and away)
    team_games['win'] = team_games.apply(lambda row: 1 if (row['home_team'] == team_name and row['home_score'] > row['away_score']) or 
                                         (row['away_team'] == team_name and row['away_score'] > row['home_score']) else 0, axis=1)
    total_wins = team_games['win'].sum()

    # Find the season with the most regular season wins
    team_games['year'] = team_games['season_year']
    regular_season_games = team_games[team_games['round'] == 'Regular Season']
    team_wins = regular_season_games.groupby('year')['win'].sum().reset_index()
    best_season = team_wins.loc[team_wins['win'].idxmax()]

    # Calculate the number of playoff wins
    playoff_games = team_games[team_games['round'] == 'Playoffs']
    playoff_wins = playoff_games.groupby('year')['win'].sum().reset_index()

    # Calculate the number of Super Bowl appearances and wins
    super_bowl_appearances = games_df[(games_df['home_team'] == team_name) | (games_df['away_team'] == team_name) & 
                                      (games_df['round'] == 'Super Bowl')].shape[0]
    super_bowl_wins = games_df[((games_df['home_team'] == team_name) & (games_df['home_score'] > games_df['away_score']) & 
                                (games_df['round'] == 'Super Bowl')) | 
                               ((games_df['away_team'] == team_name) & (games_df['away_score'] > games_df['home_score']) & 
                                (games_df['round'] == 'Super Bowl'))].shape[0]

    # Display Team Information in a white curved box
    st.markdown("""
        <div style="background-color: black; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h3>Team Stats (2000 - Present)</h3>
            <p><strong>Games Played:</strong> {}</p>
            <p><strong>Total Wins (Regular + Playoffs):</strong> {}</p>
            <p><strong>Season with Most Regular Season Wins:</strong> {} ({}) wins</p>
            <p><strong>Super Bowl Appearances:</strong> {} </p>
            <p><strong>Super Bowl Wins:</strong> {} 🏆</p>
        </div>
    """.format(total_games, total_wins, best_season['year'], best_season['win'], super_bowl_appearances, super_bowl_wins), unsafe_allow_html=True)

    # Visualizations
    st.write("### Team Performance over Time")

    # Winning percentage per season
    team_games['win_percentage'] = team_games['win'].groupby(team_games['season_year']).transform('mean')
    win_percentage = team_games.groupby('season_year')['win_percentage'].first().reset_index()

    # Plotting the winning percentage over the years
    fig = px.line(win_percentage, x='season_year', y='win_percentage', title=f"{team_name} Winning Percentage Over Time")
    st.plotly_chart(fig)

    # Plot number of wins per season
    team_wins_fig = px.bar(team_wins, x='year', y='win', title=f"{team_name} Wins Per Season")
    st.plotly_chart(team_wins_fig)


# Call the function to display the Team Information page
team_info_page()
