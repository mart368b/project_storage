import requests, json
import matplotlib.pyplot as plt
from cassiopeia import Summoner, Region, MatchHistory, Queue, Platform
from cassiopeia.core.match import *

id = Summoner(name='gravsens', region=Region.europe_west).puuid
history = MatchHistory(puuid=id, queue=Queue.normal_draft_fives, continent=Continent.europe, count=1)
timeline = Timeline(id=history[0].id, region=Region.europe_west, platform=Platform.europe_west)

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
# participant ids are 1 indexed
team1_bounty_timeline = [[] for _ in range(0, 6)]
team2_bounty_timeline = [[] for _ in range(0, 6)]

frame_count = len(timeline.frames)

def handle_kill(e: Event):
    killer = e.killer_id
    victim = e.victim_id

    if killer == 0:
        return
    
    # Increase the killers bounty
    if kill_tier[killer] < 0:
        kill_tier[killer] = 0
    else:
        kill_tier[killer] += 1
    
    # Do not include tiers gained during the fight
    # This manifests as a discrepentcy between the calculated bounty and the actual one
    tier_offset = 0
    leftover_bounty = 0
    
    delivered_bounty = e._data[EventData].bounty +  e._data[EventData].shutdownBounty

    if extra_bounty[victim] >= delivered_bounty:
        # Pay the bounty entirely with leftover bounty from last shutdown
        leftover_bounty = leftover_bounty - delivered_bounty
        tier_offset = kill_tier[victim]
    else:
        # tiers gained in a fight is only added after the fight is over
        # So we adjust to this by guessing how many kills was gained during the fight
        predicted_bounty = 9999999
        while predicted_bounty > delivered_bounty:
            kill_gold = tier_to_bounty(kill_tier[victim] - tier_offset)
            predicted_bounty = kill_gold + extra_bounty[victim]

            if predicted_bounty > 1000:
                leftover_bounty = predicted_bounty - 1000
                predicted_bounty = 1000
            else:
                leftover_bounty = 0

            tier_offset += 1

        tier_offset -= 1

    # Adjust the extra bounty for the victim
    extra_bounty[victim] = leftover_bounty

    # Increase the tier of assisting players with a negative kill_tier
    if hasattr(e, 'assisting_participants'):
        assist_bounty = assist_tier_to_bounty(kill_tier[victim] - tier_offset) / len(e.assisting_participants)
        for assistant in e.assisting_participants:
            if kill_tier[assistant] < 0:
                kill_tier[assistant] += 1

    # Reset the victims tier if 
    if kill_tier[victim] > 0:
        # Any kill tier earned during a fight will be keept for the next one
        kill_tier[victim] = tier_offset
    else:
        kill_tier[victim] -= 1

for frame in timeline.frames:
    frame: Frame = frame
    for e in frame.events:
        e: Event = e
        if e.type == 'CHAMPION_KILL':
            handle_kill(e)
    # Add to gold graph
    participants = frame.participant_frames

    def gather_total_gold(r):
        team_gold = 0
        for i in r:
            participant: ParticipantFrame = participants[i]
            team_gold += participant.gold_earned

        return team_gold
    
    team1_gold = gather_total_gold(range(1, 6))
    team2_gold = gather_total_gold(range(6, 11))
    gold_diff = team1_gold - team2_gold
    gold_timeline.append(gold_diff)

    # Add to team1 bounty graph
    team1_total_bounty = 0
    for i in range(1, 6):
        total_bounty = tier_to_bounty(kill_tier[i]) + extra_bounty[i]
        team1_bounty_timeline[i].append(-total_bounty)
        team1_total_bounty += total_bounty

    # Add to team2 bounty graph
    team2_total_bounty = 0
    for i in range(6, 11):
        total_bounty = tier_to_bounty(kill_tier[i]) + extra_bounty[i]
        team2_bounty_timeline[i - 6].append(total_bounty)
        team2_total_bounty += total_bounty

    #print('-', team1_gold, team2_gold)

import numpy as np
import matplotlib.pyplot as plt
import math
from itertools import permutations, chain
plt.figure(figsize=(12,8))

plt.plot(gold_timeline, color='y', label='Total gold difference')

def sum_timelines(*timelines):
    for i in range(0, len(timelines[0])):
        yield sum(map(lambda t: t[i], timelines))


timeline_first = True

k_alpha = [
    0,
    0.1,
    0.05,
    0.01,
    0.001,
    0.001,
]

bounty_settings = [
    {
        'range': list(range(1, 6)),
        'color': 'r',
        'timeline': team1_bounty_timeline
    },
    {
        'range': range(0,5),
        'color': 'b',
        'timeline': team2_bounty_timeline
    },
]

for setting in bounty_settings:
    k_range = setting['range']

    k1 = permutations(k_range, 1)
    k2 = permutations(k_range, 2)
    k3 = permutations(k_range, 3)
    k4 = permutations(k_range, 4)
    k5 = permutations(k_range, 5)

    combis = chain(k1, k2, k3, k4, k5)
    for k in combis:
        plt.plot(
            list(sum_timelines(*map(lambda i: setting['timeline'][i], k), gold_timeline)), 
            color=setting['color'],
            alpha=k_alpha[len(k)],
        )

plt.hlines(y=300*5, xmin=0, xmax=frame_count, linewidth=1, color='tab:grey', linestyle='dashed')
plt.hlines(y=-300*5, xmin=0, xmax=frame_count, linewidth=1, color='tab:grey', linestyle='dashed')
plt.hlines(y=0, xmin=0, xmax=frame_count, linewidth=1, color='tab:grey', linestyle='dashed')
min_gold_tick = (math.floor(min(min(gold_timeline), min(team1_bounty_timeline[4]))/300) -1) * 300
max_gold_tick = (math.ceil(max(max(gold_timeline), max(team2_bounty_timeline[4]))/300) +1) * 300
plt.yticks(np.arange(min_gold_tick, max_gold_tick, 300))
plt.grid(axis = 'y')
plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
plt.legend()
plt.show()
