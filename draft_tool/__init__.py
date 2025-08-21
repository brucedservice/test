from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Tuple

import pandas as pd

DEFAULT_ROSTER = "QB=1,RB=2,WR=2,TE=1,FLEX=1,K=1,DST=1,BENCH=5"


def parse_roster(spec: str) -> Dict[str, int]:
    """Parse a roster specification like "QB=1,RB=2" into a dict."""
    return {k: int(v) for k, v in (item.split('=') for item in spec.split(','))}


def load_players(path: str, teams: int, roster_limits: Dict[str, int],
                 adp_w: float, proj_w: float) -> pd.DataFrame:
    """Load player data from CSV, add placeholders and compute a weighted rank."""
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Player": "player",
        "Team": "team",
        "Position": "pos",
        "ConsensusProj": "proj",
        "Sleeper": "adp",
    })
    placeholders: List[Dict[str, object]] = []
    placeholder_count = teams * (1 + roster_limits.get("BENCH", 0))
    for i in range(placeholder_count):
        if roster_limits.get("K", 0) > 0:
            placeholders.append({"player": f"K{i+1}", "team": "FA", "pos": "K",
                                "proj": 0, "adp": 300 + i})
        if roster_limits.get("DST", 0) > 0:
            placeholders.append({"player": f"DST{i+1}", "team": "FA", "pos": "DST",
                                "proj": 0, "adp": 400 + i})
    if placeholders:
        df = pd.concat([df, pd.DataFrame(placeholders)], ignore_index=True)
    df["adp_rank"] = df["adp"].rank(method="min")
    df["proj_rank"] = df["proj"].rank(ascending=False, method="min")
    total = adp_w + proj_w
    adp_w /= total
    proj_w /= total
    df["rank"] = df["adp_rank"] * adp_w + df["proj_rank"] * proj_w
    cols = ["player", "team", "pos", "proj", "adp", "rank"]
    return df[cols].sort_values("rank").reset_index(drop=True)


def slot_for(pos: str, counts: Dict[str, int], roster_limits: Dict[str, int]) -> str | None:
    if counts.get(pos, 0) < roster_limits.get(pos, 0):
        return pos
    if pos in {"RB", "WR", "TE"} and counts.get("FLEX", 0) < roster_limits.get("FLEX", 0):
        return "FLEX"
    if counts.get("BENCH", 0) < roster_limits.get("BENCH", 0):
        return "BENCH"
    return None


def auto_pick(available: pd.DataFrame, counts: Dict[str, int],
              roster_limits: Dict[str, int]) -> Tuple[pd.Series, int, str] | None:
    for idx, player in available.iterrows():
        slot = slot_for(player["pos"], counts, roster_limits)
        if slot:
            return player, idx, slot
    return None


def default_user_pick(available: pd.DataFrame, counts: Dict[str, int],
                      roster_limits: Dict[str, int], top: int = 10) -> Tuple[pd.Series, int, str]:
    while True:
        print(available.head(top)[["player", "team", "pos", "adp", "rank"]].to_string(index=False))
        choice = input("Your pick: ").strip().lower()
        match = available[available["player"].str.lower() == choice]
        if match.empty:
            print("Player not found. Try again.")
            continue
        player = match.iloc[0]
        slot = slot_for(player["pos"], counts, roster_limits)
        if not slot:
            print("No roster slot available for that player. Choose another.")
            continue
        idx = match.index[0]
        return player, idx, slot


def simulate_draft(players: pd.DataFrame, teams: int, rounds: int, roster_limits: Dict[str, int],
                   mode: str = "full",
                   user_pick_fn: Callable[[pd.DataFrame, Dict[str, int], Dict[str, int]],
                                          Tuple[pd.Series, int, str]] | None = None) -> Dict[int, List[Tuple[str, str]]]:
    available = players.copy()
    rosters: Dict[int, List[Tuple[str, str]]] = defaultdict(list)
    counts = [{k: 0 for k in roster_limits} for _ in range(teams)]
    for rnd in range(rounds):
        order = range(teams) if rnd % 2 == 0 else range(teams - 1, -1, -1)
        for team in order:
            pick_info = None
            if mode == "user" and team == 0:
                picker = user_pick_fn or default_user_pick
                pick_info = picker(available, counts[team], roster_limits)
            else:
                pick_info = auto_pick(available, counts[team], roster_limits)
            if not pick_info:
                continue
            player, idx, slot = pick_info
            counts[team][slot] += 1
            rosters[team].append((slot, player["player"]))
            available = available.drop(index=idx).reset_index(drop=True)
    return rosters


def summarize_rosters(rosters: Dict[int, List[Tuple[str, str]]], teams: int,
                      roster_limits: Dict[str, int]) -> Dict[int, Dict[str, List[str]]]:
    summaries: Dict[int, Dict[str, List[str]]] = {}
    for team in range(teams):
        grouped: Dict[str, List[str]] = defaultdict(list)
        for slot, name in rosters.get(team, []):
            grouped[slot].append(name)
        summaries[team + 1] = {slot: grouped[slot] for slot in roster_limits if grouped.get(slot)}
    return summaries


def format_rosters(summaries: Dict[int, Dict[str, List[str]]]) -> str:
    lines: List[str] = []
    for team, slots in summaries.items():
        lines.append(f"Team {team}:")
        for slot, names in slots.items():
            lines.append(f"  {slot}: {', '.join(names)}")
        lines.append("")
    return "\n".join(lines)


class DraftSimulator:
    """High-level helper to run fantasy drafts programmatically."""

    def __init__(self, data: str = "ffdata_8.15_25.csv", teams: int = 12,
                 rounds: int = 14, roster: str = DEFAULT_ROSTER,
                 adp_weight: float = 0.5, proj_weight: float = 0.5) -> None:
        self.roster_limits = parse_roster(roster)
        self.teams = teams
        self.rounds = rounds
        self.players = load_players(data, teams, self.roster_limits,
                                    adp_weight, proj_weight)
        self.rosters: Dict[int, List[Tuple[str, str]]] | None = None

    def run(self, mode: str = "full",
            user_pick_fn: Callable[[pd.DataFrame, Dict[str, int], Dict[str, int]],
                                   Tuple[pd.Series, int, str]] | None = None) -> Dict[int, List[Tuple[str, str]]]:
        """Run the draft and return rosters."""
        self.rosters = simulate_draft(self.players.copy(), teams=self.teams,
                                      rounds=self.rounds, roster_limits=self.roster_limits,
                                      mode=mode, user_pick_fn=user_pick_fn)
        return self.rosters

    def summary(self) -> Dict[int, Dict[str, List[str]]]:
        """Return the roster summaries for each team."""
        if self.rosters is None:
            return {}
        return summarize_rosters(self.rosters, self.teams, self.roster_limits)
