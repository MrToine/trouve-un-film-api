# On charge les librairies nécessaires pour convertir un CSV en base de données
import pandas as pd
from collections import defaultdict
from sqlalchemy import create_engine
import os

def refresh():
    # On récupère les données du fichier CSV
    dataset_path = os.path.join('datas', 'movies.csv')
    dataset = pd.read_csv(dataset_path, sep=',', encoding='utf-8')

    # On nettoie les données
    dataset = dataset.dropna()

    # On créer le dataset des films
    dataset_movies = dataset.copy()
    dataset_movies = dataset_movies.drop(columns=['rating', 'genre', 'actors', 'author'])

    # Dictionnaire pour convertir les noms de mois en français en chiffres
    mois_to_num = {
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
    }

    # On split la colonne date en 3 colonnes Année, Mois et Jour
    dataset_movies['date'] = dataset_movies['date'].str.split(' ')
    dataset_movies['year'] = dataset_movies['date'].str[2]
    dataset_movies['month'] = dataset_movies['date'].str[1].map(mois_to_num)
    dataset_movies['day'] = dataset_movies['date'].str[0]

    # Convertir Year et day en entiers
    dataset_movies['year'] = pd.to_numeric(dataset_movies['year'], errors='coerce').astype('Int64')
    dataset_movies['month'] = pd.to_numeric(dataset_movies['month'], errors='coerce').astype('Int64')
    dataset_movies['day'] = pd.to_numeric(dataset_movies['day'], errors='coerce').astype('Int64')

    # Gérer les cas où la date est "date de sortie inconnue"
    mask_unknown = dataset_movies['date'].apply(lambda x: x[0] == 'date')
    dataset_movies.loc[mask_unknown, ['year', 'month', 'day']] = 0

    # Supprimer la colonne date originale
    dataset_movies = dataset_movies.drop(columns=['date'])

    # Réinitialiser l'index
    dataset_movies = dataset_movies.reset_index(drop=True)
    dataset_movies['id'] = dataset_movies.index + 1

    # Création de dataset_genre
    all_genres = set()
    for genres in dataset['genre'].dropna():
        all_genres.update([g.strip() for g in genres.split(',')])

    dataset_genre = pd.DataFrame({'name': sorted(all_genres)})
    dataset_genre['id'] = dataset_genre.index + 1
    dataset_genre = dataset_genre[['id', 'name']]

    # Création de df_movie_genre
    movie_genre_data = []
    for _, row in dataset.iterrows():  # Utilisez dataset au lieu de dataset_movies
        movie_id = dataset_movies[dataset_movies['title'] == row['title']]['id'].values[0]
        if pd.notna(row['genre']):
            genres = [genre.strip() for genre in row['genre'].split(',')]
            for genre in genres:
                genre_id = dataset_genre[dataset_genre['name'] == genre]['id'].values
                if len(genre_id) > 0:
                    movie_genre_data.append({'movie_id': movie_id, 'genre_id': genre_id[0]})

    df_movie_genre = pd.DataFrame(movie_genre_data)

    # Création de dataset_participants

    dataset_participants = dataset.copy()

    # Créer deux DataFrames séparés pour les acteurs et les réalisateurs
    df_acteurs = dataset_participants['actors'].str.split(',', expand=True).melt()
    df_acteurs = df_acteurs.dropna().drop(columns=['variable']).rename(columns={'value': 'name'})
    df_acteurs['isActor'] = True
    df_acteurs['isRealisator'] = False  

    df_realisateurs = dataset_participants['author'].str.split(',', expand=True).melt()
    df_realisateurs = df_realisateurs.dropna().drop(columns=['variable']).rename(columns={'value': 'name'})
    df_realisateurs['isRealisator'] = True
    df_realisateurs['isActor'] = False  

    # Fusionner les deux DataFrames
    df_movieParticipant = pd.concat([df_acteurs, df_realisateurs], ignore_index=True)

    # Nettoyer les noms et supprimer les doublons
    df_movieParticipant['name'] = df_movieParticipant['name'].str.strip()
    df_movieParticipant = df_movieParticipant.drop_duplicates(subset=['name'], keep='first')

    # Réinitialiser l'index et ajouter une colonne id
    df_movieParticipant = df_movieParticipant.reset_index(drop=True)
    df_movieParticipant['id'] = df_movieParticipant.index + 1

    # Réorganiser les colonnes
    df_movieParticipant = df_movieParticipant[['id', 'name', 'isActor', 'isRealisator']]

    # Créer un dictionnaire de correspondance pour les films
    movie_dict = dict(zip(dataset_movies['title'], dataset_movies['id']))

    participant_dict = defaultdict(list)

    for name, id in zip(df_movieParticipant['name'].str.lower(), df_movieParticipant['id']):
        participant_dict[name].append(id)

    # Fonction pour obtenir les IDs des participants
    def get_participant_ids(names, participant_dict):
        if pd.isna(names):
            return []
        return [participant_dict.get(name.strip().lower()) for name in names.split(',') if participant_dict.get(name.strip().lower()) is not None]

    # Appliquer la fonction aux colonnes Acteurs et Auteur
    dataset['actor_ids'] = dataset['actors'].apply(lambda x: get_participant_ids(x, participant_dict))
    dataset['director_ids'] = dataset['author'].apply(lambda x: get_participant_ids(x, participant_dict))


    # Fonction pour obtenir l'ID du film
    def get_movie_id(title, movie_dict):
        return movie_dict.get(title)

    # Créer la table de relation movie_participant
    movie_participant_data = []
    for _, row in dataset.iterrows():
        movie_id = get_movie_id(row['title'], movie_dict)
        if movie_id is None:
            print(f"Avertissement : Aucun ID trouvé pour le film '{row['title']}'")
            continue
        
        actor_ids = get_participant_ids(row['actors'], participant_dict)
        director_ids = get_participant_ids(row['author'], participant_dict)
        
        for participant_id in actor_ids:
            movie_participant_data.append({'movie_id': movie_id, 'participant_id': participant_id[0], 'role': 'actor'})
        
        for participant_id in director_ids:
            movie_participant_data.append({'movie_id': movie_id, 'participant_id': participant_id[0], 'role': 'director'})

    df_movie_participant = pd.DataFrame(movie_participant_data)

    # Créer la base de données. On commence par créer une copie du fichier recom-films.db
    db_path = os.path.join('datas', 'recom-films.db')
    db_backup_path = os.path.join('datas', 'recom-films_backup.db')
    if os.path.exists(db_path):
        os.replace(db_path, db_backup_path)

    # On se connecte à la base de données
    engine = create_engine('sqlite:///./datas/recom-films.db', echo=True)

    # On efface les tables si elles existent

    with engine.connect() as connection:
        connection.execute('DROP TABLE IF EXISTS movie')
        connection.execute('DROP TABLE IF EXISTS genre')
        connection.execute('DROP TABLE IF EXISTS participant')
        connection.execute('DROP TABLE IF EXISTS movie_genre')
        connection.execute('DROP TABLE IF EXISTS movie_participant')

    # On enregistre les données dans la base de données
    with engine.connect() as connection:
        dataset_movies.to_sql('movie', con=connection, if_exists='replace', index=False)
        dataset_genre.to_sql('genre', con=connection, if_exists='replace', index=False)
        df_movieParticipant.to_sql('participant', con=connection, if_exists='replace', index=False)
        df_movie_genre.to_sql('movie_genre', con=connection, if_exists='replace', index=False)
        df_movie_participant.to_sql('movie_participant', con=connection, if_exists='replace', index=False)