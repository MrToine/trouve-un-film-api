from flask_restful import Resource
from flask import request
from app.models import Movie, Like
from sqlalchemy import desc, func, text, case
from app.database import db

class MovieResource(Resource):
    def get(self, movie_id=None):
        if movie_id:
            movie = Movie.query.get_or_404(movie_id)
            return {
                'id': movie.id,
                'title': movie.title,
                'duration': movie.duration,
                'poster': movie.poster,
                'year': movie.year,
                'month': movie.month,
                'day': movie.day,
                'synopsis': movie.synopsis,
                'genres': [{'name': genre.name} for genre in movie.genres],
                # On récupère les participants du film dont isActor est True
                'actors': [{'name': p.name} for p in movie.participants if p.isActor],
                # On récupère les participants du film dont isRealisator est True
                'realisators': [{'name': p.name} for p in movie.participants if p.isRealisator],
                # On récupère les utilisateurs qui ont liké le film si ils existent
                'likes': [{
                    'user_id': like.user.id if like.user else None,
                } for like in movie.likes if like.user]
            }
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', None)

        if search:
            query = Movie.query.filter(Movie.title.ilike(f"%{search}%"))
        else:
            # Tri par date de sortie la plus récente
            query = Movie.query.order_by(
                desc(Movie.year),
                desc(Movie.month),
                desc(Movie.day)
            )

        paginated_movies = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'movies': [{
                'id': movie.id,
                'title': movie.title,
                'poster': movie.poster,
                'duration': movie.duration,
                'year': movie.year,
                'month': movie.month,
                'day': movie.day,
                'synopsis': movie.synopsis,
                'genres': [{'name': genre.name} for genre in movie.genres],
                'actors': [{'name': p.name} for p in movie.participants if p.isActor],
                'realisators': [{'name': p.name} for p in movie.participants if p.isRealisator],
                # On récupère les utilisateurs qui ont liké le film
                'likes': [{
                    'user_id': like.user.id if like.user else None,
                } for like in movie.likes if like.user]
            } for movie in paginated_movies.items],
            'total': paginated_movies.total,
            'pages': paginated_movies.pages,
            'current_page': page
        }

class MovieCountResource(Resource):
    def get(self):
        return {'count': Movie.query.count()}

class MoviesByLikes(Resource):
    def get(self, nb_sorted=10):
        # Utiliser une requête SQL optimisée pour récupérer les films les plus likés
        most_liked_movies = db.session.query(
            Movie.id,
            Movie.title,
            func.count(Like.id).label('like_count')
        ).join(Like, Movie.id == Like.movie_id, isouter=True
        ).group_by(Movie.id
        ).order_by(func.count(Like.id).desc()
        ).limit(nb_sorted).all()

        return [{
            'id': movie.id,
            'title': movie.title,
            'likes': movie.like_count
        } for movie in most_liked_movies]
    
class MoviesByYear(Resource):
    def get(self, year=None):
        #On récupère le nombre de films sortis par année
        # Si year est None, on retourne le nombre de films triés sur les 10 dernières années
        if year is None:
            movies_by_year = db.session.query(
                Movie.year,
                func.count(Movie.id).label('movie_count')
            ).group_by(Movie.year
            ).order_by(Movie.year.desc()
            ).limit(10).all()
            return [{
                'year': movie.year,
                'movies': movie.movie_count
            } for movie in movies_by_year]

        movies_by_year = Movie.query.filter(Movie.year == year).count()
        return {'movies': movies_by_year}

class MoviesByDuration(Resource):
    def get(self):
        query = text("""
            WITH duration_in_minutes AS (
                SELECT
                    CAST(SUBSTR(duration, 1, INSTR(duration, 'h') - 1) AS INTEGER) * 60 +
                    CAST(SUBSTR(duration, INSTR(duration, ' ') + 1, INSTR(duration, 'min') - INSTR(duration, ' ') - 1) AS INTEGER) AS minutes
                FROM movie
                WHERE duration IS NOT NULL AND duration != ''
            )
            SELECT 
                COUNT(*) as movie_count,
                CASE 
                    WHEN minutes < 90 THEN '< 90 min'
                    WHEN minutes >= 90 AND minutes < 120 THEN '90-120 min'
                    WHEN minutes >= 120 AND minutes < 150 THEN '120-150 min'
                    WHEN minutes >= 150 AND minutes < 180 THEN '150-180 min'
                    WHEN minutes >= 180 THEN '> 180 min'
                    ELSE 'Unknown'
                END as duration_range
            FROM duration_in_minutes
            GROUP BY duration_range
            ORDER BY 
                CASE duration_range
                    WHEN '< 90 min' THEN 1
                    WHEN '90-120 min' THEN 2
                    WHEN '120-150 min' THEN 3
                    WHEN '150-180 min' THEN 4
                    WHEN '> 180 min' THEN 5
                    ELSE 6
                END
        """)
        
        result = db.session.execute(query)
        
        return [{
            'duration_range': row.duration_range,
            'movies': row.movie_count
        } for row in result]

class MoviesByGenre(Resource):
    def get(self):
        query = text("""
            SELECT 
                COUNT(*) as movie_count,
                genre.name as genre_name
            FROM movie
            JOIN movie_genre ON movie.id = movie_genre.movie_id
            JOIN genre ON movie_genre.genre_id = genre.id
            GROUP BY genre_name
            ORDER BY movie_count DESC
        """)
        
        result = db.session.execute(query)
        
        return [{
            'genre_name': row.genre_name,
            'movies': row.movie_count
        } for row in result]

class moviesByRealisator(Resource):
    def get(self):
        query = text("""
            SELECT 
                COUNT(*) as movie_count,
                participant.name as realisator_name
            FROM movie
            JOIN movie_participant ON movie.id = movie_participant.movie_id
            JOIN participant ON movie_participant.participant_id = participant.id
            WHERE movie_participant.is_realisator = 1
            GROUP BY realisator_name
            ORDER BY movie_count DESC
        """)
        
        result = db.session.execute(query)
        
        return [{
            'realisator_name': row.realisator_name,
            'movies': row.movie_count
        } for row in result]

class moviesByActors(Resource):
    def get(self):
        query = text("""
            SELECT 
                COUNT(*) as movie_count,
                participant.name as actor_name
            FROM movie
            JOIN movie_participant ON movie.id = movie_participant.movie_id
            JOIN participant ON movie_participant.participant_id = participant.id
            WHERE movie_participant.is_actor = 1
            GROUP BY actor_name
            ORDER BY movie_count DESC
        """)
        
        result = db.session.execute(query)
        
        return [{
            'actor_name': row.actor_name,
            'movies': row.movie_count
        } for row in result]