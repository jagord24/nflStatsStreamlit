import streamlit as st
import pandas as pd

st.title('Team Leaders by Season')

# create range of seasons to select from

number = st.number_input('Enter a season', step=1, min_value=1999, max_value=2023)

# list of all NFL team abbreviations for use in selectbox

teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN',
            'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LAC', 'LAR', 'LV', 'MIA',
            'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB',
            'TEN', 'WAS']

# create selectbox for team selection

team = st.selectbox('Select a team', teams)

@st.cache_data
def get_pbp_data(year, team):
    url = url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.parquet"
    df = pd.read_parquet(url)
    df = df[(df.home_team == team) | (df.away_team == team)].reset_index(drop=True)
    return df

data_load_state = st.text('Loading data...')
data = get_pbp_data(number, team)
data_load_state.text('Loading data...done!')

# aggregate the sum of passing_yards by passer_player_name

passing_yards = data[data['posteam'] == team].groupby('passer_player_name').passing_yards.sum().reset_index()[['passer_player_name', 'passing_yards']]
st.write(passing_yards.sort_values(by='passing_yards', ascending=False))

passers = data[data.posteam == team].passer_player_name.unique()

# scoring_plays = data[data.sp == 1]
# scoring_plays = data[['desc']]

# if st.checkbox('Show raw data'):    
#     st.subheader(f'NYJ Scoring Plays for {number}')
#     st.checkbox("Use container width", value=False, key="use_container_width")
#     st.dataframe(scoring_plays, use_container_width=st.session_state.use_container_width)