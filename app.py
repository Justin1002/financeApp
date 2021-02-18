import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    overalltotal = 0
    # get symbols
    symbols = db.execute("SELECT symbol FROM stocks WHERE user_id = :user_id GROUP BY symbol;", user_id=user_id)

    if symbols != []:

        stocks = []
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id)

        for symbol in symbols:
            symbol_data = lookup(symbol['symbol'])
            stock_shares = db.execute("SELECT SUM(shares) FROM stocks WHERE user_id = :user_id AND symbol = :symbol" ,
                                        user_id=user_id, symbol = symbol_data['symbol'])
            if stock_shares[0]['SUM(shares)'] == 0:
                continue
            else:
                stock_info = {}

                stock_info['name'] = symbol_data['name']
                stock_info['symbol'] = symbol_data['symbol']
                stock_info['price'] = symbol_data['price']
                stock_info['shares'] = stock_shares[0]['SUM(shares)']
                stock_info['total'] = stock_info['shares'] * stock_info['price']

                stocks.append(stock_info)

        for i in range(len(stocks)):
            overalltotal += stocks[i]['total']
            overalltotal += cash[0]['cash']

        for i in range(len(stocks)):
            stocks[i]['price'] = usd(stocks[i]['price'])
            stocks[i]['total'] = usd(stocks[i]['total'])

        return render_template("index.html", stocks=stocks, cash = usd(cash[0]['cash']), overalltotal = usd(overalltotal))

    else:
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id)
        return render_template("index.html",cash = usd(cash[0]['cash']), overalltotal = usd(cash[0]['cash']))



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        #ensure symbol/quantity submitted

        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("No symbol/shares submitted", 400)

        #shares quantity less than one

        if int(request.form.get("shares")) <= 0:
            return apology("Cannot buy negative/zero shares", 400)

        symbol = request.form.get("symbol").upper()
        quantity = request.form.get("shares")
        user_id = session["user_id"]

        #stock look up

        stock = lookup(symbol)

        #symbol exists?

        if stock == None:
            return apology("Symbol not found", 400)

        #calculate total price

        t_price = float(stock["price"]) * float(quantity)

        user = db.execute("SELECT * FROM users WHERE id =:id",  id= user_id)
        cash = float(user[0]["cash"])

        #check if user has enough money

        if cash < t_price:
            return apology("not enough funds", 400)

        remaining_funds = cash - t_price

        db.execute("INSERT INTO stocks (user_id, symbol, shares, price) VALUES (:user_id, :symbol, :shares, :price)",
                     user_id = user_id, symbol = symbol, shares = quantity, price = stock["price"])


        #change available funds

        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash = remaining_funds, id = user_id)

        flash("Bought!")
        return redirect(url_for('index'))

    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    historical = db.execute("SELECT * FROM stocks where user_id = :user_id ORDER BY date DESC", user_id = user_id)

    return render_template("history.html", historical = historical)

    ##return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method =="POST":

        stockSym = request.form.get("symbol")
        info = lookup(stockSym)

        if info == None:
            return apology("INVALID SYMBOL", 400)

        return render_template("quoted.html", info=info)

    else:
        return render_template("quote.html")

    ##return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method =="POST":

        #Ensure username field is submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        #Ensure password field is submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        #ensure confirmation field is submitted
        if not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        #If passwords do not match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match.", 400)

        #hash the password
        pw = request.form.get("password")
        hash = generate_password_hash(pw)
        username = request.form.get("username")

        #unique username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) == 1:
            return apology("username taken", 400)

        else:
            newuserid = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=hash)

        #store session ID
        session["user_id"] = newuserid

        #flash message registration
        flash("Registration successful!")
        return redirect(url_for('index'))

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

    #ensure symbol/quantity submitted

        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("No symbol/shares submitted", 400)

        #shares quantity less than one

        if int(request.form.get("shares")) <= 0:
            return apology("Cannot sell negative/zero shares", 400)


        symbol = request.form.get("symbol").upper()
        quantity = int(request.form.get("shares"))
        user_id = session["user_id"]

        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = user_id)

        #stock look up

        stock = lookup(symbol)

        #symbol exists?

        if stock == None:
            return apology("Symbol not found", 400)

        #Does user own the stock?
        availablestock = db.execute("SELECT SUM(shares) from stocks WHERE user_id = :user_id AND symbol = :symbol;", user_id=user_id, symbol = symbol)

        if not availablestock[0]['SUM(shares)']:
            return apology("you don't own this stock", 400)

        if quantity > availablestock[0]['SUM(shares)']:
            return apology("you don't own that many stocks")

        #Enter new transaction

        db.execute("INSERT into stocks (symbol, shares, price, user_id) VALUES (:symbol, :quantity, :price, :user_id)",
                    symbol = symbol, quantity= -quantity, price = stock['price'], user_id = user_id)

        #change available funds
        newFunds = cash[0]['cash'] + quantity * stock['price']

        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash = newFunds, id = user_id)

        flash("Sold!")
        return redirect(url_for('index'))

    else:
        return render_template("sell.html")


@app.route("/account", methods = ["GET", "POST"])
@login_required

def account():
    #Change passwords
    if request.method == "POST":
        user_id = session["user_id"]
        PW = db.execute("SELECT hash from users WHERE id = :user_id", user_id = user_id)
        hashedPW = generate_password_hash(request.form.get("new password"))


        #password field is empty
        if not request.form.get("password"):
            return apology("Please enter your old password")

        #new password or confirmation field is empty

        if not request.form.get("new password") or not request.form.get("confirm"):
            return apology("Please enter new/confirmed password")

        #password is incorrect
        if not check_password_hash(PW[0]['hash'], request.form.get("password")):
            return apology("Current password is incorrect")

        #new passwords do not match
        if request.form.get("new password") != request.form.get("confirm"):
            return apology("Password confirmation does not match")

        #change password if above conditions are OK
        db.execute("UPDATE users SET hash = :newhash WHERE id = :user_id", newhash = hashedPW, user_id = user_id)
        flash("Password updated!")
        return redirect(url_for('index'))

    else:
        userName = db.execute("SELECT username FROM users WHERE id = :user_id", user_id = session["user_id"])
        return render_template("account.html",username=userName[0]['username'])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
