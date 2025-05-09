import kagglehub
from datetime import datetime
import sqlite3
import pandas as pd
from pathlib import Path


db_path, connection, cursor = "nba_data.db", None, None

def init_db():
    global connection, cursor

    # Initialize SQLite database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

def update_db_source():
    # Download latest version
    csv_path = kagglehub.dataset_download("eoinamoore/historical-nba-data-and-player-box-scores")

    # Connect to or create SQLite database
    conn = sqlite3.connect(db_path)

    # Path to folder with CSV files
    csv_folder = Path(csv_path)

    # Load each CSV into its own table
    for file in csv_folder.glob("*.csv"):
        df = pd.read_csv(file)
        table_name = file.stem
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()


    init_db()

def get_playoff_games(year):
    # Use SQL functions to extract the year from the gameDate field
    # Get playoff games for a specific year
    query = f"""
    SELECT * FROM games WHERE strftime('%Y', gameDate) = '{year}' AND gameType = 'Playoffs'
    """
    
    cursor.execute(query)
    return cursor.fetchall()



def get_regular_season_games(start_year):
    pass


if __name__ == "__main__":
    update_db_source()
    year = input("Enter the year to fetch playoff games: ")
    playoff_games = get_playoff_games(year)
    for game in playoff_games:
        print(game)
    

