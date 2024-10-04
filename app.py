from flask import Flask, render_template
import requests
from datetime import datetime, timedelta

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

@app.route('/')
def index():
    # ESPN College Football scoreboard API URL
    url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"

    # Calculate the date range for the current week (Monday to Sunday)
    current_date = datetime.now()
    monday = current_date - timedelta(days=current_date.weekday())  # Start of the week (Monday)
    sunday = monday + timedelta(days=6)  # End of the week (Sunday)

    # Generate formatted date strings
    start_date = monday.strftime('%Y%m%d')
    end_date = sunday.strftime('%Y%m%d')

    # Request data for the current week's matchups
    params = {'dates': f'{start_date}-{end_date}'}  # Use a date range from Monday to Sunday
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        matchups = []

        # Check if events exist for the week
        if data.get('events'):
            # Loop through the games (events)
            for event in data['events']:
                # Extract competitors
                competitions = event.get('competitions', [])
                if not competitions or len(competitions) == 0:
                    continue

                competitors = competitions[0].get('competitors', [])
                if len(competitors) < 2:
                    continue

                # Extract team names and home/away status
                team_1 = competitors[0]['team']['displayName']
                team_1_home_away = competitors[0]['homeAway']
                team_1_rank = competitors[0].get('curatedRank', {}).get('current', None)
                team_2 = competitors[1]['team']['displayName']
                team_2_home_away = competitors[1]['homeAway']
                team_2_rank = competitors[1].get('curatedRank', {}).get('current', None)

                # Determine which team is home
                if team_1_home_away == 'home':
                    home_team = team_1
                    away_team = team_2
                else:
                    home_team = team_2
                    away_team = team_1

                # Check if either team is in the Power 5 conference or Top 25
                if (team_1 in power_5_teams or team_2 in power_5_teams) or (team_1_rank and team_1_rank <= 25) or (team_2_rank and team_2_rank <= 25):
                    # Extract betting odds (spread) if available
                    odds = competitions[0].get('odds', [])
                    if odds:
                        spread = odds[0].get('details', 'N/A')  # Get the spread details
                    else:
                        spread = 'N/A'

                    # Add the matchup to the list
                    matchups.append(f"{away_team} at {home_team} - Spread: {spread}")

        return render_template('index.html', matchups=matchups)
    else:
        return f"Failed to retrieve data. Status code: {response.status_code}"

if __name__ == '__main__':
    app.run(debug=True)
