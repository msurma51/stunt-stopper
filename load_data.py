import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)


games = pd.read_csv("games.csv")
pffScoutingData = pd.read_csv("pffScoutingData.csv")
players = pd.read_csv("players.csv")
plays = pd.read_csv("plays.csv")
week1 = pd.read_csv("week1.csv")
week2 = pd.read_csv("week2.csv")
week3 = pd.read_csv("week3.csv")
week4 = pd.read_csv("week4.csv")
week5 = pd.read_csv("week5.csv")
week6 = pd.read_csv("week6.csv")
week7 = pd.read_csv("week7.csv")
week8 = pd.read_csv("week8.csv")

all_weeks = pd.concat((week1,week2,week3,week4,week5,week6,week7,week8))

# filtering out designed roll-outs
dropBacks = plays[(plays['dropBackType'].isin(['TRADITIONAL','SCRAMBLE_ROLLOUT_RIGHT','SCRAMBLE','SCRAMBLE_ROLLOUT_LEFT'])) &
                  (plays['pff_playAction'] == False)][['gameId','playId']]
# merge dropback passes with play scouting data
dropBackScoutingData = dropBacks.merge(pffScoutingData, on = ['gameId','playId'])
# merge that with tracking data
all_players = all_weeks.merge(dropBackScoutingData, on = ['gameId','playId','nflId'])

# get the ball location for each frame
ball_at_snap = all_weeks[(all_weeks.team == 'football') & (all_weeks.event == 'ball_snap')]
ball_at_snap = ball_at_snap[['gameId','playId','y']]
ball_at_snap = ball_at_snap.rename(columns={"y": "ball_y_snap"})
# x coordinate (yard line) for tracking data is unreliable, using the charted yard line
abs_x = plays[['gameId','playId','absoluteYardlineNumber']].copy()
abs_x.columns.values[2] = 'ball_x_snap'
ball_at_snap = ball_at_snap.merge(abs_x,on = ['gameId','playId'])

# merge ball location with player data
all_players_w_ball = all_players.merge(ball_at_snap, on = ['gameId','playId'])

