"""Transforme data/jobs.csv en une page HTML lisible (public/index.html).

Tableau responsive avec : Titre, Entreprise, Source, Lien (cliquable),
plus une barre de recherche et un tri par colonne (JavaScript, sans dependance).
"""

import html
import logging
import os
from datetime import datetime

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "jobs.csv")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
HTML_PATH = os.path.join(PUBLIC_DIR, "index.html")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "log.txt"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("html_generator")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offres d'emploi - Developpement logiciel</title>
<style>
  :root {{ --bg:#0f172a; --card:#1e293b; --accent:#38bdf8; --text:#e2e8f0; --muted:#94a3b8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif; background:var(--bg); color:var(--text); }}
  header {{ padding:24px 16px; text-align:center; border-bottom:1px solid #334155; }}
  header h1 {{ margin:0 0 6px; font-size:1.6rem; }}
  header p {{ margin:0; color:var(--muted); }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:16px; }}
  .toolbar {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin:16px 0; }}
  #search {{ flex:1; min-width:220px; padding:10px 12px; border-radius:8px; border:1px solid #334155; background:var(--card); color:var(--text); font-size:1rem; }}
  .count {{ color:var(--muted); }}
  .table-scroll {{ overflow-x:auto; border-radius:12px; border:1px solid #334155; }}
  table {{ width:100%; border-collapse:collapse; background:var(--card); }}
  th, td {{ padding:12px 14px; text-align:left; border-bottom:1px solid #334155; vertical-align:top; }}
  th {{ position:sticky; top:0; background:#0b1220; cursor:pointer; user-select:none; white-space:nowrap; }}
  th:hover {{ color:var(--accent); }}
  tbody tr:hover {{ background:#243049; }}
  a {{ color:var(--accent); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:999px; background:#334155; font-size:.8rem; }}
  footer {{ text-align:center; padding:24px; color:var(--muted); font-size:.85rem; }}
</style>
</head>
<body>
<header>
  <h1>Offres d'emploi - Developpement logiciel</h1>
  <p>{count} offres &middot; genere le {date}</p>
</header>
<div class="wrap">
  <div class="toolbar">
    <input id="search" type="text" placeholder="Rechercher (titre, entreprise, source)..." onkeyup="filterRows()">
    <span class="count" id="visible-count"></span>
  </div>
  <div class="table-scroll">
    <table id="jobs">
      <thead>
        <tr>
          <th onclick="sortTable(0)">Titre</th>
          <th onclick="sortTable(1)">Entreprise</th>
          <th onclick="sortTable(2)">Source</th>
          <th>Lien</th>
        </tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>
</div>
<footer>Pipeline CI/CD Jenkins &middot; projet 05 &middot; Dr. Haythem REHOUMA</footer>
<script>
  function filterRows() {{
    const q = document.getElementById('search').value.toLowerCase();
    const rows = document.querySelectorAll('#jobs tbody tr');
    let visible = 0;
    rows.forEach(tr => {{
      const show = tr.innerText.toLowerCase().includes(q);
      tr.style.display = show ? '' : 'none';
      if (show) visible++;
    }});
    document.getElementById('visible-count').innerText = visible + ' resultat(s)';
  }}
  let sortAsc = true;
  function sortTable(col) {{
    const tbody = document.querySelector('#jobs tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {{
      const x = a.cells[col].innerText.toLowerCase();
      const y = b.cells[col].innerText.toLowerCase();
      return sortAsc ? x.localeCompare(y) : y.localeCompare(x);
    }});
    sortAsc = !sortAsc;
    rows.forEach(r => tbody.appendChild(r));
  }}
  filterRows();
</script>
</body>
</html>
"""


def build_rows(df):
    rows = []
    for _, r in df.iterrows():
        titre = html.escape(str(r["Titre"]))
        entreprise = html.escape(str(r["Entreprise"]))
        source = html.escape(str(r["Source"]))
        lien = html.escape(str(r["Lien"]), quote=True)
        rows.append(
            "        <tr>"
            f"<td>{titre}</td>"
            f"<td>{entreprise}</td>"
            f"<td><span class=\"badge\">{source}</span></td>"
            f"<td><a href=\"{lien}\" target=\"_blank\" rel=\"noopener\">Voir l'offre</a></td>"
            "</tr>"
        )
    return "\n".join(rows)


def main():
    if not os.path.exists(CSV_PATH):
        log.error("Fichier introuvable : %s (lancez d'abord scraper.py)", CSV_PATH)
        raise SystemExit(1)

    df = pd.read_csv(CSV_PATH).fillna("N/A")
    log.info("Lecture de %d offres depuis %s", len(df), CSV_PATH)

    page = PAGE_TEMPLATE.format(
        count=len(df),
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        rows=build_rows(df),
    )
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(page)
    log.info("Page generee : %s", HTML_PATH)


if __name__ == "__main__":
    main()
