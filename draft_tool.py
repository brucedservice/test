import argparse
from collections import defaultdict
import pandas as pd


DEFAULT_ROSTER = "QB=1,RB=2,WR=2,TE=1,FLEX=1,K=1,DST=1,BENCH=5"


def parse_roster(spec: str) -> dict[str, int]:
    return {k: int(v) for k, v in (item.split('=') for item in spec.split(','))}


def load_players(path: str, teams: int, roster_limits: dict[str, int],
                 adp_w: float, proj_w: float) -> pd.DataFrame:
    """Load player data from CSV, add placeholders and compute a weighted rank."""
    df = pd.read_csv(path)
    df = df.rename(columns={
        'Player': 'player',
        'Team': 'team',
        'Position': 'pos',
        'ConsensusProj': 'proj',
        'Sleeper': 'adp',
    })
    placeholders: list[dict[str, object]] = []
    placeholder_count = teams * (1 + roster_limits.get('BENCH', 0))
    for i in range(placeholder_count):
        if roster_limits.get('K', 0) > 0:
            placeholders.append({'player': f'K{i+1}', 'team': 'FA', 'pos': 'K',
                                'proj': 0, 'adp': 300 + i})
        if roster_limits.get('DST', 0) > 0:
            placeholders.append({'player': f'DST{i+1}', 'team': 'FA', 'pos': 'DST',
                                'proj': 0, 'adp': 400 + i})
    if placeholders:
        df = pd.concat([df, pd.DataFrame(placeholders)], ignore_index=True)
    df['adp_rank'] = df['adp'].rank(method='min')
    df['proj_rank'] = df['proj'].rank(ascending=False, method='min')
    total = adp_w + proj_w
    adp_w /= total
    proj_w /= total
    df['rank'] = df['adp_rank'] * adp_w + df['proj_rank'] * proj_w
    cols = ['player', 'team', 'pos', 'proj', 'adp', 'rank']
    return df[cols].sort_values('rank').reset_index(drop=True)


def slot_for(pos: str, counts: dict[str, int], roster_limits: dict[str, int]) -> str | None:
    if counts.get(pos, 0) < roster_limits.get(pos, 0):
        return pos
    if pos in {'RB', 'WR', 'TE'} and counts.get('FLEX', 0) < roster_limits.get('FLEX', 0):
        return 'FLEX'
    if counts.get('BENCH', 0) < roster_limits.get('BENCH', 0):
        return 'BENCH'
    return None


def auto_pick(available: pd.DataFrame, counts: dict[str, int],
              roster_limits: dict[str, int]) -> tuple[pd.Series, int, str] | None:
    for idx, player in available.iterrows():
        slot = slot_for(player['pos'], counts, roster_limits)
        if slot:
            return player, idx, slot
    return None


def user_pick(available: pd.DataFrame, counts: dict[str, int],
              roster_limits: dict[str, int], top: int = 10) -> tuple[pd.Series, int, str]:
    while True:
        print(available.head(top)[['player', 'team', 'pos', 'adp', 'rank']].to_string(index=False))
        choice = input('Your pick: ').strip().lower()
        match = available[available['player'].str.lower() == choice]
        if match.empty:
            print('Player not found. Try again.')
            continue
        player = match.iloc[0]
        slot = slot_for(player['pos'], counts, roster_limits)
        if not slot:
            print('No roster slot available for that player. Choose another.')
            continue
        idx = match.index[0]
        return player, idx, slot


def simulate_draft(players: pd.DataFrame, teams: int, rounds: int, mode: str,
                   roster_limits: dict[str, int]) -> dict[int, list[tuple[str, str]]]:
    available = players.copy()
    rosters: dict[int, list[tuple[str, str]]] = defaultdict(list)
    counts = [{k: 0 for k in roster_limits} for _ in range(teams)]
    for rnd in range(rounds):
        order = range(teams) if rnd % 2 == 0 else range(teams - 1, -1, -1)
        for team in order:
            pick_info = None
            if mode == 'user' and team == 0:
                pick_info = user_pick(available, counts[team], roster_limits)
            else:
                pick_info = auto_pick(available, counts[team], roster_limits)
            if not pick_info:
                continue
            player, idx, slot = pick_info
            counts[team][slot] += 1
            rosters[team].append((slot, player['player']))
            available = available.drop(index=idx).reset_index(drop=True)
    return rosters


def print_rosters(rosters: dict[int, list[tuple[str, str]]], teams: int,
                  roster_limits: dict[str, int]) -> None:
    for team in range(teams):
        print(f'Team {team + 1}:')
        grouped: dict[str, list[str]] = defaultdict(list)
        for slot, name in rosters.get(team, []):
            grouped[slot].append(name)
        for slot in roster_limits:
            if grouped.get(slot):
                print(f'  {slot}: {", ".join(grouped[slot])}')
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description='Fantasy draft helper using local data')
    parser.add_argument('--data', default='ffdata_8.15_25.csv', help='CSV file with player data')
    parser.add_argument('--top', type=int, default=10, help='Number of top players to show')
    parser.add_argument('--mode', choices=['none', 'full', 'user'], default='none',
                        help='Draft mode: none, full simulation, or user drafts while others simulate')
    parser.add_argument('--teams', type=int, default=12, help='Number of teams in the league')
    parser.add_argument('--rounds', type=int, default=14, help='Number of draft rounds')
    parser.add_argument('--adp-weight', type=float, default=0.5, help='Weight for ADP in ranking')
    parser.add_argument('--proj-weight', type=float, default=0.5, help='Weight for projections in ranking')
    parser.add_argument('--roster', default=DEFAULT_ROSTER,
                        help='Roster configuration, e.g. "QB=1,RB=2,WR=2,TE=1,FLEX=1,K=1,DST=1,BENCH=5"')
    args = parser.parse_args()

    roster_limits = parse_roster(args.roster)
    players = load_players(args.data, teams=args.teams, roster_limits=roster_limits,
                           adp_w=args.adp_weight, proj_w=args.proj_weight)
    if args.mode in {'full', 'user'}:
        rosters = simulate_draft(players, teams=args.teams, rounds=args.rounds,
                                 mode=args.mode, roster_limits=roster_limits)
        print_rosters(rosters, args.teams, roster_limits)
    else:
        print(players.head(args.top)[['player', 'team', 'pos', 'adp', 'rank']].to_string(index=False))


if __name__ == '__main__':
    main()

