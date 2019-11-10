from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    symbols = db.execute(
        'SELECT symbol from trans WHERE id=:user_id', user_id=session['user_id'])
    shares = db.execute(
        'SELECT quantity from trans WHERE id=:user_id', user_id=session['user_id'])
    prices = db.execute(
        'SELECT price from trans  WHERE id=:user_id', user_id=session['user_id'])
    total_value = 0
    cash_total = db.execute('SELECT cash from users')
    grand_total = 0
    return redirect(url_for('transact'))


@app.route("/transact", methods=["GET", "POST"])
@login_required
def transact():
    if request.method == 'POST':
        try:
            stock = lookup(request.form.get('stocksymbol'))
            shares = int(request.form.get('shares'))
        except:
            return apology('INVALID SYMBOL OR NOT ENOUGH AVAILABLE SHARES')

        cash = db.execute(
            'SELECT cash from users WHERE id=:user_id', user_id=session['user_id'])
        if cash >= shares*stock['price']:
            db.execute('INSERT INTO trans VALUES(:symbol,:shares,:price)',
                       symbol=stock['name'], shares=shares, price=stock['price'])
            db.execute('UPDATE users SET cash=(cash-:paid) WHERE ID=1',
                       paid=shares*stock['price'])
            return render_template('index.html')
    else:
        return render_template('transact.html')


@app.route("/test")
def test():
    return render_template('test.html')




@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/index", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == 'POST':
        stockdict = lookup(request.form.get('stocksymbol'))
        return render_template('displaystock.html')
    else:
        return render_template('index.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form.get('username') == "" or request.form.get('password') == "":
            return apology("Blank username or password")
        if request.form.get('password-confirmation') != request.form.get('password'):
            return apology("passwords mismatch")
        password_hash = pwd_context.encrypt(request.form.get('password'))
        db.execute("INSERT INTO users(username,hash) VALUES(:username,:hash)",
                   username=request.form.get('username'), hash=password_hash)
        return redirect(url_for("index"))
    else:
        return render_template('register.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
