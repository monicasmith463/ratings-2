"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session, jsonify)

from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")

@app.route("/register", methods=["GET"])
def show_register():
    """Show registration form."""

    return render_template("register.html")


@app.route("/register", methods=['POST'])
def register_user():
    """Register a new user."""
    
    email = request.form.get('user_email')
    password = request.form.get('password')

    query_db = db.session.query(User).filter_by(email=email).all()

    if query_db:
        flash("User email already in use")
        return redirect('/register')

    new_user = User(email=email, password=password)

    db.session.add(new_user)
    db.session.commit()

    flash("Sucessfully registered.")    
    return redirect("/")

    
@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    # print users
    return render_template("user_list.html", users=users)


@app.route('/users/<int:user_id>')
def user_details(user_id):
    """ Show user profile """

    user = User.query.filter_by(user_id=user_id).all()[0]
    # get list of ratings from user
    ratings = Rating.query.filter_by(user_id=user.user_id).all()

    movies = []

    for rating in ratings:
        score = rating.score
        movie = Movie.query.filter_by(movie_id=rating.movie_id).first()
        movies.append(tuple([movie.title, score, movie.movie_id]))

    return render_template("user_profile.html", user=user, movies=movies)


@app.route("/movies")
def movie_list():
    """Show list of movies"""

    movies = Movie.query.order_by(Movie.title).all()
    # print movies
    return render_template("movie_list.html", movies=movies)


@app.route('/movie/<int:movie_id>', methods=['GET'])
def movie_details(movie_id):
    """ Show page for a given movie"""

    movie = Movie.query.filter_by(movie_id=movie_id).first()
    ratings = Rating.query.filter_by(movie_id=movie_id).all()

    return render_template('movie_profile.html', movie=movie, ratings=ratings)


@app.route('/movie/<int:movie_id>', methods=['POST'])
def record_rating(movie_id):
    """Submit rating to database"""

    current_user = session.get('user')
    if current_user:
        user_rating = request.form.get('user-rating')
        check_rating = Rating.query.filter_by(movie_id=movie_id).first()

        if check_rating:
            check_rating.rating = user_rating
        else:
            db.session.add(Rating(user_id=current_user['user_id'], movie_id=movie_id, score=user_rating))
        db.session.commit()
            
    else:
        flash("Please log in to rate movies.")
    return redirect('/movies')


@app.route("/login", methods=['GET'])
def get_login_info():
    """Show user login form."""

    return render_template("login.html")


@app.route("/login", methods=['POST'])     
def log_user_in():
    """Login a user."""

    email = request.form.get('user_email')
    password = request.form.get('password')

    
    user_lookup = User.query.filter_by(email=email, password=password).all()[0]

    if user_lookup:
        flash("Successfully logged in. Welcome!")
        session['user'] = { 'email': email, 'user_id': user_lookup.user_id }
        user_id = user_lookup.user_id
        return redirect('/users/' + str(user_id))

    flash("Invalid username or password. Please try again.")
    return redirect('/login')


@app.route("/logout")
def log_user_out():
    """Log out a user."""

    if session.get('user'):
        del session['user']
        flash("Successfully Logged Out") 

    return redirect('/login')    
        









if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    # disable intercept redirects
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
