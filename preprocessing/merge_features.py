import pandas as pd
from db_extract import get_playoff_game_metadata_range, update_db_source, init_db
from rate_games import generate_rs_rating_period, generate_po_pregame_ratings
import argparse

# db extract- playoff game metadata, rate_games- rs_rating_period, po_pregame_ratings

# final df - 
# non-features: gameId, gameDate, team_a_name, team_b_name
# features: team_a_home, seriesGameNumber, team_a_series_wins, team_b_series_wins, series_diff,
# home_team_rs_rating, home_team_rs_rating_var, away_team_rs_rating, away_team_rs_rating_var, 
# home_team_po_rating, home_team_po_rating_var, away_team_po_rating, away_team_po_rating_var

# starting with: 16 seasons of data, 5 year playoff prefix, train/validation split of 8 seasons/2 seasons, rolling window of 1 season, so we can validate 5 different sets
# test the finished model on the last 2 seasons
# in total: 21 seasons of playoffs, 16 regular seasons

def extract_features(season_start_year_range = (2009, 2024), playoff_rating_prefix = 5, output_dir="output/"):
    print("Extracting season start range: ", season_start_year_range, "and playoff rating prefix: ", playoff_rating_prefix)

    # PO game metadata
    print("Extracting playoff game metadata...")
    po_game_metadata_list = get_playoff_game_metadata_range(season_start_year_range)
    po_game_metadata_df = pd.DataFrame(po_game_metadata_list, columns=["game_id", "game_date", "team_a_name", "team_b_name", "team_a_home", "series_game_number", "team_a_series_wins", "team_b_series_wins", "series_diff", "season_start_year", "team_a_win"])
    print(po_game_metadata_df.head())
    po_game_metadata_df.to_csv(output_dir + "playoff_game_metadata.csv", index=False)

    # PO pregame ratings
    print("Generating playoff pregame ratings...")
    po_pregame_df = generate_po_pregame_ratings(season_start_year_range, playoff_rating_prefix)
    print(po_pregame_df.head())
    po_pregame_df.to_csv(output_dir + "playoff_pregame_ratings.csv", index=False)


    # RS ratings
    print("Generating regular season ratings...")
    rs_ratings_df = generate_rs_rating_period(season_start_year_range)
    print(rs_ratings_df.head())
    rs_ratings_df.to_csv(output_dir + "regular_season_ratings.csv", index=False)

    # Merge PO game metadata with PO pregame ratings
    print("Merging playoff game metadata with pregame ratings...", end="", flush=True)
    po_game_metadata_df = po_game_metadata_df.merge(po_pregame_df, left_on=["game_id", "team_a_name", "team_b_name", "season_start_year"], right_on=["game_id", "team_a_name", "team_b_name", "season_start_year"], how="left")
    print("done")
    print(po_game_metadata_df.head())
    
    print("Merging playoff game metadata with regular season ratings...", end="", flush=True)
    po_game_metadata_df = po_game_metadata_df.merge(rs_ratings_df, left_on=["team_a_name", "season_start_year"], right_on=["team_name", "season_start_year"], how="left")
    po_game_metadata_df = po_game_metadata_df.rename(columns={"rating_mean": "team_a_rs_rating", "rating_var": "team_a_rs_rating_var"})
    po_game_metadata_df = po_game_metadata_df.merge(rs_ratings_df, left_on=["team_b_name", "season_start_year"], right_on=["team_name", "season_start_year"], how="left")
    po_game_metadata_df = po_game_metadata_df.rename(columns={"rating_mean": "team_b_rs_rating", "rating_var": "team_b_rs_rating_var"})
    po_game_metadata_df = po_game_metadata_df.drop(columns=["team_name_x", "team_name_y"])
    print("done")
    print(po_game_metadata_df.head())
    po_game_metadata_df.to_csv(output_dir + "playoff_features.csv", index=False)

def load_data(output_dir="output/"):
    # Load the data from the CSV file
    features_df = pd.read_csv(output_dir + "playoff_features.csv")
    return features_df

# call once for up to date data.  In an operational setting we would update incrementally with a service/job, but not necessary for this scale
if __name__ == "__main__":

    # param for updating the db source or not
    parser = argparse.ArgumentParser(description="Update database and features.")
    parser.add_argument("--update-db", action="store_true", help="Flag to update the database source.")
    args = parser.parse_args()

    if args.update_db:
        # Update the database source
        print("Updating database source...", end="", flush=True)
        update_db_source()
        print("done")
    else:
        print("Skipping database source update...")
        print("Init db...", end="", flush=True)
        init_db()
        print("done")
    

    # Update the features
    print("Updating features csv...", end="", flush=True)
    extract_features()
    print("done updating features csv.")

