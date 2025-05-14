import pandas as pd
from db_extract import get_playoff_game_metadata_range
from rate_games import generate_rs_rating_period, generate_po_pregame_ratings

# db extract- playoff game metadata, rate_games- rs_rating_period, po_pregame_ratings

# final df - 
# non-features: gameId, gameDate, team_a_name, team_b_name
# features: team_a_home, seriesGameNumber, team_a_series_wins, team_b_series_wins, series_diff,
# home_team_rs_rating, home_team_rs_rating_var, away_team_rs_rating, away_team_rs_rating_var, 
# home_team_po_rating, home_team_po_rating_var, away_team_po_rating, away_team_po_rating_var

# starting with: 16 seasons of data, 5 year playoff prefix, train/validation split of 8 seasons/2 seasons, rolling window of 1 season, so we can validate 5 different sets
# test the finished model on the last 2 seasons
# in total: 21 seasons of playoffs, 16 regular seasons

def extract_features(season_start_year_range, playoff_rating_prefix):
    start_season_year, end_season_year = season_start_year_range

    # PO game metadata
    po_game_metadata_list = get_playoff_game_metadata_range(season_start_year_range)

    # PO pregame ratings
    po_pregame_df = generate_po_pregame_ratings(season_start_year_range, playoff_rating_prefix)

    # RS ratings
    rs_ratings_df = generate_rs_rating_period(season_start_year_range)

    # Merge PO game metadata with PO pregame ratings
    po_game_metadata_df = pd.DataFrame(po_game_metadata_list, columns=["game_id", "game_date", "team_a_name", "team_b_name", "team_a_home", "series_game_number", "team_a_series_wins", "team_b_series_wins", "series_diff", "season_start_year", "team_a_win"])
    po_game_metadata_df = po_game_metadata_df.merge(po_pregame_df, left_on=["game_id", "game_date" "team_a_name", "team_b_name"], right_on=["game_id", "game_date" "team_a_name", "team_b_name"], how="left")
    po_game_metadata_df = po_game_metadata_df.merge(rs_ratings_df, left_on=["team_a_name", "season_start_year"], right_on=["team_name", "season_start_year"], how="left")
    po_game_metadata_df = po_game_metadata_df.rename(columns={"rating_mean": "team_a_rs_rating", "rating_var": "team_a_rs_rating_var"})
    po_game_metadata_df = po_game_metadata_df.merge(rs_ratings_df, left_on=["team_b_name", "season_start_year"], right_on=["team_name", "season_start_year"], how="left")
    po_game_metadata_df = po_game_metadata_df.rename(columns={"rating_mean": "team_b_rs_rating", "rating_var": "team_b_rs_rating_var"})
    return po_game_metadata_df

# call once for up to date data.  In an operational setting we would update incrementally with a service/job, but not necessary for this scale
def update_features():
    # Define the range of seasons to extract features for
    season_start_year_range = (2005, 2021)  # Example range from 2005 to 2021
    playoff_rating_prefix = 5  # Example prefix size

    # Extract features + save to CSV
    features_df = extract_features(season_start_year_range, playoff_rating_prefix)
    features_df.to_csv("playoff_features.csv", index=False)

def load_data():
    # Load the data from the CSV file
    features_df = pd.read_csv("playoff_features.csv")
    return features_df

