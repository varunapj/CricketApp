from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
import tempfile
from pathlib import Path
from split_teams import parse_players, parse_availability, crosscheck_availability, split_teams

app = Flask(__name__)
app.secret_key = 'dev-secret'

ROOT = Path(__file__).resolve().parent
GENERATED_DIR = ROOT / 'generated'
GENERATED_DIR.mkdir(exist_ok=True)


def save_upload(file_storage, prefix='upload'):
    if not file_storage:
        return None
    # preserve extension so downstream parsers can detect format
    suffix = Path(file_storage.filename).suffix if file_storage.filename else ''
    tmp = tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, dir=str(GENERATED_DIR), delete=False)
    try:
        tmp.write(file_storage.read())
    finally:
        tmp.flush()
        tmp.close()
    return tmp.name


@app.route('/', methods=['GET'])
def index():
    # list repo TSVs in root to choose
    tsvs = [p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in ('.tsv', '.csv', '.xlsx', '.xls') and 'Players_Inventory' in p.name]
    return render_template('index.html', tsvs=tsvs)


@app.route('/split', methods=['POST'])
def split():
    # decide master source
    use_repo_master = request.form.get('master_source') == 'repo'
    uploaded_master = request.files.get('master_file')
    master_path = None
    if use_repo_master:
        master_choice = request.form.get('repo_master') or 'Players_Inventory.tsv'
        master_path = str(ROOT / master_choice)
    elif uploaded_master and uploaded_master.filename:
        master_path = save_upload(uploaded_master, prefix='master_')
    else:
        flash('No master TSV chosen or uploaded', 'error')
        return redirect(url_for('index'))

    # availability (optional)
    avail_choice = request.form.get('availability_source')
    availability_path = None
    if avail_choice == 'repo':
        availability_path = str(ROOT / 'Players_Availability') if (ROOT / 'Players_Availability').exists() else None
    elif avail_choice == 'upload':
        up = request.files.get('availability_file')
        if up and up.filename:
            availability_path = save_upload(up, prefix='avail_')

    # weights and options
    role_parity = bool(request.form.get('role_parity'))

    # parse master players
    players = parse_players(master_path)

    # if availability provided, parse and crosscheck
    if availability_path:
        avail_names = parse_availability(availability_path)
        matched, unmatched, ambiguous = crosscheck_availability(players, avail_names)
        players_to_split = matched
    else:
        matched = []
        unmatched = []
        ambiguous = []
        players_to_split = players

    teamA, teamB, totals = split_teams(players_to_split, ensure_role_parity=role_parity)

    # write generated files
    a_path = GENERATED_DIR / 'ui_team_A.tsv'
    b_path = GENERATED_DIR / 'ui_team_B.tsv'
    with open(a_path, 'w', encoding='utf-8') as fa:
        for p in teamA:
            fa.write(p['name'] + '\n')
    with open(b_path, 'w', encoding='utf-8') as fb:
        for p in teamB:
            fb.write(p['name'] + '\n')

    return render_template('result.html', teamA=teamA, teamB=teamB, totals=totals,
                           unmatched=unmatched, ambiguous=ambiguous,
                           a_file=a_path.name, b_file=b_path.name)


@app.route('/download/<fname>')
def download(fname):
    path = GENERATED_DIR / fname
    if not path.exists():
        flash('File not found', 'error')
        return redirect(url_for('index'))
    return send_file(str(path), as_attachment=True)


if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    # Allow controlling debug and reloader via environment variables.
    debug = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    # Disable the reloader by default on hosted platforms to avoid signal errors.
    use_reloader = os.environ.get('FLASK_USE_RELOADER', '0').lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug, use_reloader=use_reloader)
