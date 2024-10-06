from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime, timedelta
import pytz  # For time zone conversion


app = Flask(__name__)

# Define Power 5 teams with both school name and mascot
power_5_teams = [
    'Boston College Eagles', 'Clemson Tigers', 'Duke Blue Devils', 'Florida State Seminoles', 'Georgia Tech Yellow Jackets',
    'Louisville Cardinals', 'Miami Hurricanes', 'North Carolina Tar Heels', 'NC State Wolfpack', 'Syracuse Orange', 
    'Virginia Cavaliers', 'Virginia Tech Hokies', 'Wake Forest Demon Deacons',

    'Illinois Fighting Illini', 'Indiana Hoosiers', 'Iowa Hawkeyes', 'Maryland Terrapins', 'Michigan Wolverines', 
    'Michigan State Spartans', 'Minnesota Golden Gophers', 'Nebraska Cornhuskers', 'Northwestern Wildcats', 
    'Ohio State Buckeyes', 'Penn State Nittany Lions', 'Purdue Boilermakers', 'Rutgers Scarlet Knights', 'Wisconsin Badgers',

    'Baylor Bears', 'Iowa State Cyclones', 'Kansas Jayhawks', 'Kansas State Wildcats', 'Oklahoma Sooners', 
    'Oklahoma State Cowboys', 'TCU Horned Frogs', 'Texas Longhorns', 'Texas Tech Red Raiders', 'West Virginia Mountaineers',

    'Arizona Wildcats', 'Arizona State Sun Devils', 'California Golden Bears', 'Colorado Buffaloes', 'Oregon Ducks', 
    'Oregon State Beavers', 'Stanford Cardinal', 'UCLA Bruins', 'USC Trojans', 'Utah Utes', 
    'Washington Huskies', 'Washington State Cougars',

    'Alabama Crimson Tide', 'Arkansas Razorbacks', 'Auburn Tigers', 'Florida Gators', 'Georgia Bulldogs', 
    'Kentucky Wildcats', 'LSU Tigers', 'Mississippi State Bulldogs', 'Missouri Tigers', 
    'South Carolina Gamecocks', 'Tennessee Volunteers', 'Texas A&M Aggies', 'Vanderbilt Commodores'
]

# Simulating a basic leaderboard (to be stored in memory for now)
leaderboard = {}

# Function to calculate the current week based on the season start date
def get_current_week():
    season_start_date = datetime(2024, 8, 24)
    current_date = datetime.now()
    days_since_start = (current_date - season_start_date).days
    current_week = (days_since_start // 7)
    return max(1, current_week)

#Function to calculate time from UTC to Eastern time
def convert_to_eastern(utc_datetime_str):
    utc_time = datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%MZ")
    eastern = pytz.timezone('US/Eastern')
    utc_time = pytz.utc.localize(utc_time)
    eastern_time = utc_time.astimezone(eastern)
    return eastern_time.strftime('%Y-%m-%d %I:%M %p')




@app.route('/')
def index():
    # ESPN College Football scoreboard API URL
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    current_date = datetime.now()
    monday = current_date - timedelta(days=current_date.weekday())  # Start of the week (Monday)
    sunday = monday + timedelta(days=6)  # End of the week (Sunday)
    start_date = monday.strftime('%Y%m%d')
    end_date = sunday.strftime('%Y%m%d')

    # Request data for the current week's matchups
    params = {'dates': f'{start_date}-{end_date}'}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        matchups = []
        current_week = get_current_week()

        if data.get('events'):
            for event in data['events']:
                competitions = event.get('competitions', [])
                if not competitions:
                    continue
                
                # Extract the competitors and the game status
                competitors = competitions[0].get('competitors', [])
                if len(competitors) < 2:
                    continue
                
                team_1 = competitors[0]['team']['displayName']
                team_1_logo = competitors[0]['team'].get('logo')
                team_1_home_away = competitors[0]['homeAway']
                team_1_rank = competitors[0].get('curatedRank', {}).get('current', None)
                team_1_score = competitors[0].get('score', None)

                team_2 = competitors[1]['team']['displayName']
                team_2_logo = competitors[1]['team'].get('logo')
                team_2_home_away = competitors[1]['homeAway']
                team_2_rank = competitors[1].get('curatedRank', {}).get('current', None)
                team_2_score = competitors[1].get('score', None)

                # Convert scores to integers if they exist, otherwise default to None or 0
                team_1_score = int(team_1_score) if team_1_score is not None else 0
                team_2_score = int(team_2_score) if team_2_score is not None else 0

                # Extract the game status and start time
                status = competitions[0]['status']['type']['state']
                start_time = convert_to_eastern(competitions[0]['date'])

                # Extract time remaining and quarter for live games
                time_remaining = None
                quarter = None
                if status == 'in':
                    time_remaining = competitions[0]['status']['displayClock']
                    quarter = competitions[0]['status']['period']

                # Extract possession information for live games
                possession = None
                if status == 'in':
                    possession_team_id = competitions[0].get('situation', {}).get('possession', None)
                    if possession_team_id == competitors[0]['team']['id']:
                        possession = 'team_1'
                    elif possession_team_id == competitors[1]['team']['id']:
                        possession = 'team_2'

                # Determine the winner if the game has finished
                if status == "post":
                    if int(team_1_score) > int(team_2_score):
                        winner = team_1
                    else:
                        winner = team_2
                else:
                    winner = None

                # Add the rank before the team name if the team is ranked
                if team_1_rank and team_1_rank <= 25:
                    team_1 = f"<span class='rank'>{team_1_rank}</span> {team_1}"
                if team_2_rank and team_2_rank <= 25:
                    team_2 = f"<span class='rank'>{team_2_rank}</span> {team_2}"

                if team_1_home_away == 'home':
                    home_team = team_1
                    away_team = team_2
                    home_team_logo = team_1_logo
                    away_team_logo = team_2_logo
                else:
                    home_team = team_2
                    away_team = team_1
                    home_team_logo = team_2_logo
                    away_team_logo = team_1_logo

                odds = competitions[0].get('odds', [])
                spread = odds[0].get('details', 'N/A') if odds else 'N/A'

                # Filter for matchups with at least one Power 5 or Top 25 team
                if (team_1 in power_5_teams or team_2 in power_5_teams) or (team_1_rank and team_1_rank <= 25) or (team_2_rank and team_2_rank <= 25):
                    matchups.append({
                        'team_1': away_team,
                        'team_1_logo': away_team_logo,
                        'team_1_score': team_1_score,
                        'team_2': home_team,
                        'team_2_logo': home_team_logo,
                        'team_2_score': team_2_score,
                        'status': status,
                        'start_time': start_time,
                        'spread': spread,
                        'winner': winner,
                        'time_remaining': time_remaining,
                        'possession': possession,
                        'quarter': quarter
                    })

        return render_template('index.html', matchups=matchups, current_week=current_week)

    else:
        return f"Failed to retrieve data. Status code: {response.status_code}"


# This route will render a celebration page for Matt Faris
@app.route('/celebration')
def celebration():
    winner_name = "Matt Faris"
    correct_picks = ["SMU +6.5 ✅", "Minnesota +8.5 ✅"]
    week = 6

    # Standings data
    standings = [
        {'name': 'Faris', 'points': 55},
        {'name': 'Alex', 'points': 37},
        {'name': 'Mike', 'points': 31.5},
        {'name': 'Herm', 'points': 6.5},
        {'name': 'Fied', 'points': 0}
    ]

    # Results for all participants
    player_results = [
        {
            'name': 'Faris',
            'picks': ['SMU +6.5 ✅', 'Minnesota +8.5 ✅']
        },
        {
            'name': 'Mike',
            'picks': ['Syracuse +6.5 ✅', 'Stanford +8 ❌']
        },
        {
            'name': 'Alex',
            'picks': ['Arkansas +13.5 ✅', 'Duke +8.5 ❌']
        },
        {
            'name': 'Herm',
            'picks': ['SMU +6.5 ✅', 'Stanford +8 ❌']
        },
        {
            'name': 'Fied',
            'picks': ['Stanford +8 ❌', 'Duke +8.5 ❌']
        }
    ]
    
    return render_template('celebration.html', winner_name=winner_name, correct_picks=correct_picks, player_results=player_results, standings=standings, week=week)

# Route for picks and leaderboard
@app.route('/picks', methods=['GET', 'POST']) 
def picks():
    # ESPN College Football scoreboard API URL
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
    current_date = datetime.now()
    monday = current_date - timedelta(days=current_date.weekday())
    sunday = monday + timedelta(days=6)
    start_date = monday.strftime('%Y%m%d')
    end_date = sunday.strftime('%Y%m%d')

    # Request data for the current week's matchups
    params = {'dates': f'{start_date}-{end_date}'}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        matchups = []
        current_week = get_current_week()      

        if data.get('events'):
            for event in data['events']:
                competitions = event.get('competitions', [])
                if not competitions:
                    continue

                competitors = competitions[0].get('competitors', [])
                if len(competitors) < 2:
                    continue

                team_1 = competitors[0]['team']['displayName']
                team_2 = competitors[1]['team']['displayName']

                # Extract team rankings
                team_1_rank = competitors[0].get('curatedRank', {}).get('current', None)
                team_2_rank = competitors[1].get('curatedRank', {}).get('current', None)

                # Odds/spread details
                odds = competitions[0].get('odds', [])
                spread = odds[0].get('details', 'N/A') if odds else 'N/A'

                # Add only matchups where at least one team is in Power 5 or Top 25 ranked
                if (team_1 in power_5_teams or team_2 in power_5_teams) or (team_1_rank and team_1_rank <= 25) or (team_2_rank and team_2_rank <= 25):
                    matchups.append({
                        'team_1': team_1,
                        'team_2': team_2,
                        'spread': spread,
                        'game_id': event['id']
                    })

        if request.method == 'POST':
            player_name = request.form['player_name']
            pick_1 = request.form['pick_1']
            pick_2 = request.form['pick_2']

            if player_name not in leaderboard:
                leaderboard[player_name] = 0

            return redirect(url_for('picks'))

        return render_template('picks.html', matchups=matchups, current_week=current_week, leaderboard=leaderboard)

    else:
        return f"Failed to retrieve data. Status code: {response.status_code}"

if __name__ == '__main__':
    app.run(debug=True)
