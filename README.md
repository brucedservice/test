# Fantasy Draft Helper

Utilities for running a fantasy football draft from the command line.

## Getting Started

The `draft_tool.py` script reads player projection data from `ffdata_8.15_25.csv`.
Player **ADP** comes from the `Sleeper` column and a custom **rank** is
computed by averaging ADP with projection-based rankings.

```bash
pip install pandas  # if running outside this environment
python draft_tool.py --help      # show available options
```

To view the best available players:

```bash
python draft_tool.py --top 15
```

To load a different dataset, supply the CSV path with `--data`.

### Draft Simulation Modes

The tool supports three modes controlled by `--mode`:

* `none` – list top players only (default)
* `full` – simulate an entire draft
* `user` – you draft for Team 1 while other teams auto-pick

Drafts can be run with 10 or 12 teams and consist of 14 rounds. Each team
has roster slots: QB, RB, RB, WR, WR, TE, FLEX (RB/WR/TE), K, DST and five
bench spots.

Example full simulation:

```bash
python draft_tool.py --mode full --teams 12
```

Example user-assisted draft (you will be prompted for picks):

```bash
python draft_tool.py --mode user --teams 10
```

At the end of a simulation the script prints each team's roster.
