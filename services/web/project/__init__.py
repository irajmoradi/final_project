import os

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
psql_connection = "postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev"



class User(db.Model):
    __tablename__ = "users_b"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Store password in plaintext

    def __init__(self, email, password):
        self.email = email
        self.password = password



@app.route("/")
def hello_world():
    messages = [{}]
    sqlcommand = """
    SELECT text, created_at
    FROM tweets
    Ordered by created_at DESC
    Limit 20;
    """
    engine = sqlalchemy.create_engine(db_connection)
    connection = engine.connect()
    result = connection.execute(text(sql))

    # check if logged in correctly
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_credentials = are_credentials_good(username, password)
    print('good_credentials=', good_credentials)
    
    for message in result:
        messages.append({'text': message.text, 'created_at': message.created_at})
    connection.close()

    # render_template does preprocessing of the input html file;
    # technically, the input to the render_template function is in a language called jinja2
    # the output of render_template is html
    return render_template('root.html', logged_in=good_credentials, messages=messages)

def are_credentials_good(email, password):
    user = User.query.filter_by(email=email).first()
    if user and user.password == password:
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
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('create_user.html', error_message='Passwords do not match.')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('create_user.html', error_message='Email already in use.')

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template('create_user.html')

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
