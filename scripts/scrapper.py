import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import base64
import os
from datetime import datetime
import shutil

# Paramètres de scraping
START = 0
END = 8035
PLAGE = 100

# On récupère l'url de la page
url = "https://www.allocine.fr/films/?page="

def save_base64_image(data, filename):
    with open(filename, "wb") as fh:
        fh.write(base64.b64decode(data.split(",")[1]))

def scrape_page(page, callback=None):
    response = requests.get(url + str(page))
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    page_movies = []
    for movie in soup.select('li.mdl'):
        title = movie.select_one('h2.meta-title').text.strip() if movie.select_one('h2.meta-title') else ''
        img_tag = movie.select_one('img.thumbnail-img')
        if img_tag:
            poster = img_tag.get('data-src', img_tag.get('src', ''))
            if poster.startswith('data:image'):
                filename = f"poster_{title.replace(' ', '_')}.jpg"
                save_base64_image(poster, filename)
                poster = filename
        else:
            poster = ''
        rating = movie.select_one('span.stareval-note').text.strip() if movie.select_one('span.stareval-note') else ''
        author = movie.select_one('div.meta-body-item.meta-body-direction').text.strip().replace('\n', ' ').replace('|', ' ').replace('  ', ' ').replace('De', '') if movie.select_one('div.meta-body-item.meta-body-direction') else ''
        infos = movie.select_one('div.meta-body-item.meta-body-info').text.strip().split('\n|\n') if movie.select_one('div.meta-body-item.meta-body-info') else []
        date = infos[0] if len(infos) > 0 else ''
        duration = infos[1] if len(infos) > 1 else ''
        genre = infos[2].replace('\n', '') if len(infos) > 2 else ''
        actors = movie.select_one('div.meta-body-item.meta-body-actor').text.strip().replace('\n', ' ').replace('|', ' ').replace('  ', ' ').replace('Avec', '').replace(', ', ',') if movie.select_one('div.meta-body-item.meta-body-actor') else ''
        synopsis = movie.select_one('div.synopsis').text.strip() if movie.select_one('div.synopsis') else ''
        page_movies.append({
            'title': title,
            'poster': poster,
            'author': author,
            'date': date,
            'rating': rating,
            'genre': genre,
            'actors': actors,
            'duration': duration,
            'synopsis': synopsis
        })
    
    return page_movies

def scrape_all_pages(start_page, end_page, callback=None):
    movies = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scrape_page, page, callback) for page in range(start_page, end_page + 1)]
        for future in as_completed(futures):
            movies.extend(future.result())
    return movies

def calculate_progress(start, end, current):
    total = end - start
    progress = current - start
    return int((progress / total) * 100)

def main(callback=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.dirname(script_dir)
    datas_dir = os.path.join(api_dir, 'datas')
    # On commence par créer un backup en renoman le fichier movies.csv en movies_backup_date.csv
    original_file = os.path.join(datas_dir, 'movies.csv')
    backup_file = os.path.join(datas_dir, f'movies_backup_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv')
    try:
        # On renomme le fichier movies.csv en movies_backup_date.csv
        shutil.copyfile(original_file, backup_file)
        # On supprime le fichier movies.csv
        os.remove(original_file)
        if callback:
            callback({
                "text": "Backup du fichier CSV terminé",
                "status": "terminé",
                "progress": 0
            })
    except IOError as e:
        if callback:
            callback({
                "text": "Erreur lors du backup du fichier CSV",
                "status": "erreur",
                "progress": 0
            })
        raise e

    start = START
    end = END
    plage = PLAGE
    for i in range(start, end, plage):
        current_progress = i - start
        percentage = calculate_progress(start, end, i)
        if callback:
            callback({
                "text": f'Scraping de la page {i} à la page {i + plage}',
                "status": "en cours",
                "progress": percentage
            })
        movies = scrape_all_pages(i, i + plage, callback)
        if callback:
            callback({
                "text": f'Scraping de la page {i} à la page {i + plage}',
                "status": "terminé",
                "progress": percentage
            })
        with open(original_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=movies[0].keys())
            if i == start:
                writer.writeheader()
            writer.writerows(movies)
        if callback:
            callback({
                "text": f'Écriture des données dans le fichier CSV',
                "status": "en cours",
                "progress": percentage
            })
    if callback:
        callback({
            "text": "Scrapping dans le fichier CSV terminé",
            "status": "terminé",
            "progress": 100
        })
