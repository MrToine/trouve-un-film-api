import argparse
from flask_migrate import Migrate
from flask import current_app
from app import create_app
from app.database import db
from app.models import Participant, User, Movie, Genre, Like, Post
from app.models.relations import MovieGenre, MovieParticipant

def init_migrations(app):
    with app.app_context():
        from flask_migrate import init
        init(directory='migrations')
    print("Migrations initialized.")

def create_new_migration(app):
    with app.app_context():
        from flask_migrate import revision
        revision(autogenerate=True, message="Automatic migration")
    print("New migration created.")

def upgrade_db(app):
    with app.app_context():
        from flask_migrate import upgrade
        upgrade()
    print("Database upgraded.")

def downgrade_db(app):
    with app.app_context():
        from flask_migrate import downgrade
        downgrade()
    print("Database downgraded.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manage database migrations")
    parser.add_argument('action', choices=['init', 'migrate', 'upgrade', 'downgrade', 'all'],
                        help="Action to perform")
    args = parser.parse_args()

    app = create_app()
    migrate = Migrate(app, db)

    if args.action == 'init' or args.action == 'all':
        init_migrations(app)
    if args.action == 'migrate' or args.action == 'all':
        create_new_migration(app)
    if args.action == 'upgrade' or args.action == 'all':
        upgrade_db(app)
    if args.action == 'downgrade':
        downgrade_db(app)

print("Migration actions completed.")
