from trueskill import Rating, rate, setup
import numpy as np

# Set up TrueSkill environment with draw support
env = setup(draw_probability=0)  # no draws! doing minute weighted game results

# Weighted average of player ratings (Gaussian sums)
def weighted_team_rating(players, weights):
    mu_team = sum(w * p.mu for p, w in zip(players, weights))
    sigma_sq_team = sum((w ** 2) * (p.sigma ** 2) for p, w in zip(players, weights))
    return mu_team, sigma_sq_team

# Perform a weighted TrueSkill update with optional draw
# winner: 1 (team1 wins), 2 (team2 wins), 0 (draw)
def weighted_update(team1, team2, weights1, weights2, winner=1):
    w1 = np.array(weights1) / np.sum(weights1)
    w2 = np.array(weights2) / np.sum(weights2)

    mu1, var1 = weighted_team_rating(team1, w1)
    mu2, var2 = weighted_team_rating(team2, w2)

    pseudo_team1 = [Rating(mu1, np.sqrt(var1))]
    pseudo_team2 = [Rating(mu2, np.sqrt(var2))]

    if winner == 1:
        (new_team1,), (new_team2,) = rate([pseudo_team1, pseudo_team2], ranks=[0, 1])
    elif winner == 2:
        (new_team1,), (new_team2,) = rate([pseudo_team1, pseudo_team2], ranks=[1, 0])
    elif winner == 0:
        (new_team1,), (new_team2,) = rate([pseudo_team1, pseudo_team2], ranks=[0, 0])
    else:
        raise ValueError("Winner must be 0 (draw), 1 (team1), or 2 (team2)")

    delta_mu1 = new_team1.mu - mu1
    delta_mu2 = new_team2.mu - mu2
    delta_sigma1 = new_team1.sigma - np.sqrt(var1)
    delta_sigma2 = new_team2.sigma - np.sqrt(var2)

    updated_team1 = [Rating(p.mu + delta_mu1 * w, max(p.sigma + delta_sigma1 * w, 0.0001))
                     for p, w in zip(team1, w1)]
    updated_team2 = [Rating(p.mu + delta_mu2 * w, max(p.sigma + delta_sigma2 * w, 0.0001))
                     for p, w in zip(team2, w2)]

    return updated_team1, updated_team2

# Example usage
# if __name__ == '__main__':
#     team1 = [Rating(), Rating()]
#     team2 = [Rating(), Rating(), Rating()]
#     weights1 = [30, 10]  # e.g. minutes played
#     weights2 = [12, 15, 11]

#     # Simulate a draw
#     updated_team1, updated_team2 = weighted_update(team1, team2, weights1, weights2, winner=0)

#     for i, p in enumerate(updated_team1):
#         print(f"Team 1 - Player {i}: mu={p.mu:.2f}, sigma={p.sigma:.2f}")
#     for i, p in enumerate(updated_team2):
#         print(f"Team 2 - Player {i}: mu={p.mu:.2f}, sigma={p.sigma:.2f}")
