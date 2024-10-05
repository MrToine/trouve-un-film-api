from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Database:
    """
    Classe Database pour la gestion de la base de données.
    """
    def __init__(self, db_url):
        """
        Constructeur de la classe Database.
        parameters 
        ----------
        db_url: URL de la base de données        
        """
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
    
    def check_connection(self):
        """
        Vérifie la connexion à la base de données.
        """
        try:
            self.engine.connect()
            return True
        except:
            return False
    
    def check_table(self, table_name):
        """
        Vérifie l'existence d'une table dans la base de données.
        parameters 
        ----------
        table_name: Nom de la table        
        """
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    
    def create_table(self, table):
        """
        Crée une table dans la base de données.
        parameters 
        ----------
        table: Table à créer        
        """
        table.__table__.create(self.engine)
    
    def insert_record(self, table_name, record):
        """
        Insère un enregistrement dans la table.

        Parameters
        ----------
        table_name : str
            Le nom de la table.
        record : dict
            Un dictionnaire où les clés sont les noms des colonnes et les valeurs sont les valeurs à insérer.
        """
        columns = ", ".join(record.keys())
        placeholders = ", ".join([f":{col}" for col in record.keys()])
        query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})")
        
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(query, record)
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                print(f"Erreur lors de l'insertion: {e}")
                raise
    
    def update_record(self, table_name, record, where_clause):
        """
        Met à jour un enregistrement dans la table.

        Parameters
        ----------
        table_name : str
            Le nom de la table.
        record : dict
            Un dictionnaire où les clés sont les noms des colonnes et les valeurs sont les nouvelles valeurs.
        where_clause : str
            La clause WHERE pour spécifier quel enregistrement mettre à jour.
        """
        set_clause = ", ".join([f"{col} = :{col}" for col in record.keys()])
        query = text(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}")
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(query, record)
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                print(f"Erreur lors de la mise à jour: {e}")
                raise

    def delete_record(self, table_name, where_clause):
        """
        Supprime un enregistrement de la table.

        Parameters
        ----------
        table_name : str
            Le nom de la table.
        where_clause : str
            La clause WHERE pour spécifier quel enregistrement supprimer.
        """
        query = text(f"DELETE FROM {table_name} WHERE {where_clause}")
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(query)
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                print(f"Erreur lors de la suppression: {e}")

    def get_records(self, table_name, convert_func=None):
        """
        Récupère tous les enregistrements de la table.

        Parameters
        ----------
        table_name : str
            Le nom de la table.
        convert_func : function, optional
            Fonction pour convertir les données brutes en objets spécifiques.

        Returns
        -------
        list
            Une liste d'enregistrements ou d'objets convertis.
        """
        query = text(f"SELECT * FROM {table_name}")
        with self.engine.connect() as connection:
            results = connection.execute(query)
            records = results.fetchall()
        if convert_func:
            return [convert_func(*record) for record in records]
        return records
    
    def execute_query(self, query):
        """
        Exécute une requête SQL.

        Parameters
        ----------
        query : str
            La requête SQL à exécuter.
        """
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text(query))
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                print(f"Erreur lors de l'exécution de la requête: {e}")
                raise
    
    def search_record(self, table_name, field, query, convert_func=None):
        """
        Recherche un enregistrement dans la table.

        Parameters
        ----------
        table_name : str
            Le nom de la table.
        where_clause : str
            La clause WHERE pour spécifier quel enregistrement rechercher.
        convert_func : function, optional
            Fonction pour convertir les données brutes en objets spécifiques.
        
        Returns
        -------
        list
            Une liste d'enregistrements ou d'objets convertis.
        """
        query = text(f"SELECT * FROM {table_name} WHERE {field} LIKE '%{query}%'")
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                results = connection.execute(query)
                records = results.fetchall()
                transaction.commit()
            except Exception as e:
                transaction.rollback()
                print(f"Erreur lors de la recherche: {e}")

        return records

    def get_session(self):
        """
        Retourne la session SQLAlchemy.

        Returns
        -------
        session : Session
            La session SQLAlchemy.
        """
        return self.session