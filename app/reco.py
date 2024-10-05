import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import numpy as np
from app import db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Movie, Like
import threading
import os
import redis
import pickle

data_lock = threading.Lock()
data_loaded = threading.Event()

# Variables globales pour stocker les données
movies_df, likes_df, user_features, movie_features, tfidf, tfidf_matrix = None, None, None, None, None, None

redis_client = redis.Redis(host='localhost', port=6379, password='Toinesteban90@')

# Connexion à la base de données et récupération des données
def load_data(progress_callback=None):
    global movies_df, likes_df, user_features, movie_features, tfidf, tfidf_matrix

    with data_lock:
        if progress_callback:
            progress_callback(0, "Chargement des données de films depuis la base de données...")

        session = Session(db.engine)

        # Charger les films directement depuis la base de données
        query = text("""
            SELECT m.id, m.title, m.synopsis, m.year, m.month, m.day,
                   GROUP_CONCAT(DISTINCT g.name) as genres,
                   GROUP_CONCAT(DISTINCT CASE WHEN p.isRealisator = 1 THEN p.name END) as realisator,
                   GROUP_CONCAT(DISTINCT CASE WHEN p.isActor = 1 THEN p.name END) as actors
            FROM movie m
            LEFT JOIN movie_genre mg ON m.id = mg.movie_id
            LEFT JOIN genre g ON mg.genre_id = g.id
            LEFT JOIN movie_participant mp ON m.id = mp.movie_id
            LEFT JOIN participant p ON mp.participant_id = p.id
            GROUP BY m.id
        """)
        movies_data = db.session.execute(query).fetchall()
        movies_df = pd.DataFrame(movies_data, columns=['id', 'title', 'synopsis', 'year', 'month', 'day', 'genres', 'realisator', 'actors'])

        if progress_callback:
            progress_callback(30, f"Chargement de {len(movies_df)} films........OK")

        # Charger les likes
        likes = Like.query.all()
        if progress_callback:
            progress_callback(40, f"Chargement de {len(likes)} likes........OK")

        # Convertir les likes en DataFrame
        if likes:
            likes_df = pd.DataFrame([{
                'user_id': like.user_id,
                'movie_id': like.movie_id,
                'like': like.like
            } for like in likes])
        else:
            likes_df = pd.DataFrame(columns=['user_id', 'movie_id', 'like'])

        # Supprimer les doublons dans les likes
        likes_df = likes_df.drop_duplicates(subset=['user_id', 'movie_id'], keep='last')

        if progress_callback:
            progress_callback(60, "Création de la soup de données...")
        movies_df['soup'] = movies_df.apply(create_soup, axis=1)

        # Créer la matrice TF-IDF
        if progress_callback:
            progress_callback(70, "Création de la matrice TF-IDF...")
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(movies_df['soup'])

        # Préparer le filtrage collaboratif
        if progress_callback:
            progress_callback(80, "Préparation du filtrage collaboratif...")
        
        if not likes_df.empty:
            user_movie_matrix = likes_df.pivot(index='user_id', columns='movie_id', values='like').fillna(0)
            
            if user_movie_matrix.shape[1] > 1:
                n_components = min(100, user_movie_matrix.shape[1] - 1)
                
                if progress_callback:
                    progress_callback(90, "Calcul des composantes SVD...")
                svd = TruncatedSVD(n_components=n_components)
                user_features = svd.fit_transform(user_movie_matrix)
                movie_features = svd.components_.T
            else:
                print("Données insuffisantes pour un filtrage collaboratif. SVD ignoré.")
                user_features = None
                movie_features = None
        else:
            print("Aucun like trouvé. Filtrage collaboratif ignoré.")
            user_features = None
            movie_features = None

        if progress_callback:
            progress_callback(100, "Chargement des données terminé........OK")
        
            # Sauvegarde des données dans Redis
            redis_client.set('movies_df', pickle.dumps(movies_df))
            redis_client.set('likes_df', pickle.dumps(likes_df))
            redis_client.set('user_features', pickle.dumps(user_features))
            redis_client.set('movie_features', pickle.dumps(movie_features))
            redis_client.set('tfidf', pickle.dumps(tfidf))
            redis_client.set('tfidf_matrix', pickle.dumps(tfidf_matrix))
            print("Data saved to Redis successfully.")

    data_loaded.set()

    return movies_df, likes_df, user_features, movie_features, tfidf_matrix

# Création de la soup de caractéristiques en ajoutant du poids
def create_soup(x):
    genres = x['genres'] if x['genres'] is not None else ''
    realisator = x['realisator'] if x['realisator'] is not None else ''
    actors = x['actors'] if x['actors'] is not None else ''
    synopsis = x['synopsis'] if x['synopsis'] is not None else ''
    year = str(x['year']) if x['year'] is not None else ''
    return (genres + ' ') * 4 + (realisator + ' ') * 3 + (actors + ' ') * 2 + synopsis + ' ' + (year + ' ') * 2

# On créer une fonction pour obtenir les films les plus similaires basés sur le contenu
def content_based_recommendations(genres=None, realisator=None, actors=None, top_n=10):
    query_part = []
    if genres:
        if isinstance(genres, str):
            query_part.append(genres)
        elif isinstance(genres, list):
            query_part.extend(map(str, genres))
    if realisator:
        query_part.append(realisator)
    if actors:
        if isinstance(actors, str):
            query_part.append(actors)
        elif isinstance(actors, list):
            query_part.extend(map(str, actors)) 

    query = ', '.join(query_part)

    # Création d'un film à partir de la requête
    query_soup = ' '.join(query.split(', '))

    # Vérifiez que tfidf n'est pas None avant d'appeler transform
    if tfidf is None:
        raise ValueError("tfidf n'a pas été initialisé correctement.")

    query_tfidf = tfidf.transform([query_soup])

    # On calcule les similarités entre la requête et les films
    sim_scores = cosine_similarity(query_tfidf, tfidf_matrix).flatten()

    # On récupère les indices des films les plus similaires
    top_indices = sim_scores.argsort()[-top_n:][::-1]

    # On retourne les films les plus similaires
    recommendations = [
        {
            'id': int(movies_df.iloc[idx]['id']),
            'title': movies_df.iloc[idx]['title'],
            'year': int(movies_df.iloc[idx].get('year', 0)),
            'score': float(sim_scores[idx])
        }
        for idx in top_indices
    ]

    return recommendations

# Fonction de recommandation collaborative
def collaborative_filtering_recommendations(user_id, top_n=10):
    if user_features is None or movie_features is None:
        print("Warning: Collaborative filtering data not available.")
        return []

    if user_id not in likes_df['user_id'].unique():
        return []
    
    # Créer un dictionnaire pour mapper les IDs utilisateurs aux indices
    user_id_to_index = {user_id: idx for idx, user_id in enumerate(likes_df['user_id'].unique())}
    
    # Utiliser l'ID utilisateur pour obtenir l'index correct
    user_index = user_id_to_index.get(user_id)
    
    if user_index is None:
        raise ValueError(f"User ID {user_id} introuvable dans likes_df")
    
    if user_index >= len(user_features):
        raise IndexError(f"user_index {user_index} est hors limites pour l'axe 0 avec une taille {len(user_features)}")
    
    user_vector = user_features[user_index]
    scores = np.dot(movie_features, user_vector)
    top_indices = scores.argsort()[-top_n:][::-1]
    
    return [{
        'id': int(movies_df.iloc[idx]['id']),
        'title': movies_df.iloc[idx]['title'],
        'year': int(movies_df.iloc[idx]['year']),
        'score': float(scores[idx])
    } for idx in top_indices]

def hybrid_recommendations(user_id, genres=None, realisator=None, actors=None, top_n=10):
    if not data_loaded.is_set():
        data_loaded.wait(timeout=30)  # Attendre jusqu'à 30 secondes
        if not data_loaded.is_set():
            raise TimeoutError("Data loading timeout")

    with data_lock:
        # Préparation de la requête de contenu
        query_part = []
        if genres:
            if isinstance(genres, str):
                query_part.append(genres)
            elif isinstance(genres, list):
                query_part.extend(map(str, genres))
        if realisator:
            query_part.append(realisator)
        if actors:
            if isinstance(actors, str):
                query_part.append(actors)
            elif isinstance(actors, list):
                query_part.extend(map(str, actors))
        
        content_query = ' '.join(query_part)
        print(f"Content Query: {content_query}")  # Debugging line

        # Obtenir les recommandations basées sur le contenu
        content_recs = content_based_recommendations(genres, realisator, actors, top_n * 2)

        # Vérifier si le filtrage collaboratif est possible
        if user_features is not None and movie_features is not None and user_id in likes_df['user_id'].unique():
            collab_recs = collaborative_filtering_recommendations(user_id, top_n * 2)
        else:
            print("Avertissement : données insuffisantes pour un filtrage collaboratif. SVD ignoré.")
            collab_recs = []

        # Combiner les recommandations
        all_recs = {}
        for rec in content_recs + collab_recs:
            if rec['id'] not in all_recs:
                all_recs[rec['id']] = rec
                all_recs[rec['id']]['content_score'] = 0
                all_recs[rec['id']]['collab_score'] = 0
            if rec in content_recs:
                all_recs[rec['id']]['content_score'] = rec['score']
            if rec in collab_recs:
                all_recs[rec['id']]['collab_score'] = rec['score']

        # Normalisation des scores
        max_content_score = max((rec['content_score'] for rec in all_recs.values()), default=1)
        max_collab_score = max((rec['collab_score'] for rec in all_recs.values()), default=1)

        for rec in all_recs.values():
            rec['content_score'] = rec['content_score'] / max_content_score if max_content_score > 0 else 0
            rec['collab_score'] = rec['collab_score'] / max_collab_score if max_collab_score > 0 else 0
            
            # Ajuster les poids si le filtrage collaboratif n'est pas disponible
            if collab_recs:
                rec['score'] = 0.6 * rec['content_score'] + 0.4 * rec['collab_score']
            else:
                rec['score'] = rec['content_score']

        # Ajouter un facteur de popularité si possible
        if not likes_df.empty:
            popularity = likes_df.groupby('movie_id').size()
            max_popularity = popularity.max() if not popularity.empty else 1
            for rec in all_recs.values():
                pop_score = popularity.get(rec['id'], 0) / max_popularity
                rec['score'] = 0.8 * rec['score'] + 0.2 * pop_score
        
        sorted_recs = sorted(all_recs.values(), key=lambda x: x['score'], reverse=True)[:top_n]
        
        # Conversion des types de données pour assurer la compatibilité JSON
        for rec in sorted_recs:
            rec['id'] = int(rec['id'])
            rec['year'] = int(rec['year']) if 'year' in rec and rec['year'] is not None else None
            rec['score'] = float(rec['score'])
            rec['content_score'] = float(rec['content_score'])
            rec['collab_score'] = float(rec['collab_score'])
        
        return sorted_recs

# On créer des recommandations basé sur les likes de l'utilisateur
def content_based_likes(user_id, top_n=10):
    """
    Cette fonction recommande des films similaires aux films aimés par l'utilisateur.
    """
    if user_id not in likes_df['user_id'].unique():
        return []
    
    user_likes = likes_df[likes_df['user_id'] == user_id]
    liked_movies = movies_df[movies_df['id'].isin(user_likes['movie_id'])]
    
    query_parts = liked_movies['soup'].tolist()
    content_query = ' '.join(query_parts)
    
    return content_based_recommendations(content_query, top_n)
