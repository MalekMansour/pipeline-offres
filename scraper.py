"""Scraping multi-sources d'offres d'emploi (developpement logiciel).

Genere data/jobs.csv avec les colonnes : Titre, Entreprise, Source, Lien.
Utilise le module logging (et non print) et journalise dans logs/log.txt.
"""

import logging
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- Chemins (toujours relatifs a CE fichier, pas au repertoire courant) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
CSV_PATH = os.path.join(DATA_DIR, "jobs.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- Configuration du logging (fichier + console) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "log.txt"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 15


def scrape_hackernews():
    """Offres de la page jobs de HackerNews."""
    url = "https://news.ycombinator.com/jobs"
    offers = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(res.text, "lxml")
        for row in soup.find_all("tr", class_="athing"):
            a = row.find("span", class_="titleline")
            a = a.find("a") if a else row.find("a")
            if a and a.text.strip():
                href = a.get("href", "")
                if href.startswith("item?id="):
                    href = "https://news.ycombinator.com/" + href
                offers.append({
                    "Source": "HackerNews",
                    "Titre": a.text.strip(),
                    "Entreprise": "N/A",
                    "Lien": href,
                })
    except Exception as e:  # noqa: BLE001
        log.warning("Erreur HackerNews : %s", e)
    log.info("HackerNews : %d offres", len(offers))
    return offers


def scrape_python_jobs():
    """Offres de python.org/jobs."""
    url = "https://www.python.org/jobs/"
    offers = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(res.text, "lxml")
        for job in soup.select(".list-recent-jobs li"):
            if not job.h2 or not job.h2.a:
                continue
            company = job.find("span", class_="listing-company-name")
            offers.append({
                "Source": "Python.org",
                "Titre": job.h2.text.strip(),
                "Entreprise": company.text.strip() if company else "N/A",
                "Lien": "https://www.python.org" + job.h2.a["href"],
            })
    except Exception as e:  # noqa: BLE001
        log.warning("Erreur Python.org : %s", e)
    log.info("Python.org : %d offres", len(offers))
    return offers


def scrape_remotive():
    """Offres via l'API JSON de Remotive (source la plus fiable)."""
    url = "https://remotive.com/api/remote-jobs?category=software-dev"
    offers = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        for job in res.json().get("jobs", []):
            offers.append({
                "Source": "Remotive",
                "Titre": job.get("title", "N/A"),
                "Entreprise": job.get("company_name", "N/A"),
                "Lien": job.get("url", ""),
            })
    except Exception as e:  # noqa: BLE001
        log.warning("Erreur Remotive : %s", e)
    log.info("Remotive : %d offres", len(offers))
    return offers


def scrape_workingnomads():
    """Offres via l'API JSON de WorkingNomads."""
    url = "https://www.workingnomads.com/api/exposed_jobs/"
    offers = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        for job in res.json():
            offers.append({
                "Source": "WorkingNomads",
                "Titre": job.get("title", "N/A"),
                "Entreprise": job.get("company_name", "N/A"),
                "Lien": job.get("url", ""),
            })
    except Exception as e:  # noqa: BLE001
        log.warning("Erreur WorkingNomads : %s", e)
    log.info("WorkingNomads : %d offres", len(offers))
    return offers


def main():
    log.info("Scraping multi-sources en cours...")

    all_offers = []
    all_offers += scrape_remotive()
    all_offers += scrape_workingnomads()
    all_offers += scrape_python_jobs()
    all_offers += scrape_hackernews()

    df = pd.DataFrame(all_offers, columns=["Titre", "Entreprise", "Source", "Lien"])
    # Nettoyage : retirer les lignes sans titre ou sans lien, et les doublons.
    df = df.dropna(subset=["Titre", "Lien"])
    df = df[df["Titre"].str.strip() != ""]
    df = df.drop_duplicates(subset=["Lien"]).reset_index(drop=True)

    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    log.info("Fichier %s genere avec %d offres.", CSV_PATH, len(df))

    if len(df) < 10:
        log.error("Moins de 10 offres recuperees (%d) : sources possiblement bloquees.", len(df))


if __name__ == "__main__":
    main()
