import streamlit as st
from pathlib import Path
from PIL import Image
import pandas as pd
import os
from split_teams import parse_players, parse_availability, crosscheck_availability, split_teams

# --- PATH CONFIGURATION ---
# ROOT points to the folder containing your .py file
ROOT = Path(__file__).parent.resolve()
GENERATED = ROOT / 'generated'
GENERATED.mkdir(exist_ok=True) 

def find_logo(filename):
    """
    Recursively searches the project for the logo file to ensure 
    it works on both local and Streamlit Cloud environments.
    """
    # Streamlit Cloud is case-sensitive. Ensure 'filename' matches exactly on GitHub.
    for path in ROOT.rglob(filename):
        return path
    return None

def main():
    st.set_page_config(page_title='SCC Team Splitter', layout='wide')

    # --- 1. ROBUST LOGO LOADING ---
    # Searches for the file anywhere in your project structure
    logo_path = find_logo('surprise_cricket_club.png')
    
    if logo_path and logo_path.exists():
        try:
            img = Image.open(logo_path)
            col1, col2 = st.columns([1, 5])
            with col1:
                # use_container_width prevents stretching or broken icons
                st.image(img, width=120) 
            with col2:
                st.title("Surprise Cricket Club — Team Splitter")
        except Exception:
            st.title("Surprise Cricket Club — Team Splitter")
    else:
        # Fallback to emoji if file is missing/misnamed on GitHub
        st.title("🏏 Surprise Cricket Club — Team Splitter")

    # --- 2. SIDEBAR ---
    with st.sidebar.form('options'):
        st.header("Configuration")
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
        st.write("**Balance Settings**")
        role_parity = st.checkbox('Enforce Role Parity', value=True)
        submitted = st.form_submit_button('Split Teams')

    if submitted:
        # Handle Master File Loading
        if use_repo and repo_files:
            master_path = str(ROOT / repo_choice)
        elif uploaded_master:
            # Save buffer to a physical path so 'parse_players' can read it
            master_path = str(GENERATED / f"temp_master{Path(uploaded_master.name).suffix}")
            with open(master_path, 'wb') as f:
                f.write(uploaded_master.getbuffer())
        else:
            st.error("Please provide a file.")
            return

        try:
            players = parse_players(master_path)
            
            # Filter availability if checked
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
            # Ensures the draft starts with Impact players, then League players
            players_to_split.sort(key=lambda p: (
                p.get('Impact Player', 'No') == 'Yes', 
                p.get('League Player', 'No') == 'Yes', 
                p.get('Role', 'Allrounder')            
            ), reverse=True)

            # Perform the split
            teamA, teamB, totals = split_teams(players_to_split, ensure_role_parity=role_parity)

            # --- 4. STRICT DISPLAY (NAMES ONLY) ---
            # Removing Role column by explicitly selecting 'name' key
            df_a = pd.DataFrame(teamA)[['name']].rename(columns={'name': 'Player Name'})
            df_b = pd.DataFrame(teamB)[['name']].rename(columns={'name': 'Player Name'})
            df_a.index += 1
            df_b.index += 1

            st.success("Teams Split by Priority (Impact > League > Role)")
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader(f"Team A (Total Score: {totals.get('A', 0)})")
                st.table(df_a) # Table strictly shows only the names
                
            with col_right:
                st.subheader(f"Team B (Total Score: {totals.get('B', 0)})")
                st.table(df_b)

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == '__main__':
    main()