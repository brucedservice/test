import argparse

from . import DEFAULT_ROSTER, DraftSimulator, format_rosters


def main() -> None:
    parser = argparse.ArgumentParser(description="Fantasy draft helper using local data")
    parser.add_argument("--data", default="ffdata_8.15_25.csv", help="CSV file with player data")
    parser.add_argument("--top", type=int, default=10, help="Number of top players to show")
    parser.add_argument("--mode", choices=["none", "full", "user"], default="none",
                        help="Draft mode: none, full simulation, or user drafts while others simulate")
    parser.add_argument("--teams", type=int, default=12, help="Number of teams in the league")
    parser.add_argument("--rounds", type=int, default=14, help="Number of draft rounds")
    parser.add_argument("--adp-weight", type=float, default=0.5, help="Weight for ADP in ranking")
    parser.add_argument("--proj-weight", type=float, default=0.5, help="Weight for projections in ranking")
    parser.add_argument("--roster", default=DEFAULT_ROSTER,
                        help="Roster configuration, e.g. 'QB=1,RB=2,WR=2,TE=1,FLEX=1,K=1,DST=1,BENCH=5'")
    args = parser.parse_args()

    sim = DraftSimulator(data=args.data, teams=args.teams, rounds=args.rounds,
                         roster=args.roster, adp_weight=args.adp_weight,
                         proj_weight=args.proj_weight)
    if args.mode in {"full", "user"}:
        sim.run(mode=args.mode)
        print(format_rosters(sim.summary()))
    else:
        print(sim.players.head(args.top)[["player", "team", "pos", "adp", "rank"]].to_string(index=False))


if __name__ == "__main__":
    main()
