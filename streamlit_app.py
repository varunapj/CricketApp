import streamlit as st
from pathlib import Path
from PIL import Image
import pandas as pd
import urllib.parse

from split_teams import (
    parse_players,
    parse_availability,
    crosscheck_availability,
    split_teams
)

# -------------------- PATHS --------------------
ROOT = Path(__file__).parent.resolve()
GENERATED = ROOT / "generated"
GENERATED.mkdir(exist_ok=True)

# -------------------- LOGO --------------------
def get_logo():
    for name in ["surprise_cricket_club.png", "Surprise_Cricket_Club.png"]:
        p = ROOT / "static" / "images" / name
        if p.exists():
            return p
    return None

# -------------------- LOAD INVENTORY --------------------
def load_inventory():
    edited = GENERATED / "Players_Inventory_edited.tsv"
    base = ROOT / "Players_Inventory.tsv"
    path = edited if edited.exists() else base

    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, sep="\t")

    # Normalize Yes/No → Y/N
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].replace(
                {"Yes": "Y", "No": "N", "yes": "Y", "no": "N"}
            )

    # Ensure No column exists
    if "No" not in df.columns:
        df.insert(0, "No", range(1, len(df) + 1))

    return df

# -------------------- MAIN APP --------------------
def main():
    st.set_page_config(
        page_title="Surprise Cricket Club — Team Splitter",
        layout="wide"
    )

    # ---------- HEADER ----------
    c1, c2 = st.columns([1, 4])
    with c1:
        logo = get_logo()
        if logo:
            st.image(Image.open(logo), width=140)
    with c2:
        st.title("Surprise Cricket Club — Team Splitter")

    st.markdown("---")

    # ---------- INVENTORY ----------
    df_inventory = load_inventory()
    if df_inventory.empty:
        st.error("Players_Inventory.tsv not found.")
        return

    with st.expander("📋 Players Inventory (Add / Edit / Delete)", expanded=True):

        df_editor = st.data_editor(
            df_inventory,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            column_config={
                "No": st.column_config.NumberColumn(
                    "No", disabled=True, width="small"
                ),
                "Role": st.column_config.SelectboxColumn(
                    "Role",
                    options=["Allrounder", "Batsman", "Bowler"]
                ),
            },
            key="players_editor"
        )

        if st.button("💾 Save Players Inventory"):
            df_save = df_editor.copy()
            df_save["No"] = range(1, len(df_save) + 1)  # auto-reindex
            df_save.to_csv(
                GENERATED / "Players_Inventory_edited.tsv",
                sep="\t",
                index=False
            )
            st.success("Inventory saved successfully!")

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.header("⚙️ Controls")
        use_avail = st.checkbox("Apply Availability File", value=True)
        uploaded_avail = st.file_uploader(
            "Upload Availability",
            type=["tsv", "csv", "xlsx", "xls"]
        )
        role_parity = st.checkbox("Balance Roles", value=True)
        split_btn = st.button("⚡ SPLIT TEAMS", use_container_width=True)

    # ---------- TEAM SPLIT ----------
    if split_btn:
        try:
            df_active = df_editor.copy()
            df_active["No"] = range(1, len(df_active) + 1)

            temp_path = GENERATED / "active_inventory.tsv"
            df_active.to_csv(temp_path, sep="\t", index=False)

            players = parse_players(str(temp_path))

            if use_avail and uploaded_avail:
                avail_path = GENERATED / uploaded_avail.name
                with open(avail_path, "wb") as f:
                    f.write(uploaded_avail.getbuffer())

                avail_names = parse_availability(str(avail_path))
                players, _, _ = crosscheck_availability(players, avail_names)

            teamA, teamB, totals = split_teams(
                players,
                ensure_role_parity=role_parity
            )

            cA, cB = st.columns(2)

            with cA:
                st.subheader(f"🏆 Team A — Score {totals.get('A', 0)}")
                dfA = pd.DataFrame(teamA)[["name"]]
                dfA.index = range(1, len(dfA) + 1)
                st.table(dfA)

            with cB:
                st.subheader(f"🏆 Team B — Score {totals.get('B', 0)}")
                dfB = pd.DataFrame(teamB)[["name"]]
                dfB.index = range(1, len(dfB) + 1)
                st.table(dfB)

            # ---------- WHATSAPP SHARE ----------
            msg = (
                "🏏 *SURPRISE CRICKET CLUB*\n\n"
                "*TEAM A*\n" +
                "\n".join(f"{i}. {p['name']}" for i, p in enumerate(teamA, 1)) +
                "\n\n*TEAM B*\n" +
                "\n".join(f"{i}. {p['name']}" for i, p in enumerate(teamB, 1))
            )

            wa_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
            st.markdown(
                f'<a href="{wa_url}" target="_blank" '
                f'style="background:#25D366;color:white;'
                f'padding:12px 20px;border-radius:8px;'
                f'text-decoration:none;font-weight:bold;display:inline-block;">'
                f'📤 Share to WhatsApp</a>',
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Error: {e}")

# -------------------- RUN --------------------
if __name__ == "__main__":
    main()
