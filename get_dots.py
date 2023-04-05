# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 05:54:18 2023

@author: surma
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from name_space import tm_color_spec
from function_space import play_subframe
from load_data import plays

pass_rush = pd.read_csv('pass_rush.csv', index_col = 0)
pass_pro = pd.read_csv('pass_pro.csv', index_col = 0)
all_stunt_info = pd.read_csv('stunt_info.csv', index_col = 0)
play_info = plays[['gameId', 'playId', 'quarter', 'gameClock']]
all_stunt_info = all_stunt_info.merge(play_info, on = ['gameId', 'playId'])
all_matchups = pd.read_csv('matchups.csv', index_col = 0)

all_rush_pro = pd.concat((pass_rush, pass_pro))

def build_a_gif(game, play, stunt = 1.0):
    temp = play_subframe(all_rush_pro, game, play)
    stunt_query = "gameId == {} & playId == {} & stuntId == {}".format(game,play,stunt)
    info = all_stunt_info.query(stunt_query).iloc[0]
    matchups = all_matchups.query(stunt_query)
    
    fig, ax = plt.subplots(dpi=141)

    fig.set_figheight(5.0)
    fig.set_figwidth(5.0)
    
    ax.axhline(0, color = 'blue', zorder = 0)
    ax.axhline(-5, color = 'black', zorder = 0)
    ax.axhline(-10, color = 'black', zorder = 0)
    y = np.arange(-15,0,1)
    ax.hlines(y, xmin = -4, xmax = -3, color = 'black')
    ax.hlines(y, xmin = 3, xmax = 4, color = 'black')
    
    teams = list(temp['team'].unique())
    test = temp.iloc[0]
    off_team = str(np.where(test['qb_x_rel'] > 0, test['team'], 
                            [team for team in teams if team != test['team']][0]))
    def_team = [team for team in teams if team != off_team][0]
    plt.title('off: {} --- def: {} --- qtr: {} --- clock: {}\ngame: {} --- play: {} --- stunt: {}'.format(
        off_team, def_team, info['quarter'], info['gameClock'], int(game), int(play), int(stunt)), fontsize = 10.0)
    plt.xlabel('type: {} --- time to overlap: {} --- rush win: {}'.format(
        info['stunt_type'], info['time_to_overlap']/10, info['rush_win'] == 1.0))

    qb_frames = temp[temp['qb_x_rel'] > -100][['frameId','team', 'qb_x_rel', 'qb_y_rel']].drop_duplicates()
    qb_frames[['x_rel', 'y_rel']] = qb_frames[['qb_x_rel', 'qb_y_rel']]
    temp = pd.concat((temp,qb_frames))
    color_map_primary = {team : list(tm_color_spec[team].values())[0] for team in tm_color_spec.keys()}
    color_map_secondary = {team : list(tm_color_spec[team].values())[1] for team in tm_color_spec.keys()}
    temp['dot_color'] = np.where(temp['qb_x_rel'] > -100, temp['team'].map(color_map_primary), 'white')
    temp['edge_color'] = temp['team'].map(color_map_secondary)
    temp['number_color'] = np.where(temp['qb_x_rel'] > -100, 'white', 
                                  temp['team'].map(color_map_primary))
    temp['jerseyNumber'] = temp['jerseyNumber'].fillna(0.0).astype('int64')
    temp['num_str'] = np.where(temp['jerseyNumber'] > 0, temp['jerseyNumber'].astype('string'), 'QB')
    
    paths = temp[temp['nflId'].isin(matchups['nflId_def'])][['nflId','frameId','x_rel', 'y_rel']].copy()
    penetrator_map = matchups.groupby('nflId_def')['penetrator'].max()
    line_color = lambda x: 'red' if x == 'penetrator' else 'green'
    
    max_width_ball = max(temp['x_rel'].abs().max() + 1, 8)  
    width_yards = max_width_ball*2
    width_pix = ax.get_window_extent().width
    s = (width_pix / width_yards)*np.pi*2
   
    snap_frame = temp['frameId'].min()
    frame_numbers = list(range(snap_frame, temp['frameId'].max() + 1))


    snap_frames = temp[temp['frameId'] == snap_frame]
    scatter = ax.scatter(snap_frames['x_rel'], 
                         snap_frames['y_rel'], 
                         s = s, 
                         alpha = 1.0,
                         color = snap_frames['dot_color'], 
                         edgecolors = snap_frames['edge_color'], 
                         linewidths = 2,
                         zorder = 5)
    

    x_corr = -0.32
    y_corr = -0.15
    numbers = [ax.annotate(player['num_str'], xy = (player['x_rel'] + x_corr, player['y_rel'] + y_corr), 
                           fontsize = 7.0, zorder = 10, color = player['number_color']) 
               for index, player in snap_frames.iterrows()]


    def init():
        ax.set_xlim(-1*max_width_ball, max_width_ball)
        ax.set_ylim(temp['y_rel'].min()-1, temp['y_rel'].max()+1)
        return [scatter, *numbers]

    def update(frame_number):
        temp_frame = temp[temp['frameId'] == frame_number]
        scatter.set_offsets(np.c_[temp_frame['x_rel'],
                                  temp_frame['y_rel']])
        for i in range(len(numbers)):
            numbers[i].set_position((temp_frame.iloc[i]['x_rel'] + x_corr, temp_frame.iloc[i]['y_rel'] + y_corr))
        lines = []
        path_frames = paths[paths['frameId'] < frame_number+1]
        for player in path_frames['nflId'].unique(): 
            player_frames = path_frames[path_frames['nflId'] == player]
            role = 'penetrator' if penetrator_map.loc[player] == 1.0 else 'looper'
            line = ax.plot(player_frames['x_rel'], player_frames['y_rel'], linestyle = '-', marker = None,
                           color = line_color(role), label = role)
            lines.append(line)
        
        return [scatter, *lines, *numbers]
    
            
    # chugga chugga choo choo
    anim = FuncAnimation(fig, update, init_func = init, interval=100, frames=frame_numbers, repeat=True)
    
    # remove the axis/ticks from the gif
    plt.xticks([]),plt.yticks([])
    
    # saving the gif 
    fname = '_'.join([str(int(item)) for item in (game,play,stunt)]) + '.gif'
    anim.save('dots/'+fname, writer = animation.PillowWriter(fps=10))
    plt.close()

for index, row in all_stunt_info[['gameId', 'playId', 'stuntId']].iterrows():
    try:
        build_a_gif(row['gameId'], row['playId'], row['stuntId'])
    except Exception as e:
        print('Error in game {} play {} stunt {}'.format(row['gameId'], row['playId'], row['stuntId']))
        print(e)
