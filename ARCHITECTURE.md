**Architecture Diagram**

The architecture diagram for the Team Split app is available in the repository:

- File: [static/images/architecture.svg](static/images/architecture.svg)

- PNG raster preview: [static/images/architecture.png](static/images/architecture.png)

Overview:
- Client Browser → Flask App (`app.py`) → Splitter (`split_teams.py`) → generated TSV outputs
- Inputs: `Players_Inventory.tsv` (master), optional availability uploads
- Outputs: `generated/ui_team_A.tsv`, `generated/ui_team_B.tsv` (names-only)

To preview locally, open `static/images/architecture.svg` in your browser or image viewer.
