import streamlit as st
import psycopg2
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv


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

def scorigami_page():
    st.title("Scorigami Finder")
    st.write("Enter the score of a game (Home Team Score - Away Team Score) to check if it has ever happened in the NFL in this century.")
    
    # Get the games data from the database
    games_df = get_games()

    # Check if 'season_year' exists, if not merge with seasons table
    if 'season_year' not in games_df.columns:
        seasons_df = get_seasons()
        games_df = games_df.merge(seasons_df[['season_id', 'year']], left_on='season_id', right_on='season_id', how='left')
        games_df['season_year'] = games_df['year']

    # Get teams data and merge it to get team names based on IDs
    teams_df = get_teams()  # This function should return a DataFrame with team_id and name
    games_df = games_df.merge(teams_df[['team_id', 'name']], left_on='home_team_id', right_on='team_id', how='left')
    games_df = games_df.rename(columns={'name': 'home_team'})
    games_df = games_df.merge(teams_df[['team_id', 'name']], left_on='away_team_id', right_on='team_id', how='left')
    games_df = games_df.rename(columns={'name': 'away_team'})

    # User input for Home and Away Team scores
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        home_score = st.number_input("Home Team Score", min_value=0, step=1)

    with col3:
        away_score = st.number_input("Away Team Score", min_value=0, step=1)

    # Button to check for scorigami
    if st.button("Check Scorigami"):
        # Filter the games where the score matches the user input
        matching_games = games_df[(games_df['home_score'] == home_score) & (games_df['away_score'] == away_score)]
        
        if matching_games.empty:
            st.markdown(f'<h3 style="color: red;">{home_score} - {away_score} has never happened in the NFL in this century!</h3>', unsafe_allow_html=True)
        else:
            st.markdown(f'<h3 style="color: green;">The following games match {home_score} - {away_score}:</h3>', unsafe_allow_html=True)
            
            for index, row in matching_games.iterrows():
                st.markdown(f"""
                    <div style="padding: 10px; border: 2px solid #ccc; margin-bottom: 15px; border-radius: 8px;">
                        <strong>{row['season_year']}:</strong> {row['home_team']} {home_score} - {away_score} {row['away_team']}
                    </div>
                """, unsafe_allow_html=True)

    st.write("### 5 Most Common Scorelines in the NFL:")

    # Get the most common scorelines (home_score - away_score)
    scorelines = games_df.groupby(['home_score', 'away_score']).size().reset_index(name='count')
    common_scorelines = scorelines.sort_values(by='count', ascending=False).head(5)

    # Display the most common scorelines and the number of times they occurred
    for _, row in common_scorelines.iterrows():
        st.markdown(f"""
            <div style="padding: 10px; border: 2px solid #ccc; margin-bottom: 15px; border-radius: 8px;">
                <strong>{row['home_score']} - {row['away_score']}</strong>: {row['count']} occurrences
            </div>
        """, unsafe_allow_html=True)

scorigami_page()
