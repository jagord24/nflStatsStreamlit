import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go # or plotly.express as px

st.title('Season Passing Leader')

# create range of seasons to select from

number = st.number_input('Enter a season', step=1, min_value=2001, max_value=2023)

# list of all NFL team abbreviations for use in selectbox


# create selectbox for team selection

teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN',
            'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LAC', 'LAR', 'LV', 'MIA',
            'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB',
            'TEN', 'WAS']
team = st.selectbox('Select a team to get started', teams)

@st.cache_data
def get_pbp_data(year):
    url = url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.parquet"
    df = pd.read_parquet(url)
    # df = df[(df.home_team == team) | (df.away_team == team)].reset_index(drop=True)
    return df

@st.cache_data
def filter_pbp_for_team(df, team):
    df = df[(df.home_team == team) | (df.away_team == team)].reset_index(drop=True)
    return df

@st.cache_data
def get_roster_data(year):
    url = f'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{year}.parquet'
    df = pd.read_parquet(url)
    return df

# roster = get_roster_data(number)

data_load_state = st.text('Loading data...')
data = get_pbp_data(number)
data_load_state.text('Loading data...done!')

# aggregate the sum of passing_yards by passer_player_name
if team == 'All':
    passing_yards = data.groupby('passer_player_name').passing_yards.sum().reset_index()
else:
    passing_yards = filter_pbp_for_team(data[data['posteam'] == team], team).groupby('passer_player_id').passing_yards.sum().reset_index()

# st.subheader(f'Passing Yard Leaders for {number}')
# st.dataframe(passing_yards[passing_yards['passing_yards'] > 0].sort_values(by='passing_yards', ascending=False),
#                 column_config={
#                 'passer_player_name': 'Player',
#                 'passing_yards': 'Passing Yards'
#                 },
#              hide_index=True,
#              use_container_width=True
#         )

def get_scoring_plays(df):
    scoring_plays = df[
                        (df['quarter_end'] == 1) | # additional data points for when there are scoreless games or quarters
                        (df['sp'] == 1)  # limit dataset to scoring plays
                        # (df['play_id'] == 1) # include start of game in addition to the end of each quarter
                    ]
    return scoring_plays
# scoring_plays = get_scoring_plays(data)

# # get the plays that were the start of each game. this should be the minimum play_id for each game_id
# game_starts = data.groupby('game_id').play_id.min().reset_index()

# st.dataframe(scoring_plays[['desc', 'home_team', 'away_team', 'total_home_score', 'total_away_score', 'play_id', 'game_seconds_remaining', 'game_half']],
#              use_container_width=True)

df = data[data['game_half'] != 'Overtime'].copy()

df.loc[:,'game_seconds_elapsed'] = df.apply(lambda row: 3600 - row['game_seconds_remaining'], axis=1)
df.loc[:,'season_seconds_elapsed'] = df.apply(lambda row: (row['week'] - 1) * 3600 + row['game_seconds_elapsed'], axis = 1)

df_team = get_scoring_plays(filter_pbp_for_team(df, team))
df_team.loc[:,'team_score_after'] = df_team.apply(lambda row: row['posteam_score_post'] if row['posteam'] == team else row['defteam_score_post'], axis=1)
df_team.loc[:,'opp_score_after'] = df_team.apply(lambda row: row['posteam_score_post'] if row['posteam'] != team else row['defteam_score_post'], axis=1)

df_team.loc[:,'team_score_before'] = df_team.apply(lambda row: row['posteam_score'] if row['posteam'] == team else row['defteam_score'], axis=1)
df_team.loc[:,'opp_score_before'] = df_team.apply(lambda row: row['posteam_score'] if row['posteam'] != team else row['defteam_score'], axis=1)


def points_scored(row, which_team):
    if which_team == 'team':
        if row['play_id'] == 1:
            return 0
        return row['team_score_after'] - row['team_score_before']
    elif which_team == 'opp':
        if row['play_id'] == 1:
            return 0
        return row['opp_score_after'] - row['opp_score_before']
    else:
        print('Error')
        return 0

df_team.loc[:,'points_scored'] = df_team.apply(lambda row: points_scored(row, 'team'), axis=1)
df_team.loc[:,'points_allowed'] = df_team.apply(lambda row: points_scored(row, 'opp'), axis=1)

df_team.loc[:,'play_differential'] = df_team.apply(lambda row: row['points_scored'] - row['points_allowed'], axis=1)

# calculate current game score differential by subtracting opp_score_after from team_score_after
df_team.loc[:,'score_differential'] = df_team['team_score_after'] - df_team['opp_score_after']

# cumulative sum column for play_differential by season
df_team.loc[:,'cumulative_play_differential'] = df_team['play_differential'].cumsum()

# add column to indicate if cumulative_play_differential is positive or negative
df_team.loc[:,'cumulative_play_differential_sign'] = df_team['cumulative_play_differential'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')

# add column to name the opponent team
df_team.loc[:,'opponent'] = df_team.apply(lambda row: row['away_team'] if row['home_team'] == team else row['home_team'], axis=1)

# add column for team
# df_team.loc[:,'team'] = team

# st.dataframe(df_team[['game_id', 'qtr', 'desc', 'points_scored', 'game_seconds_elapsed', 
#                       'season_seconds_elapsed', 'points_allowed', 'play_differential', 
#                       'score_differential', 'cumulative_play_differential', 
#                       'cumulative_play_differential_sign']])

# st.bar_chart(data = df_team,
#               x='season_seconds_elapsed',
#               y='cumulative_play_differential'
# )

fig = go.Figure() # or any Plotly Express function e.g. px.bar(...)
fig.update_traces(connectgaps=True)
fig = px.line(df_team, x='season_seconds_elapsed', y='cumulative_play_differential', 
              title = f"{team} Cumulative Score Differential by Week for {number}",
            #   color = 'cumulative_play_differential_sign',
            #   color_discrete_map={
            #         'Positive': 'green',
            #         'Negative': 'red'
            #     },
              labels={
                    'season_seconds_elapsed': 'Week',
                    'cumulative_play_differential': 'Cumulative Score Differential'
                },
                template='plotly_white',
                height=600,
                width=1200,
                hover_data={
                    'week': True,
                    'season_seconds_elapsed': ':,',
                    'play_id': True,
                    'game_id': True,
                    'desc': True
                }
                )

# add vertical red lines every 3600 seconds

for i in range(1, max(df['week'])+1):
    fig.add_vline(x=i * 3600, line_width=0.5, line_dash='dash', line_color='grey')


tickvals = [i * 3600 for i in range(0, max(df['week'])+ 2)]
# add 0 as first entry in tickvals
# tickvals.insert(0, 0)

ticktext = [f'Wk {i} Start' for i in range(1, max(df['week'])+ 2)]

# print(tickvals)
# print(ticktext)

fig.data[0].line.color = 'green'

fig.update_xaxes(
    showgrid=False,
    tickmode = 'array',
    tick0 = 0,
    dtick = 3600,
    tickvals = tickvals,
    ticktext = ticktext,
    tickangle=45
)

fig.update_yaxes(
    showgrid=False
)
st.plotly_chart(fig, use_container_width=True)

cols_to_display = ['week', 'opponent', 'qtr', 'points_scored', 'points_allowed', 'desc']
st.dataframe(df_team[cols_to_display],
             hide_index=True)