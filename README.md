# Fantasy Draft Helper

Utilities for running a fantasy football draft from Python or the command line.

## Getting Started

The `draft_tool` package reads player projection data from `ffdata_8.15_25.csv`.
Player **ADP** comes from the `Sleeper` column and a custom **rank** blends
ADP and projection-based ordering.  The balance can be adjusted with
`--adp-weight` and `--proj-weight`.

```bash
./setup.sh                     # install required packages
python -m draft_tool --help    # show available options
```

To view the best available players:

```bash
python -m draft_tool --top 15
```

Example with custom ranking weights:

```bash
python -m draft_tool --top 15 --adp-weight 0.7 --proj-weight 0.3
```

To load a different dataset, supply the CSV path with `--data`.

### Draft Simulation Modes

The tool supports three modes controlled by `--mode`:

* `none` – list top players only (default)
* `full` – simulate an entire draft
* `user` – you draft for Team 1 while other teams auto-pick

Drafts may include any number of teams and consist of 14 rounds by default.
Roster slots are configurable with `--roster`; the default is
`QB=1,RB=2,WR=2,TE=1,FLEX=1,K=1,DST=1,BENCH=5`.

Example full simulation:

```bash
python -m draft_tool --mode full --teams 12
```

Example user-assisted draft (you will be prompted for picks):

```bash
python -m draft_tool --mode user --teams 10
```

At the end of a simulation the script prints each team's roster grouped by
position.

### Using as an API

The core functionality is available programmatically via `DraftSimulator`:

```python
from draft_tool import DraftSimulator, format_rosters

sim = DraftSimulator(teams=3, rounds=2)
sim.run(mode="full")
print(format_rosters(sim.summary()))
```
