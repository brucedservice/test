import argparse
from collections import defaultdict
import pandas as pd


ROSTER_LIMITS = {
    'QB': 1,
    'RB': 2,
    'WR': 2,
    'TE': 1,
    'FLEX': 1,
    'K': 1,
    'DST': 1,
    'BENCH': 5,
}


def load_players(path: str) -> pd.DataFrame:
    """Load player data from CSV, add placeholders and compute a composite rank."""
    df = pd.read_csv(path)
    df = df.rename(columns={
        'Player': 'player',
        'Team': 'team',
        'Position': 'pos',
        'ConsensusProj': 'proj',
        'Sleeper': 'adp',
    })
    placeholders = []
    for i in range(12):
        placeholders.append({'player': f'K{i+1}', 'team': 'FA', 'pos': 'K', 'proj': 0, 'adp': 300 + i})
        placeholders.append({'player': f'DST{i+1}', 'team': 'FA', 'pos': 'DST', 'proj': 0, 'adp': 320 + i})
    df = pd.concat([df, pd.DataFrame(placeholders)], ignore_index=True)
    df['adp_rank'] = df['adp'].rank(method='min')
    df['proj_rank'] = df['proj'].rank(ascending=False, method='min')
    df['rank'] = (df['adp_rank'] + df['proj_rank']) / 2
    cols = ['player', 'team', 'pos', 'proj', 'adp', 'rank']
    return df[cols].sort_values('rank').reset_index(drop=True)


def slot_for(pos: str, counts: dict[str, int]) -> str | None:
    """Return roster slot name where a player of `pos` can be placed."""
    if counts.get(pos, 0) < ROSTER_LIMITS[pos]:
        return pos
    if pos in {'RB', 'WR', 'TE'} and counts.get('FLEX', 0) < ROSTER_LIMITS['FLEX']:
        return 'FLEX'
    if counts.get('BENCH', 0) < ROSTER_LIMITS['BENCH']:
        return 'BENCH'
    return None


def auto_pick(available: pd.DataFrame, counts: dict[str, int]) -> tuple[pd.Series, int, str] | None:
    for idx, player in available.iterrows():
        slot = slot_for(player['pos'], counts)
        if slot:
            return player, idx, slot
    return None


def user_pick(available: pd.DataFrame, counts: dict[str, int], top: int = 10) -> tuple[pd.Series, int, str]:
    while True:
        print(available.head(top)[['player', 'team', 'pos', 'adp', 'rank']].to_string(index=False))
        choice = input('Your pick: ').strip().lower()
        match = available[available['player'].str.lower() == choice]
        if match.empty:
            print('Player not found. Try again.')
            continue
        player = match.iloc[0]
        slot = slot_for(player['pos'], counts)
        if not slot:
            print('No roster slot available for that player. Choose another.')
            continue
        idx = match.index[0]
        return player, idx, slot


def simulate_draft(players: pd.DataFrame, teams: int, rounds: int, mode: str) -> dict[int, list[str]]:
    """Run a snake draft with optional user interaction."""
    available = players.copy()
    rosters: dict[int, list[str]] = defaultdict(list)
    counts = [{k: 0 for k in ROSTER_LIMITS} for _ in range(teams)]
    for rnd in range(rounds):
        order = range(teams) if rnd % 2 == 0 else range(teams - 1, -1, -1)
        for team in order:
            pick_info = None
            if mode == 'user' and team == 0:
                pick_info = user_pick(available, counts[team])
            else:
                pick_info = auto_pick(available, counts[team])
            if not pick_info:
                continue
            player, idx, slot = pick_info
            counts[team][slot] += 1
            rosters[team].append(player['player'])
            available = available.drop(index=idx).reset_index(drop=True)
    return rosters


def main() -> None:
    parser = argparse.ArgumentParser(description='Fantasy draft helper using local data')
    parser.add_argument('--data', default='ffdata_8.15_25.csv', help='CSV file with player data')
    parser.add_argument('--top', type=int, default=10, help='Number of top players to show')
    parser.add_argument('--mode', choices=['none', 'full', 'user'], default='none',
                        help='Draft mode: none, full simulation, or user drafts while others simulate')
    parser.add_argument('--teams', type=int, choices=[10, 12], default=12,
                        help='Number of teams (10 or 12)')
    parser.add_argument('--rounds', type=int, default=14, help='Number of draft rounds')
    args = parser.parse_args()

    players = load_players(args.data)
    if args.mode == 'full' or args.mode == 'user':
        rosters = simulate_draft(players, teams=args.teams, rounds=args.rounds, mode=args.mode)
        for team in range(args.teams):
            picks = ', '.join(rosters.get(team, []))
            print(f'Team {team + 1}: {picks}')
    else:
        print(players.head(args.top).to_string(index=False))


if __name__ == '__main__':
    main()

