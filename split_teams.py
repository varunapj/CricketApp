#!/usr/bin/env python3
import csv
import argparse
from collections import defaultdict
import re
from pathlib import Path


def normalize_role(raw):
    if not raw:
        return 'Unknown'
    r = raw.strip().lower()
    if 'all' in r and 'round' in r:
        return 'Allrounder'
    if 'batsman' in r and 'wicket' in r:
        return 'Batsman/Wicketkeeper'
    if 'batsman' in r:
        return 'Batsman'
    if 'bowler' in r:
        return 'Bowler'
    return raw.strip()


def parse_players(path):
    """Parse players from a TSV/CSV or Excel file.

    Accepts paths to files with extensions: .tsv, .csv, .xlsx, .xls
    Returns list of player dicts with keys: name, dob, role, league, impact
    """
    players = []
    p = Path(path)
    suffix = p.suffix.lower()

    # Excel handling via pandas if available
    if suffix in ('.xlsx', '.xls'):
        try:
            import pandas as _pd
        except Exception:
            raise RuntimeError('Reading Excel requires pandas. Please install with `pip install pandas openpyxl`')
        df = _pd.read_excel(path)
        # normalize dataframe columns (strip)
        df.columns = [str(c).strip() for c in df.columns]
        for _, row in df.iterrows():
            player = {str(k).strip(): (str(v).strip() if not (_pd.isna(v)) else '') for k, v in row.items()}
            name = player.get('Player Name') or player.get('Player') or ''
            dob = player.get('Date of Birth', '')
            role = normalize_role(player.get('Role', ''))
            league = player.get('League Player', '')
            impact = player.get('Impact Player', '')
            players.append({
                'name': name,
                'dob': dob,
                'role': role,
                'league': league,
                'impact': impact,
            })
        return players

    # fallback: treat as text TSV/CSV
    delim = '\t' if suffix == '.tsv' or suffix == '' else ','
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delim)
        for row in reader:
            # normalize keys by stripping
            player = {k.strip(): (v.strip() if v is not None else '') for k, v in row.items()}
            name = player.get('Player Name') or player.get('Player') or ''
            dob = player.get('Date of Birth', '')
            role = normalize_role(player.get('Role', ''))
            league = player.get('League Player', '')
            impact = player.get('Impact Player', '')
            players.append({
                'name': name,
                'dob': dob,
                'role': role,
                'league': league,
                'impact': impact,
            })
    return players


def normalize_name(n):
    if not n:
        return ''
    # keep alphanumerics and spaces, collapse whitespace, lowercase
    s = re.sub(r'[^A-Za-z0-9\s]', '', n)
    parts = s.strip().lower().split()
    return ' '.join(parts)


def parse_availability(path):
    """Parse availability names from a text file (one-per-line) or from Excel/CSV.

    If Excel is provided, attempts to read a column named 'Player Name' or uses the
    first column.
    """
    from pathlib import Path
    names = []
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix in ('.xlsx', '.xls'):
        try:
            import pandas as _pd
        except Exception:
            raise RuntimeError('Reading Excel requires pandas. Please install with `pip install pandas openpyxl`')
        df = _pd.read_excel(path)
        if 'Player Name' in df.columns:
            col = df['Player Name']
        else:
            # take first column
            col = df.iloc[:, 0]
        for v in col:
            if _pd.isna(v):
                continue
            n = str(v).strip()
            if n:
                names.append(n)
        return names

    delim = '\t' if suffix == '.tsv' or suffix == '' else ','
    if delim == ',' and suffix in ('.csv',):
        # CSV file read
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                names.append(row[0].strip())
        return names

    # default: plain text one-name-per-line
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            n = line.strip()
            if not n:
                continue
            names.append(n)
    return names


def crosscheck_availability(master_players, availability_names):
    # build lookup by normalized name
    lookup = defaultdict(list)
    for p in master_players:
        lookup[normalize_name(p['name'])].append(p)

    matched = []
    unmatched = []
    ambiguous = []
    seen = set()

    for raw in availability_names:
        key = normalize_name(raw)
        if key in lookup and len(lookup[key]) == 1:
            player = lookup[key][0]
            if player['name'] not in seen:
                matched.append(player)
                seen.add(player['name'])
            continue

        # try prefix match: find master names where normalized startswith key or vice versa
        candidates = []
        for k, plist in lookup.items():
            if k.startswith(key) or key.startswith(k):
                candidates.extend(plist)

        # dedupe candidates by name
        uniq = {p['name']: p for p in candidates}.values()
        uniq = list(uniq)
        if len(uniq) == 1:
            p = uniq[0]
            if p['name'] not in seen:
                matched.append(p); seen.add(p['name'])
        elif len(uniq) > 1:
            ambiguous.append((raw, [p['name'] for p in uniq]))
        else:
            unmatched.append(raw)

    return matched, unmatched, ambiguous


def score_player(p, impact_w, league_w, role_map):
    s = 0
    if p.get('impact', '').strip().upper() in ('Y', 'YES', 'TRUE'):
        s += impact_w
    if p.get('league', '').strip().upper() in ('Y', 'YES', 'TRUE'):
        s += league_w
    s += role_map.get(p.get('role'), 0)
    return s


def split_teams(players, impact_w=100, league_w=10, role_map=None, ensure_role_parity=False):
    if role_map is None:
        role_map = {
            'Allrounder': 30,
            'Batsman': 20,
            'Bowler': 15,
            'Batsman/Wicketkeeper': 18,
            'Unknown': 5,
        }

    # attach score
    for p in players:
        p['score'] = score_player(p, impact_w, league_w, role_map)

    # sort by score descending so we place highest-impact players first
    players_sorted = sorted(players, key=lambda x: x['score'], reverse=True)

    teamA = []
    teamB = []
    totals = {'A': 0, 'B': 0}
    role_counts = {'A': defaultdict(int), 'B': defaultdict(int)}

    # if parity requested, compute desired per-role counts
    desired = {}
    if ensure_role_parity:
        totals_by_role = defaultdict(int)
        for p in players_sorted:
            totals_by_role[p['role']] += 1
        for role, cnt in totals_by_role.items():
            desired[role] = (cnt // 2, cnt - (cnt // 2))  # (min, max) per team

    for p in players_sorted:
        role = p['role']

        # helper: check if assigning to team_key would violate size constraint
        def size_would_violate(team_key):
            sizeA = len(teamA) + (1 if team_key == 'A' else 0)
            sizeB = len(teamB) + (1 if team_key == 'B' else 0)
            return abs(sizeA - sizeB) > 1

        # If role parity enforced, prefer assigning to the team that currently has fewer of this role
        assigned = False
        if ensure_role_parity and role in desired:
            # desired split is (min,max) but teams can take either; compute deficits
            # we try to bring both teams toward floor(cnt/2) and ceil(cnt/2)
            needA = desired[role][0] - role_counts['A'][role]
            needB = desired[role][0] - role_counts['B'][role]

            # If both need more (rare), choose the team with lower total score to keep balance
            if needA > 0 and needB > 0:
                prefer = 'A' if totals['A'] <= totals['B'] else 'B'
                if not size_would_violate(prefer):
                    team = prefer
                else:
                    team = 'B' if prefer == 'A' else 'A'
                if team == 'A':
                    teamA.append(p); totals['A'] += p['score']; role_counts['A'][role] += 1
                else:
                    teamB.append(p); totals['B'] += p['score']; role_counts['B'][role] += 1
                assigned = True
            else:
                # assign to the team that still needs this role (deficit > 0), prefer that team
                if needA > needB and not size_would_violate('A'):
                    teamA.append(p); totals['A'] += p['score']; role_counts['A'][role] += 1; assigned = True
                elif needB > needA and not size_would_violate('B'):
                    teamB.append(p); totals['B'] += p['score']; role_counts['B'][role] += 1; assigned = True

        # fallback: assign to team with lower total score while keeping sizes balanced
        if not assigned:
            prefer = 'A' if totals['A'] <= totals['B'] else 'B'
            other = 'B' if prefer == 'A' else 'A'

            # try preferred if it doesn't make size diff >1
            if not size_would_violate(prefer):
                if prefer == 'A':
                    teamA.append(p); totals['A'] += p['score']; role_counts['A'][role] += 1
                else:
                    teamB.append(p); totals['B'] += p['score']; role_counts['B'][role] += 1
            elif not size_would_violate(other):
                if other == 'A':
                    teamA.append(p); totals['A'] += p['score']; role_counts['A'][role] += 1
                else:
                    teamB.append(p); totals['B'] += p['score']; role_counts['B'][role] += 1
            else:
                # both would violate (shouldn't happen), assign to lower total anyway
                if totals['A'] <= totals['B']:
                    teamA.append(p); totals['A'] += p['score']; role_counts['A'][role] += 1
                else:
                    teamB.append(p); totals['B'] += p['score']; role_counts['B'][role] += 1

    return teamA, teamB, totals


def write_team(path, team):
    # write only player names, one per line
    with open(path, 'w', newline='') as f:
        for p in team:
            f.write(f"{p['name']}\n")


def main():
    parser = argparse.ArgumentParser(description='Split players into two balanced teams')
    parser.add_argument('input', help='Path to players TSV file')
    parser.add_argument('--impact-weight', type=int, default=100)
    parser.add_argument('--league-weight', type=int, default=10)
    parser.add_argument('--role-parity', action='store_true', dest='role_parity',
                        help='Try to enforce equal per-role counts between teams')
    parser.add_argument('--availability', help='Path to a file listing available player names (one per line)')
    parser.add_argument('--master', help='Path to master players TSV (default: provided input file)', default=None)
    parser.add_argument('--write-output', action='store_true')
    parser.add_argument('--out-prefix', default='teams')
    args = parser.parse_args()

    # use provided master if given, otherwise use the input TSV as master
    master_path = args.master or args.input
    master_players = parse_players(master_path)

    if args.availability:
        avail_names = parse_availability(args.availability)
        matched, unmatched, ambiguous = crosscheck_availability(master_players, avail_names)
        if unmatched:
            print(f"Warning: {len(unmatched)} availability names not found in master:")
            for n in unmatched:
                print(f" - {n}")
        if ambiguous:
            print(f"Warning: {len(ambiguous)} ambiguous availability names (multiple matches):")
            for raw, opts in ambiguous:
                print(f" - {raw} -> possible matches: {', '.join(opts)}")
        players = matched
    else:
        players = master_players

    teamA, teamB, totals = split_teams(players, impact_w=args.impact_weight,
                                       league_w=args.league_weight,
                                       role_map=None,
                                       ensure_role_parity=args.role_parity)

    print(f"Team A: {len(teamA)} players, total score={totals['A']}")
    for p in teamA:
        print(f" - {p['name']} | {p['role']} | League={p['league']} | Impact={p['impact']} | score={p['score']}")

    print('\n')
    print(f"Team B: {len(teamB)} players, total score={totals['B']}")
    for p in teamB:
        print(f" - {p['name']} | {p['role']} | League={p['league']} | Impact={p['impact']} | score={p['score']}")

    if args.write_output:
        a_path = f"{args.out_prefix}_A.tsv"
        b_path = f"{args.out_prefix}_B.tsv"
        write_team(a_path, teamA)
        write_team(b_path, teamB)
        print(f"\nWrote {a_path} and {b_path}")


if __name__ == '__main__':
    main()
