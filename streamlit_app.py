import streamlit as st
from pathlib import Path
from PIL import Image
import pandas as pd
import os
from split_teams import parse_players, parse_availability, crosscheck_availability, split_teams

# Paths
ROOT = Path(__file__).resolve().parent
GENERATED = ROOT / 'generated'
GENERATED.mkdir(exist_ok=True) # Create folder for temp files
LOGO_PATH = ROOT / 'static' / 'images' / 'surprise_cricket_club.png'

def main():
    st.set_page_config(page_title='SCC Team Splitter', layout='wide')

    # --- 1. LOGO ---
    if LOGO_PATH.exists():
        try:
            img = Image.open(LOGO_PATH)
            col1, col2 = st.columns([1, 6])
            with col1:
                st.image(img, width=100)
            with col2:
                st.title("Surprise Cricket Club — Team Splitter")
        except Exception:
            st.title("Surprise Cricket Club — Team Splitter")
    else:
        st.title("Surprise Cricket Club — Team Splitter")

    # --- 2. SIDEBAR ---
    with st.sidebar.form('options'):
        st.header("Configuration")
        repo_files = [p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in ('.tsv', '.csv', '.xlsx', '.xls')]
        repo_choice = st.selectbox('Master File', repo_files, index=0)
        use_repo = st.checkbox('Use repository master', value=True)
        uploaded_master = st.file_uploader('Upload Master', type=['tsv', 'csv', 'xlsx', 'xls'])
        
        st.markdown("---")
        use_avail = st.checkbox('Use availability', value=False)
        uploaded_avail = st.file_uploader('Upload Availability', type=['tsv', 'csv', 'xlsx', 'xls'])
        
        role_parity = st.checkbox('Enforce role parity', value=False)
        submitted = st.form_submit_button('Split Teams')

    if submitted:
        # --- 3. UPLOADED FILE PATH FIX ---
        if use_repo:
            master_path = str(ROOT / repo_choice)
        elif uploaded_master:
            # We save the upload to a real path so 'parse_players' can read it
            master_path = str(GENERATED / f"temp_master{Path(uploaded_master.name).suffix}")
            with open(master_path, 'wb') as f:
                f.write(uploaded_master.getbuffer())
        else:
            st.error("Please provide a file.")
            return

        try:
            players = parse_players(master_path)
            
            if use_avail and uploaded_avail:
                # Same fix for availability file
                avail_path = str(GENERATED / f"temp_avail{Path(uploaded_avail.name).suffix}")
                with open(avail_path, 'wb') as f:
                    f.write(uploaded_avail.getbuffer())
                avail_names = parse_availability(avail_path)
                matched, _, _ = crosscheck_availability(players, avail_names)
                players_to_split = matched
            else:
                players_to_split = players

            teamA, teamB, totals = split_teams(players_to_split, ensure_role_parity=role_parity)

            # --- 4. STRICT NAME-ONLY FILTER ---
            # Convert to DataFrame and drop every column except 'name'
            df_a = pd.DataFrame(teamA)[['name']].rename(columns={'name': 'Player Name'})
            df_a.index += 1
            
            df_b = pd.DataFrame(teamB)[['name']].rename(columns={'name': 'Player Name'})
            df_b.index += 1

            st.success("Teams Split Successfully!")
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader(f"Team A (Total Score: {totals['A']})")
                st.table(df_a) # Force display of only the 'Name' column
                
            with col_right:
                st.subheader(f"Team B (Total Score: {totals['B']})")
                st.table(df_b)

        except Exception as e:
            st.error(f"Error during team split: {e}")

if __name__ == '__main__':
    main()