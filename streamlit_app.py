import streamlit as st
from pathlib import Path
from split_teams import parse_players, parse_availability, crosscheck_availability, split_teams

ROOT = Path(__file__).resolve().parent
GENERATED = ROOT / 'generated'
GENERATED.mkdir(exist_ok=True)


def write_tsv_lines(lines):
    return "\n".join(lines) + "\n"


def main():
    st.set_page_config(page_title='Team Splitter', layout='wide')
    st.title('Surprise Cricket Club — Team Splitter (Streamlit)')

    with st.sidebar.form('options'):
        st.markdown('**Master source**')
        repo_files = [p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in ('.tsv', '.csv', '.xlsx', '.xls')]
        repo_choice = st.selectbox('Repository files', repo_files, index=repo_files.index('Players_Inventory.tsv') if 'Players_Inventory.tsv' in repo_files else 0)
        use_repo = st.checkbox('Use repository master', value=True)
        uploaded_master = st.file_uploader('Upload master file (TSV/CSV/XLSX)', type=['tsv', 'csv', 'xlsx', 'xls'])

        st.markdown('**Availability (optional)**')
        use_avail = st.checkbox('Use availability file', value=False)
        uploaded_avail = st.file_uploader('Upload availability (one-per-line or Excel/CSV)', type=['tsv', 'csv', 'xlsx', 'xls'])

        st.markdown('**Scoring & options**')
        impact_w = st.number_input('Impact weight', value=100, min_value=0)
        league_w = st.number_input('League weight', value=10, min_value=0)
        role_parity = st.checkbox('Enforce role parity', value=False)

        submitted = st.form_submit_button('Split Teams')

    if submitted:
        # decide master path
        master_path = None
        if use_repo:
            master_path = str(ROOT / repo_choice)
        elif uploaded_master is not None:
            tmp = GENERATED / f'master_upload{Path(uploaded_master.name).suffix}'
            with open(tmp, 'wb') as f:
                f.write(uploaded_master.getbuffer())
            master_path = str(tmp)
        else:
            st.error('No master file selected. Either choose repository master or upload a file.')
            return

        try:
            players = parse_players(master_path)
        except Exception as e:
            st.error(f'Failed to parse master file: {e}')
            return

        # availability
        players_to_split = players
        unmatched = []
        ambiguous = []
        if use_avail:
            if uploaded_avail is None:
                st.error('Availability selected but no file uploaded')
                return
            tmpa = GENERATED / f'avail_upload{Path(uploaded_avail.name).suffix}'
            with open(tmpa, 'wb') as f:
                f.write(uploaded_avail.getbuffer())
            try:
                avail_names = parse_availability(str(tmpa))
            except Exception as e:
                st.error(f'Failed to parse availability: {e}')
                return
            matched, unmatched, ambiguous = crosscheck_availability(players, avail_names)
            players_to_split = matched

        teamA, teamB, totals = split_teams(players_to_split, impact_w=impact_w, league_w=league_w, ensure_role_parity=role_parity)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f'Team A — {len(teamA)} players — total {totals["A"]}')
            for p in teamA:
                st.write(f"- {p['name']} ({p['role']}) — score {p['score']}")
            txtA = write_tsv_lines([p['name'] for p in teamA])
            st.download_button('Download Team A', txtA, file_name='team_A.tsv', mime='text/tab-separated-values')

        with col2:
            st.subheader(f'Team B — {len(teamB)} players — total {totals["B"]}')
            for p in teamB:
                st.write(f"- {p['name']} ({p['role']}) — score {p['score']}")
            txtB = write_tsv_lines([p['name'] for p in teamB])
            st.download_button('Download Team B', txtB, file_name='team_B.tsv', mime='text/tab-separated-values')

        if unmatched:
            st.warning(f'{len(unmatched)} availability names not found. See list below.')
            st.write(unmatched)
        if ambiguous:
            st.info('Some availability names were ambiguous:')
            st.write(ambiguous)


if __name__ == '__main__':
    main()
