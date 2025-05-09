import kagglehub
from datetime import datetime
import sqlite3
import pandas as pd
from pathlib import Path

class Player:
    def __init__(self, player_id, first_name, last_name, minutes):
        self.player_id = player_id
        self.first_name = first_name
        self.last_name = last_name
        self.minutes = minutes

    def __repr__(self):
        return f"Player({self.first_name} {self.last_name}, ID: {self.player_id}, Minutes: {self.minutes})"


class Team:
    def __init__(self, team_name):
        self.team_name = team_name
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def __repr__(self):
        return f"Team({self.team_name}, Players: {len(self.players)})"


class Game:
    def __init__(self, game_id, date, home_win):
        self.game_id = game_id
        self.date = date
        self.home_team = None
        self.away_team = None
        self.home_win = home_win

    def __repr__(self):
        return f"Game(ID: {self.game_id}, Date: {self.date}, Home: {self.home_team.team_name}, Away: {self.away_team.team_name})"


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

def process_game_data(row_list):
    games = []
    game = None
    for row in row_list:
        if not game or game.game_id != row[3]:
            if game:
                games.append(game)
            game = Game(row[3], datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"), row[8] > row[9])
        
        if row[6] == 1:
            if(game.home_team is None):
                game.home_team = Team(row[5])
            game.home_team.add_player(Player(row[2], row[0], row[1], row[7]))
        else:
            if(game.away_team is None):
                game.away_team = Team(row[5])
            game.away_team.add_player(Player(row[2], row[0], row[1], row[7]))
        
    if game:
        games.append(game)
    return games

def get_playoff_games(season_start_year):
    # Use SQL functions to extract the year from the gameDate field
    # Get playoff games for a specific year
    query = f"""
    SELECT p.firstName, p.lastName, p.personId, p.gameId, p.gameDate, p.playerTeamName, p.home, p.numMinutes, g.homeScore, g.awayScore
    FROM games g LEFT JOIN PlayerStatistics p ON g.gameId = p.gameId 
    WHERE strftime('%Y', g.gameDate) = '{season_start_year + 1}' AND g.gameType = 'Playoffs'
    AND p.numMinutes IS NOT NULL AND p.numMinutes > 0
    ORDER BY g.gameDate, g.gameId, p.home ASC
    """
    
    cursor.execute(query)
    return process_game_data(cursor.fetchall())
    

def get_regular_season_games(season_start_year):
    # Get regular season games from September of the start year to May of the next year
    query = f"""
    SELECT p.firstName, p.lastName, p.personId, p.gameId, p.gameDate, p.playerTeamName, p.home, p.numMinutes, g.homeScore, g.awayScore
    FROM games g LEFT JOIN PlayerStatistics p ON g.gameId = p.gameId 
    WHERE g.gameDate BETWEEN '{season_start_year}-09-01' AND '{int(season_start_year) + 1}-05-31' 
    AND g.gameType = 'Regular Season'
    AND p.numMinutes IS NOT NULL AND p.numMinutes > 0
    ORDER BY g.gameDate, g.gameId, p.home ASC
    """
    
    cursor.execute(query)
    return process_game_data(cursor.fetchall())
    # return cursor.fetchall()


if __name__ == "__main__":
    init_db()
    year = input("Enter the year to fetch playoff games: ")
    
    rs_games = get_regular_season_games(year)
    for game in rs_games:
        print(game.home_team.team_name, game.away_team.team_name)
        for player in game.home_team.players:
            print(player)
        for player in game.away_team.players:
            print(player)
    
    
    

