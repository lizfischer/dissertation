from flask import Flask


app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER = 'projects',
    ALLOWED_EXTENSIONS = {'pdf'},
    SECRET_KEY='192bkturyfd22ab9ewa43d1234bawes36c78afcb9a393ec15f71987wa3w4y764727823bca'
)

from interface import routes

if __name__ == "__main__":
    app.run()
