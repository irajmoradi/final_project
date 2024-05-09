import os
from sqlalchemy import text
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    render_template,
    make_response,
    url_for,
    redirect,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy
app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)
psql_connection = "postgresql://hello_flask:hello_flask@db:5432/hello_flask_prod"



class User(db.Model):
    __tablename__ = "users_b"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Store password in plaintext

    def __init__(self, email, password):
        self.email = email
        self.password = password


@app.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    messages_per_page = 20
    offset = (page - 1) * messages_per_page
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_credentials = are_credentials_good(username, password)

    if query:
        sqlcommand = """
        SELECT u.screen_name, t.text, ts_headline('english', t.text, plainto_tsquery(:query)) AS highlighted_text, t.created_at
        FROM tweets t
        JOIN users u ON t.id_users = u.id_users
        WHERE to_tsvector('english', t.text) @@ plainto_tsquery(:query)
        ORDER BY ts_rank_cd(to_tsvector('english', t.text), plainto_tsquery(:query)) DESC
        LIMIT :limit OFFSET :offset;
        """
        engine = sqlalchemy.create_engine(psql_connection)
        connection = engine.connect()
        result = connection.execute(text(sqlcommand), {'query': query, 'limit': messages_per_page, 'offset': offset}).fetchall()
        connection.close()

        messages = []
        for row in result:
            highlighted_text = row[2]
            highlighted_text = highlighted_text.replace('<b>', '<span class="highlighted">')
            highlighted_text = highlighted_text.replace('</b>', '</span>')
            messages.append({'text': row[1], 'created_at': row[3], 'screen_name': row[0], 'highlighted_text': highlighted_text})
    else:
        messages = []

    return render_template('search.html', logged_in=good_credentials, messages=messages, query=query, page=page)

@app.route("/")
def hello_world():
    page = request.args.get('page', 1, type=int)
    messages_per_page = 20
    offset = (page - 1) * messages_per_page

    sqlcommand = """
    SELECT t.text, t.created_at, u.screen_name
    FROM tweets t
    JOIN users u ON t.id_users = u.id_users
    ORDER BY t.created_at DESC, id_tweets
    LIMIT :limit OFFSET :offset;
    """
    engine = sqlalchemy.create_engine(psql_connection)
    connection = engine.connect()
    result = connection.execute(text(sqlcommand), {'limit': messages_per_page, 'offset': offset}).fetchall()
    connection.close()


    messages = [{'text': msg[0], 'created_at': msg[1], 'screen_name': msg[2]} for msg in result]

    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_credentials = are_credentials_good(username, password)

    return render_template('root.html', logged_in=good_credentials, messages=messages, page=page)


def are_credentials_good(email, password):
    engine = sqlalchemy.create_engine(psql_connection)
    with engine.connect() as connection:
        # Prepare and execute the SQL command
        sqlcommand = "SELECT password FROM users WHERE screen_name = :email"
        result = connection.execute(text(sqlcommand), {'email': email}).fetchone()

        # Check if the user was found and the password matches
        if result and result[0] == password:
            return True
    return False
@app.route('/login', methods=['GET', 'POST'])
def login():
    # requests (plural) library for downloading;
    # now we need request singular 
    username = request.form.get('username')
    password = request.form.get('password')

    good_credentials = are_credentials_good(username, password)

    # the first time we've visited, no form submission
    if username is None:
        return render_template('login.html', bad_credentials=False)

    # they submitted a form; we're on the POST method
    else:
        if not good_credentials:
            return render_template('login.html', bad_credentials=True)
        else:
            # if we get here, then we're logged in
            #return 'login successful'

            # create a cookie that contains the username/password info

            template = render_template(
                'login.html', 
                bad_credentials=False,
                logged_in=True)
            #return template
            response = make_response(template)
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response


@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('create_user.html', error_message='Passwords do not match.')

        engine = sqlalchemy.create_engine(psql_connection)
        with engine.begin() as connection:  # Start a transaction
            # Check if the email is already in use
            sqlcommand = "SELECT count(*) FROM users WHERE screen_name = :username"
            result = connection.execute(text(sqlcommand), {'username': email}).scalar()
            if result > 0:
                return render_template('create_user.html', error_message='User Name already in use.')

            # Insert the new user if the email is not in use
            sqlcommand = "INSERT INTO users (screen_name, password) VALUES (:screen_name, :password)"
            connection.execute(text(sqlcommand), {'screen_name': email, 'password': password})

        return redirect(url_for('login'))
    return render_template('create_user.html')


@app.route('/create_message', methods=['GET', 'POST'])
def create_message():
    engine = sqlalchemy.create_engine(psql_connection)
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_credentials = are_credentials_good(username, password)
    if request.method == 'POST':
        message_text = request.form['text']
        username = request.cookies.get('username')  # Fetch username from cookies
        with engine.begin() as connection:  # Automatic transaction management
            # Fetch user ID from the users table based on the username (screen_name)
            user_id_result = connection.execute(
                text("SELECT id_users FROM users WHERE screen_name = :username"),
                {'username': username}
            ).fetchone()

            if not user_id_result:
                return "User not found", 404  # Or handle appropriately

            user_id = user_id_result[0]
            created_at = datetime.now()

            # SQL to insert the new tweet
            connection.execute(
                text("INSERT INTO tweets (id_users, text, created_at) VALUES (:id_users, :text, :created_at)"),
                {'id_users': user_id, 'text': message_text, 'created_at': created_at}
            )

        return redirect(url_for('hello_world'))  # Redirect to home page to see all tweets

    return render_template('create_message.html', logged_in = good_credentials)

@app.route('/logout')
def logout():
    # Clear the cookies by setting them to expire immediately
    resp = make_response(redirect(url_for('login')))  # Redirect within the response
    resp.set_cookie('username', '', expires=0)       # Clear the username cookie
    resp.set_cookie('password', '', expires=0)       # Clear the password cookie
    return resp  # Return the modified response that redirects and clears cookies

@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["MEDIA_FOLDER"], filename))
    return """
    <!doctype html>
    <title>upload new File</title>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file><input type=submit value=Upload>
    </form>
    """
