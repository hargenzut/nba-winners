import pandas as pd
from ts_ratings import weighted_update
from trueskill import Rating

def generate_ts_ratings(games_list, game_df_update_callback=None):
    rating_dictionary = dict()
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
            home_mins.append(player.mins)
            
        away_ratings = []
        away_mins = []
        for player in game.away_team.players:
            if player.player_id not in rating_dictionary:
                rating_dictionary[player.player_id] = (Rating(), [])
            
            away_ratings.append(rating_dictionary[player.player_id][0])
            away_mins.append(player.mins)

        # call our rating function, get updated ratings for all players with mins
        new_home_ratings, new_away_ratings = weighted_update(home_ratings, away_ratings, home_mins, away_mins, winner=1 if game.home_win else 2)

        # update the dictionary with the new ratings
        for i, player in enumerate(game.home_team.players):
            rating_dictionary[player.player_id] = (new_home_ratings[i], rating_dictionary[player.player_id][1] + [player.mins])

        for i, player in enumerate(game.away_team.players):
            rating_dictionary[player.player_id] = (new_away_ratings[i], rating_dictionary[player.player_id][1] + [player.mins])

        # return dictionary
        return rating_dictionary

def generate_ts_ratings_pregame(games_list):
    
    pregame_ratings_df = pd.DataFrame(columns=["game_date", "home_team_name", "away_team_name", "home_team_rating", "away_team_rating"])

    def df_update_callback(game, rating_dict):
        home_team_rating = compute_team_rating(rating_dict, game.home_team)
        away_team_rating = compute_team_rating(rating_dict, game.away_team)
        pregame_ratings_df.loc[len(pregame_ratings_df)] = {
            "game_date": game.date,
            "home_team_name": game.home_team.name,
            "away_team_name": game.away_team.name,
            "home_team_rating": home_team_rating,
            "away_team_rating": away_team_rating
        }

    return pregame_ratings_df, generate_ts_ratings(games_list, game_df_update_callback=df_update_callback)


def compute_team_rating(ratings_dict, team):
    pass

def generate_rs_ratings(games_list):
    pass

def generate_rs_rating_period(season_range):
    pass

def generate_po_pregame_ratings(season_range, prefix_seasons_size):
    pass
