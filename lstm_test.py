import numpy as np
from scipy.special import softmax
import pandas as pd
import matplotlib.pyplot as plt
import os
from lstm2 import train_lstm
from scoring_players import scorer, most_played_pos
import datetime
from sklearn.model_selection import train_test_split

pd.options.mode.chained_assignment = None  # default='warn'
attackers = []
days_interval = []
fpl_scores = []
min_played = []
start_column = []


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "positions//attackers.txt"), "r") as f:
    for line in f:
        attackers.append(line.strip())

seasons = ['2019-2020', '2020-2021', '2021-2022', '2022-2023']
min_rounds = 20
data = np.zeros((2, 1, min_rounds))
relevant_columns = ['Round', 'Venue', 'FPL Score']

y = np.zeros((1, min_rounds))

first = 1
# preparing data and labels
for j, season in enumerate(seasons):
    for i, attacker in enumerate(attackers):

        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "csvs", attacker, season,"summary.csv")):
            df = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "csvs", attacker, season,"summary.csv"))
        else:
            continue

        df_premier = df[df['Comp'] == 'Premier League']
        if df_premier.shape[0] < min_rounds:
            continue

        position = most_played_pos(df["Pos"])
        date_column = df["Date"]
        #min_played.append(df["Min"].tolist())
        #start_column = df["Start"]
        df_premier['FPL Score'] = df_premier.apply(scorer, axis=1)

        relevant_data = df_premier[df_premier.columns.intersection(relevant_columns)].head(min_rounds)
        relevant_data['Round'] = relevant_data['Round'].str[-1]
        relevant_data['Venue'] = relevant_data['Venue'].replace(r'Home', '1', regex=True)
        relevant_data['Venue'] = relevant_data['Venue'].replace(r'Away', '0', regex=True)
        relevant_data['Venue'] = relevant_data['Venue'].astype(float)
        relevant_data = relevant_data[relevant_data.Round != 'e']
        relevant_data = relevant_data[relevant_data.Round != 'd']
        relevant_data['Round'] = relevant_data['Round']

        # removing rounds that ends in character, as they are not the Premier League
        mask = ~relevant_data['Round'].apply(lambda x: any(char.isalpha() for char in x))
        relevant_data = relevant_data[mask]
        player_season_data = relevant_data[relevant_data.columns.intersection(['Round', 'Venue'])].values.astype(float).T
        #print(player_season_data.shape)

        if first == 1:
            data[:, 0, :] += player_season_data.astype(float)
            y[0, :] += relevant_data['FPL Score'].values
            first = 0
        else:
            data = np.concatenate([data, player_season_data[:, np.newaxis, :]], axis=1)
            y = np.vstack((y, relevant_data['FPL Score'].values))


y = y[np.newaxis, :, :]
all_indices = list(range(data.shape[1]))
train_ind, test_ind = train_test_split(all_indices, test_size=0.2)
x_train, x_test = data[:,train_ind,:], data[:,test_ind, :]
y_train, y_test = y[:,train_ind,:], y[:,test_ind, :]
# print(x_train.shape, x_test.shape, y_train.shape, y_test.shape)

train_lstm(X_train=x_train, Y_train=y_train, X_val=x_test, Y_val=y_test, learning_rate=0.1, num_epochs=20, depth=64)