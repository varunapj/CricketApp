# Team Splitter

This repository contains a small script to split players into two balanced teams based on three factors (in order of priority):

- Impact Player (Y/N)
- League Player (Yes/No)
- Role (Batsman / Allrounder / Bowler / Batsman/Wicketkeeper)

Usage:

Run the splitter on the provided `Players_Inventory.tsv`:

```bash
python3 split_teams.py Players_Inventory.tsv --write-output --out-prefix players_teams
```

Options:
- `--impact-weight`: numeric weight for impact players (default 100)
- `--league-weight`: numeric weight for league players (default 10)
- `--write-output`: write two TSV files (`<prefix>_A.tsv` and `<prefix>_B.tsv`)
- `--out-prefix`: prefix for output files (default `teams`)

Output:
- Two TSV files with team assignments and scores.

- Two output files (one per team) containing only player names, one per line when `--write-output` is used.

Adjust weights to tune how strongly Impact and League affect balancing.
