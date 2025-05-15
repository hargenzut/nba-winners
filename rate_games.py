from numpy import average
import pandas as pd
from ts_ratings import weighted_update, weighted_team_rating
from db_extract import get_season_end_rosters, get_regular_season_games, get_playoff_games
from trueskill import Rating

def generate_ts_ratings(games_list, rating_dictionary = dict(), game_df_update_callback=None):

    for game in games_list:

        if game_df_update_callback:
            game_df_update_callback(game, rating_dictionary)

        # get player ratings from the dictionary + mins from the game
        home_ratings = []
        home_mins = []
        for player in game.home_team.players:
            if player.player_id not in rating_dictionary:
                rating_dictionary[player.player_id] = (Rating(), [])
            
            home_ratings.append(rating_dictionary[player.player_id][0])
            home_mins.append(player.minutes)
            
        away_ratings = []
        away_mins = []
        for player in game.away_team.players:
            if player.player_id not in rating_dictionary:
                rating_dictionary[player.player_id] = (Rating(), [])
            
            away_ratings.append(rating_dictionary[player.player_id][0])
            away_mins.append(player.minutes)

        # call our rating function, get updated ratings for all players with mins
        new_home_ratings, new_away_ratings = weighted_update(home_ratings, away_ratings, home_mins, away_mins, winner=1 if game.home_win else 2)

        # update the dictionary with the new ratings
        for i, player in enumerate(game.home_team.players):
            rating_dictionary[player.player_id] = (new_home_ratings[i], rating_dictionary[player.player_id][1] + [player.minutes])

        for i, player in enumerate(game.away_team.players):
            rating_dictionary[player.player_id] = (new_away_ratings[i], rating_dictionary[player.player_id][1] + [player.minutes])

    # return dictionary
    return rating_dictionary

def generate_ts_ratings_pregame(games_list, prefix_ratings_dict=dict()):    
    pregame_ratings_df = pd.DataFrame(columns=["game_id", "team_a_name", "team_b_name", "team_a_po_rating", "team_a_po_rating_var", "team_b_po_rating", "team_b_po_rating_var"])

    def df_update_callback(game, rating_dict):
        home_team_rating, home_team_rating_var = compute_team_rating(rating_dict, game.home_team)
        away_team_rating, away_team_rating_var = compute_team_rating(rating_dict, game.away_team)

        team_a_is_home = game.home_team.team_name > game.away_team.team_name
        pregame_ratings_df.loc[len(pregame_ratings_df)] = {
            "game_id": game.game_id,
            "team_a_name": game.home_team.team_name if team_a_is_home else game.away_team.team_name,
            "team_b_name": game.away_team.team_name if team_a_is_home else game.home_team.team_name,
            "team_a_po_rating": home_team_rating if team_a_is_home else away_team_rating,
            "team_a_po_rating_var": home_team_rating_var if team_a_is_home else away_team_rating_var,
            "team_b_po_rating": away_team_rating if team_a_is_home else home_team_rating,
            "team_b_po_rating_var": away_team_rating_var if team_a_is_home else home_team_rating_var
        }

    return pregame_ratings_df, generate_ts_ratings(games_list, prefix_ratings_dict, game_df_update_callback=df_update_callback)


def compute_team_rating(ratings_dict, team):
    
    # default here handled below
    # # if no players, return default rating
    # if len(team.players) == 0:
    #     rating_default = Rating()
    #     return rating_default.mu, rating_default.sigma ** 2
    
    # otherwise...
    team_ratings = []
    team_mins = []
    for player in team.players:
        if player.player_id in ratings_dict:
            team_ratings.append(ratings_dict[player.player_id][0])
            team_mins.append(average(ratings_dict[player.player_id][1]))

    # if our total average mins for everyone on the roster is below 240 (total person-min for a game), add a "default" player to our list with
    # a default rating and the remaining mins
    # this accounts for a roster where we only know about low-mins players, or don't have data on anyone
    if sum(team_mins) < 240:
        default_player = Rating()
        team_ratings.append(default_player)
        team_mins.append(240 - sum(team_mins))

    # normalize mins (weights)
    team_mins = [x / 240 for x in team_mins]
    return weighted_team_rating(team_ratings, team_mins)

def generate_rs_ratings(games_list, roster_list):
    ratings_dict = generate_ts_ratings(games_list)

    team_ratings_df = pd.DataFrame(columns=["team_name", "rating_mean", "rating_var"])
    for team in roster_list:
        mean, var = compute_team_rating(ratings_dict, team)
        team_ratings_df.loc[len(team_ratings_df)] = {
            "team_name": team.team_name,
            "rating_mean": mean,
            "rating_var": var
        }

    return team_ratings_df


def generate_rs_rating_period(season_range):
    start_season, end_season = season_range

    rs_ratings_period_df = pd.DataFrame(columns=["season_start_year", "team_name", "rating_mean", "rating_var"])
    for season_year in range(start_season, end_season + 1):

        print("Calculating regular season ratings for: ", season_year, "... ", end="", flush=True)

        # Get the games and rosters for the current season
        games_list = get_regular_season_games(season_year)
        roster_list = get_season_end_rosters(season_year)

        # Generate ratings for the current season
        ratings_df = generate_rs_ratings(games_list, roster_list)

        # add to the period dataframe
        for i, row in ratings_df.iterrows():
            rs_ratings_period_df.loc[len(rs_ratings_period_df)] = {
                "season_start_year": season_year,
                "team_name": row["team_name"],
                "rating_mean": row["rating_mean"],
                "rating_var": row["rating_var"]
            }

        print("Done")

    return rs_ratings_period_df

def generate_po_pregame_ratings(season_range, prefix_seasons_size):
    start_season, end_season = season_range

    prefix_po_games = []
    for season_year in range(start_season - prefix_seasons_size, start_season):
        print("Getting prefix playoff games for: ", season_year, "... ", end="", flush=True)
        prefix_po_games = prefix_po_games + get_playoff_games(season_year)
        print("Done")

    print("Generating prefix ratings for playoff games...", end="", flush=True)
    prefix_ratings_dict = generate_ts_ratings(prefix_po_games)
    print("Done")

    po_ratings_df = pd.DataFrame(columns=["season_start_year", "game_id", "team_a_name", "team_b_name", "team_a_po_rating", "team_a_po_rating_var", "team_b_po_rating", "team_b_po_rating_var"]) 
    for season_year in range(start_season, end_season + 1):
        
        print("Getting prefix ratings for: ", season_year, "... ", end="", flush=True)
        
        # Get the games and rosters for the current season
        games_list = get_playoff_games(season_year)

        # Generate ratings for the current season
        pregame_ratings_df, prefix_ratings_dict = generate_ts_ratings_pregame(games_list, prefix_ratings_dict)

        # add to the period dataframe'
        for i, row in pregame_ratings_df.iterrows():
            po_ratings_df.loc[len(po_ratings_df)] = {
                "season_start_year": season_year,
                "game_id": row["game_id"],
                "team_a_name": row["team_a_name"],
                "team_b_name": row["team_b_name"],
                "team_a_po_rating": row["team_a_po_rating"],
                "team_a_po_rating_var": row["team_a_po_rating_var"],
                "team_b_po_rating": row["team_b_po_rating"],
                "team_b_po_rating_var": row["team_b_po_rating_var"]
            }

        print("Done")

    return po_ratings_df
