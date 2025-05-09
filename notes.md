# todo
Overall, we're talking about three learning models:

1. individual player performance model - one model with *many* features to differentiate players, input: player data summary + upcoming matchup metadata, output: player performance prediction.  This is meant to predict the individual contribution of players in a vacuum, accounting for volume, efficiency, and time.  Will probably be a gradient-boosted tree/random forest/something else that can handle large parameterization, but have not looked into it much. Given the importance of more recent data, probably dealing with limited dataset size, so anything NN-based may not be feasible
2. player-on-team performance rating with glicko-2, like what's used in counter-strike matchmaking.  This captures the 'winningness' of players agnostic to statistical contribution. Separate, but important to the overall picture. One-hot encoded categorical to identify player
3. (maybe) lineup synergy + matchup tilt.  one-hot encoded every player in the league x2: home + away team, some model to spit out a home/away edge
4. Meta-model combining the results of 1, 2 and 3, perhaps a linear classifier

So, breaking things down further, Steps are gonna be, approximately:

1. individual player model: research + choose model options
2. individual player model: data pipeline + feature engineering
3. individual player model: training, model selection + hyperparameter tuning, Reg. season + Playoffs
4. learn about glicko-2 alg
5. data pipeline for glicko-2 ratings processing
6. process RS + PO games to get player ratings
7. lineup/synergy model: research + choose model options
8. lineup/synergy model: data pipeline + feature engineering
9. lineup/synergy model: training, model selection + hyperparameter tuning, Reg. season + Playoffs
10. data pipeline for meta-model
11. feature engineering for meta-model
12. training, model selection + hyperparameter tuning for PO meta-model
13. Monte-carlo simulator for playoff bracket, using updated PO ratings/contrib numbers


what if I simplified it.  What if.... I just did shift-level glicko-2 for the regular season + playoffs separately, and team-level regular season stats + series meta-stuff predicting playoff success?

ok, new thing features:

- both teams RS stats
- both teams RS ratings (all players, aggregated somehow)
- playoff state
- both teams playoff rating (all players, aggregated somehow) (updating, snapshotted per game)
- (optional) both teams playoff stats (updating, snapshotted per game)

so, each row is a playoff game, covariates are above

RS stats statically filled for each team slot, just aggregated from known RS results
RS ratings statically filled as well, cover only last RS
PO state is updated based on simulated result
(optional) PO stats are a weighted moving average (account for new series somehow?)****
PO rating is backfilled farther than our training data window so we can have reasonably more stable playoff ratings
    - adjust for shifts? using shifts for the training period is possible, but in simulation we can't do it. seems like we might want to either
        1. update the PO ratings only by game rather than shift when running the alg on old data- this would let us update in simulation more easily and 
        2. try to simulate shifts somehow.  this seems extremely hard


**** could handle this in simulation as follows:
1. simulate the outcome 
2. outcome is derived input to a multivar regression model
3. for each team stat we need, get an output
4. use model SE + a normality assumption to draw from the distribution of that output (i.e. distribution of Y | X, the model output is just the expectation of that dist)

don't think I'll be doing this- not necessary and too much work!


ok, new plan:

1. forget optional running PO stats, too much work to sim, don't need it much anyway
2. get per-season per-team RS stats in one df
3. build rating (probably glicko-2) alg
4. get rs shifts + outcomes in one df
5. get PO game rosters + outcomes in one df
6. use rating alg to generate RS rating df
7. use rating alg to generate PO rating df
8. get PO state df from db
9. merge to one PO game df
10. choose model
10. model training: rolling window validation, maybe 10 playoffs of training, 1 validation, with 5 windows? so 15y of league results





