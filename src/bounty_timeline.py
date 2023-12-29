import requests, json
import matplotlib.pyplot as plt

SESSION_TOKEN = 'RGAPI-153a2f54-6c10-46ae-82c7-bf1824323dac'

# From https://static.developer.riotgames.com/docs/lol/queues.json
DRAFT_QUEUE_TYPE = 400
SOLOQ_QUEUE_TYPE = 420
FLEX_QUEUE_TYPE = 440

def make_request(url: str):
    req = requests.get(url, headers={'X-Riot-Token': SESSION_TOKEN})
    req.raise_for_status()
    return req.json()

def get_account_puuid(gameName: str, tagLine: str):
    url = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}'
    return make_request(url)['puuid']

def get_match_history(puuid: str, queue=None, start=0, count=10):
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}'
    if queue:
        url = url + f'&queue={queue}'
    return make_request(url)

def get_timeline(match_id: str):
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline'
    return make_request(url)

id = get_account_puuid('Unknown Profile', 'euw1')
history = get_match_history(id, queue=DRAFT_QUEUE_TYPE, count=1)
timeline = get_timeline(history[0])

with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, indent=4)

frames = timeline['info']['frames']

BOUNTY_TIER = {
    7: 1000,
    6: 900,
    5: 800,
    4: 700,
    3: 600,
    2: 450,
    1: 300,
    0: 300,
    -1: 274,
    -2: 219,
    -3: 174,
    -4: 140,
    -5: 112,
    -6: 100
}

ASSIST_TIER = {
    -1: 137,
    -2: 110,
    -3: 88,
    -4: 70,
    -5: 56,
    -6: 50
}
def tier_to_bounty(tier):
    if tier > 7:
        return BOUNTY_TIER[7] + 100 * (tier - 7)
    if tier < -6:
        return BOUNTY_TIER[-6]

    return BOUNTY_TIER[tier]

def assist_tier_to_bounty(tier):
    if tier >= 0:
        return 150
    if tier < -6:
        return  ASSIST_TIER[-6]
    return ASSIST_TIER[tier]

# Bounties
# https://leagueoflegends.fandom.com/wiki/Kill

kill_tier = dict(map(lambda i: (i, 0), range(1, 11)))
extra_bounty = dict(map(lambda i: (i, 0), range(1, 11)))

kill_gold = dict(map(lambda i: (i, 0), range(1, 11)))

gold_timeline = []
team1_bounty_timeline = [[] for i in range(0, 6)]
team2_bounty_timeline = [[] for i in range(0, 6)]

for frame in frames:
    events = frame['events']

    for e in events:
        if e['type'] == 'CHAMPION_KILL':
            killer = e['killerId']        
            victim = e['victimId']

            if killer == 0:
                continue
            
            if kill_tier[killer] < 0:
                kill_tier[killer] = 0
            else:
                kill_tier[killer] += 1
            
            tier_offset = 0
            leftover_bounty = 0
            total_gold = 9999999
            while total_gold > e['bounty'] + e['shutdownBounty']:
                kill_gold = tier_to_bounty(kill_tier[victim] - tier_offset)
                total_gold = kill_gold + extra_bounty[victim]

                if total_gold > 1000:
                    leftover_bounty = total_gold - 1000
                    total_gold = 1000
                else:
                    leftover_bounty = 0

                tier_offset += 1

            tier_offset -= 1

            extra_bounty[victim] = leftover_bounty
            
            tier_offset = 0

            #print(e['bounty'], e['shutdownBounty'], total_gold, kill_tier[victim], killer, victim)

            if 'assistingParticipantIds' in e:
                assist_bounty = assist_tier_to_bounty(kill_tier[victim] - tier_offset) / len(e['assistingParticipantIds'])
                for assistant in e['assistingParticipantIds']:                    
                    if kill_tier[assistant] < 0:
                        kill_tier[assistant] += 1

            if kill_tier[victim] > 0:
                kill_tier[victim] = tier_offset
            else:
                kill_tier[victim] -= 1
        #elif e['type'] == 'BUILDING_KILL':


    participants = frame['participantFrames']

    def gather_total_gold(r):
        team_gold = 0
        for i in r:
            participant = participants[str(i)]
            #print(i, participant['totalGold'])
            team_gold += participant['totalGold']

        return team_gold
    
    team1_gold = gather_total_gold(range(1, 6))
    team2_gold = gather_total_gold(range(6, 11))

    team1_total_bounty = 0
    for i in range(1, 6):
        total_bounty = tier_to_bounty(kill_tier[i]) + extra_bounty[i] 
        team1_bounty_timeline[i].append(-(total_bounty + team1_total_bounty))
        team1_total_bounty += total_bounty

    team2_total_bounty = 0
    for i in range(6, 11):
        total_bounty = tier_to_bounty(kill_tier[i]) + extra_bounty[i]
        team2_bounty_timeline[i - 6].append(total_bounty + team2_total_bounty)
        team2_total_bounty += total_bounty

    gold_timeline.append(team1_gold - team2_gold)

    #print('-', team1_gold, team2_gold)

import numpy as np
import matplotlib.pyplot as plt
import math

plt.figure(figsize=(12,8))
plt.plot(gold_timeline, color='y', label='Total gold difference')
timeline_first = True
for timeline in team1_bounty_timeline:
    if timeline_first:
        timeline_first = False
        plt.plot(timeline, color='r', label='Team 1 available bounty')
    else:
        plt.plot(timeline, color='r')

timeline_first = True
for timeline in team2_bounty_timeline:
    if timeline_first:
        timeline_first = False
        plt.plot(timeline, color='b', label='Team 2 available bounty')
    else:
        plt.plot(timeline, color='b')
plt.hlines(y=300*5, xmin=0, xmax=len(frames), linewidth=1, color='tab:grey', linestyle='dashed')
plt.hlines(y=-300*5, xmin=0, xmax=len(frames), linewidth=1, color='tab:grey', linestyle='dashed')
plt.hlines(y=0, xmin=0, xmax=len(frames), linewidth=1, color='tab:grey', linestyle='dashed')
min_gold_tick = (math.floor(min(min(gold_timeline), min(team1_bounty_timeline[4]))/300) -1) * 300
max_gold_tick = (math.ceil(max(max(gold_timeline), max(team2_bounty_timeline[4]))/300) +1) * 300
plt.yticks(np.arange(min_gold_tick, max_gold_tick, 300))
plt.grid(axis = 'y')
plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
plt.legend()
plt.show()
