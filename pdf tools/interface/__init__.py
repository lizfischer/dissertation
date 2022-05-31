from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER="interface/static/projects",
    VIEW_UPLOAD_FOLDER="/static/projects",
    ALLOWED_EXTENSIONS={'pdf'},
    SECRET_KEY='192bkturyfd22ab9ewa43d1234bawes36c78afcb9a393ec15f71987wa3w4y764727823bca'
)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db?check_same_thread=False'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from interface import routes

if __name__ == "__main__":
    app.run()
