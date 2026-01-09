import streamlit as st
from pathlib import Path
from PIL import Image
import pandas as pd
import os
# Ensure split_teams.py does not have internal circular imports!
from split_teams import parse_players, parse_availability, crosscheck_availability, split_teams

# --- PATH CONFIGURATION ---
ROOT = Path(__file__).parent.resolve()
GENERATED = ROOT / 'generated'
GENERATED.mkdir(exist_ok=True) 

def get_logo():
    """Checks for both possible filenames to handle case-sensitivity issues."""
    # List of possible names found in your screenshots
    names = ['surprise_cricket_club.png', 'Surprise_Cricket_Club.png']
    for name in names:
        # Check in the 'static/images' folder specifically
        path = ROOT / 'static' / 'images' / name
        if path.exists():
            return path
    return None

def main():
    st.set_page_config(page_title='SCC Team Splitter', layout='wide')

    # --- 1. LOGO LOADING ---
    logo_path = get_logo()
    
    if logo_path:
        try:
            img = Image.open(logo_path)
            col1, col2 = st.columns([1, 5])
            with col1:
                st.image(img, width=150) 
            with col2:
                st.title("Surprise Cricket Club — Team Splitter")
        except Exception:
            st.title("Surprise Cricket Club — Team Splitter")
    else:
        # Fallback to emoji if file is still not found
        st.title("🏏 Surprise Cricket Club — Team Splitter")

    # --- 2. SIDEBAR ---
    with st.sidebar.form('options'):
        st.header("Configuration")
        # Filters for master files in root
        repo_files = [p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in ('.tsv', '.csv', '.xlsx', '.xls')]
        
        default_idx = 0
        if 'Players_Inventory.tsv' in repo_files:
            default_idx = repo_files.index('Players_Inventory.tsv')
            
        repo_choice = st.selectbox('Master File', repo_files if repo_files else ["No files found"], index=default_idx)
        use_repo = st.checkbox('Use repository master', value=True)
        uploaded_master = st.file_uploader('Upload Master', type=['tsv', 'csv', 'xlsx', 'xls'])
        
        st.markdown("---")
        use_avail = st.checkbox('Use availability', value=False)
        uploaded_avail = st.file_uploader('Upload Availability', type=['tsv', 'csv', 'xlsx', 'xls'])
        
        st.markdown("---")
        st.write("**Priority & Balance Settings**")
        role_parity = st.checkbox('Enforce Role Parity', value=True)
        submitted = st.form_submit_button('Split Teams')

    if submitted:
        if use_repo and repo_files:
            master_path = str(ROOT / repo_choice)
        elif uploaded_master:
            master_path = str(GENERATED / f"temp_master{Path(uploaded_master.name).suffix}")
            with open(master_path, 'wb') as f:
                f.write(uploaded_master.getbuffer())
        else:
            st.error("Please provide a file.")
            return

        try:
            players = parse_players(master_path)
            
            if use_avail and uploaded_avail:
                avail_path = str(GENERATED / f"temp_avail{Path(uploaded_avail.name).suffix}")
                with open(avail_path, 'wb') as f:
                    f.write(uploaded_avail.getbuffer())
                avail_names = parse_availability(avail_path)
                matched, _, _ = crosscheck_availability(players, avail_names)
                players_to_split = matched
            else:
                players_to_split = players

            # --- 3. PRIORITY SORTING (Impact > League > Role) ---
            players_to_split.sort(key=lambda p: (
                str(p.get('Impact Player', 'No')).strip().lower() == 'yes', 
                str(p.get('League Player', 'No')).strip().lower() == 'yes', 
                str(p.get('Role', 'Allrounder')).strip()
            ), reverse=True)

            teamA, teamB, totals = split_teams(players_to_split, ensure_role_parity=role_parity)

            # --- 4. STRICT DISPLAY (NAMES ONLY) ---
            df_a = pd.DataFrame(teamA)[['name']].rename(columns={'name': 'Player Name'})
            df_b = pd.DataFrame(teamB)[['name']].rename(columns={'name': 'Player Name'})
            df_a.index += 1
            df_b.index += 1

            st.success("Teams Split by Priority (Impact > League > Role)")
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader(f"Team A (Total Score: {totals.get('A', 0)})")
                st.table(df_a) 
                
            with col_right:
                st.subheader(f"Team B (Total Score: {totals.get('B', 0)})")
                st.table(df_b)

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == '__main__':
    main()