
import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, lookup_by_id, lookup_by_stats

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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = sqlite3.connect("admissions.db")
cur_user_stats={}

@app.route("/rec", methods=["GET", "POST"])
@login_required
def rec():
    return render_template("rec.html", schools=lookup_by_stats(cur_user_stats))

@app.route('/save_school', methods=["GET", "POST"])
def save_school():
    if request.method == "POST":
        print ("Hello")
        print(request.form.get("school_id"))
        print(session["user_id"][0])
        db.execute("INSERT INTO saved_schools(user_id, school_id) VALUES (?,?)", (int(session["user_id"][0]), int(request.form.get("school_id"))))
        db.commit()
        return render_template("buy.html")

@app.route("/")
def index():
    session.clear()
    return render_template("homepage.html")

@app.route("/profile")
@login_required
def profile():
    cursor = db.execute("SELECT name, GPA, SATreading, SATmath, ACT FROM users WHERE id = ?", session["user_id"])
    user = cursor.fetchone()
    cursor2 = db.execute("SELECT school_id FROM saved_schools WHERE user_id = ?", session["user_id"])
    schools = cursor2.fetchall()
    school_list = []
    for school in schools:
        school_list.append(lookup_by_id(school))
    school_list_f = []
    for i in range(len(school_list)):
        school_list_f.append(school_list[i][0])
    sat_designation = {}
    act_designation = {}
    sat_chances = {}
    act_chances = {}
    sat = int(user[2]) + int(user[3])
    act = int(user[4])
    cur_user_stats['sat']=sat
    cur_user_stats["act"]=act
    for school in school_list_f:
        if sat:
            sat_upperpct = school.get("sat75thmath") + school.get("sat75thread")
            sat_lowerpct = school.get("sat25thmath") + school.get("sat25thread")
            if sat >= sat_upperpct:
                sat_designation[school.get("name")] = "Safer bet."

            if sat <= sat_lowerpct:
                sat_designation[school.get("name")] = "Reach."

            if sat < sat_upperpct and sat > sat_lowerpct:
                sat_designation[school.get("name")] = "Target."
            a = school.get("admission_rate")
            median = school.get("satmidptmath") + school.get("satmidptread")
            d = int(abs(sat - (median - 200))/100)
            constant = 0
            if sat >= (median - 200):
                for iteration in range(d):
                    iteration += 1
                    if iteration == 1:
                        constant = 1
                    else:
                        constant += (1/(2*(iteration-1)))
                acceptance_chance_sat = a + (a*.38095238)*constant
                if acceptance_chance_sat > 1:
                    acceptance_chance_sat = 1
                sat_chances[school.get("name")] = acceptance_chance_sat
            elif sat < (median - 200):
                for iteration in range(d):
                    iteration += 1
                    if iteration == 1:
                        constant = 1
                    else:
                        constant += (1/(2*(iteration-1)))
                acceptance_chance_sat = a - (a*.61345)*constant
                if acceptance_chance_sat < 0:
                    acceptance_chance_sat = 0
                sat_chances[school.get("name")] = acceptance_chance_sat
        if act:
            act_upperpct = school.get("act75thcum")
            act_lowerpct = school.get("act25thcum")
            if act > act_upperpct:
                act_designation[school.get("name")] = "Safer bet."

            if act < act_lowerpct:
                act_designation[school.get("name")] = "Reach."

            if act <= act_upperpct and act >= act_lowerpct:
                act_designation[school.get("name")] = "Target."
            a = school.get("admission_rate")
            median = school.get("actmidptcum")
            d = int(abs(act - (median - 7)))
            constant = 0
            if act >= (median - 7):
                for iteration in range(d):
                    iteration += 1
                    if iteration == 1:
                        constant = 1
                    else:
                        constant += ((3*(iteration-1))/(4*(iteration-1)))
                acceptance_chance_act = a + (a*.16)*constant
                if acceptance_chance_act > 1:
                    acceptance_chance_act = 1
                act_chances[school.get("name")] = acceptance_chance_act
            if act < (median - 7):
                for iteration in range(d):
                    constant += d*.69566
                acceptance_chance_act = a - (a*.132485)*constant
                if acceptance_chance_act < 0:
                    acceptance_chance_act = 0
                act_chances[school.get("name")] = acceptance_chance_act


    return render_template("profile.html", user = user, schools = school_list_f, sat_designation = sat_designation, act_designation = act_designation, sat_chances = sat_chances, act_chances = act_chances)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        print("POST SUCCESSFUL")
        # # Get symbol from form
        school = request.form.get("school")
        print("HEREREREER")
        print(school)
        return render_template("buy.html", schools=lookup(school))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html", schools=[])

@app.route("/athletic")
@login_required
def athletic():
    return render_template("athletic.html")

@app.route("/counselor")
@login_required
def counselor():
    return render_template("counselor.html")

@app.route("/help")
@login_required
def help():
    return render_template("help.html")

@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    if request.method == "POST":
        error = None

        if not request.form.get("GPA"):
            error = 'Must provide GPA.'
            return render_template('update.html', error=error)

        if request.form.get("SATreading"):
            if int(request.form.get("SATreading")) > 800 or int(request.form.get("SATreading")) < 200:
                error = 'Invalid SAT Reading score.'
                return render_template('update.html', error=error)
            if not request.form.get("SATmath"):
                error = 'Must enter SAT Math score.'
                return render_template('update.html', error=error)

        if request.form.get("SATmath"):
            if int(request.form.get("SATmath")) > 800 or int(request.form.get("SATmath")) < 200:
                error = 'Invalid SAT Math score.'
                return render_template('update.html', error=error)
            if not request.form.get("SATreading"):
                error = 'Must enter SAT Reading score.'
                return render_template('update.html', error=error)

        if request.form.get("ACT"):
            if int(request.form.get("ACT")) > 36 or int(request.form.get("ACT")) < 1:
                rerror = 'Invalid ACT score'
                return render_template('update.html', error=error)

        if float(request.form.get("GPA")) > 5 or float(request.form.get("GPA")) < 0:
                error = 'Invalid GPA.'
                return render_template('update.html', error=error)

        satr = request.form.get("SATreading")
        satm = request.form.get("SATmath")
        act = request.form.get("ACT")
        gpa = request.form.get("GPA")
        if not satr and not act:
            print(type(gpa))
            db.execute("UPDATE users SET GPA = ? WHERE id = ?", (gpa, session["user_id"][0]))
        elif not satr:
            db.execute("UPDATE users SET GPA = ?, ACT = ? WHERE id = ?", (gpa, act, int(session["user_id"][0])))
        elif not act:
            db.execute("UPDATE users SET GPA = ?, SATreading = ?, SATmath = ? WHERE id = ?", (gpa, satr, satm, int(session["user_id"][0])))
        else:
            db.execute("UPDATE users SET GPA = ?, SATreading = ?, SATmath = ?, ACT = ? WHERE id = ?", (gpa, satr, satm, act, int(session["user_id"][0])))

        db.commit()
        # Redirect user to home page
        return redirect("/profile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("update.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        error = None

        # Ensure username was submitted
        if not request.form.get("username"):
            error = 'Must provide username.'
            return render_template('login.html', error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = 'Must provide password.'
            return render_template('login.html', error=error)

        # Query database for username
        pass_hash = db.execute("SELECT hash FROM users WHERE username = ?", [request.form.get("username")])
        user_id = db.execute("SELECT id FROM users WHERE username = ?", [request.form.get("username")])
        check = pass_hash.fetchone()
        session_id = user_id.fetchone()
        # Ensure username exists and password is correct
        if not check:
            error = 'Invalid username.'
            return render_template('login.html', error=error)

        if not check_password_hash(check[0], request.form.get("password")):
            error = 'Invalid password.'
            return render_template('login.html', error=error)

        # Remember which user has logged in
        session["user_id"] = session_id

        # Redirect user to home page
        return redirect("/profile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = 'Must provide username.'
            return render_template('register.html', error=error)

        # Ensure email was submitted
        elif not request.form.get("email"):
            error = 'Must provide email.'
            return render_template('register.html', error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = 'Must provide password.'
            return render_template('register.html', error=error)

        # Ensure password was submitted
        elif not request.form.get("name"):
            error = 'Must provide name.'
            return render_template('register.html', error=error)

        # Ensure password was submitted
        elif not request.form.get("GPA"):
            error = 'Must provide GPA.'
            return render_template('register.html', error=error)

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            error = 'Must provide password confirmation.'
            return render_template('register.html', error=error)

        if request.form.get("SATreading"):
            if int(request.form.get("SATreading")) > 800 or int(request.form.get("SATreading")) < 200:
                error = 'Invalid SAT Reading score.'
                return render_template('register.html', error=error)
            if not request.form.get("SATmath"):
                error = 'Must enter SAT Math score.'
                return render_template('register.html', error=error)

        if request.form.get("SATmath"):
            if int(request.form.get("SATmath")) > 800 or int(request.form.get("SATmath")) < 200:
                error = 'Invalid SAT Math score.'
                return render_template('register.html', error=error)
            if not request.form.get("SATreading"):
                error = 'Must enter SAT Reading score.'
                return render_template('register.html', error=error)

        if request.form.get("ACT"):
            if int(request.form.get("ACT")) > 36 or int(request.form.get("ACT")) < 1:
                rerror = 'Invalid ACT score'
                return render_template('register.html', error=error)

        if float(request.form.get("GPA")) > 5 or float(request.form.get("GPA")) < 0:
                error = 'Invalid GPA.'
                return render_template('register.html', error=error)

        # checks that passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            error = 'Passwords do not match.'
            return render_template('register.html', error=error)

        rows = db.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")])
        if rows.fetchone():
            error = 'Username already taken.'
            return render_template('register.html', error=error)

        password = generate_password_hash(request.form.get("password"))
        username = request.form.get("username")
        email = request.form.get("email")
        name = request.form.get("name")
        satr = request.form.get("SATreading")
        satm = request.form.get("SATmath")
        act = request.form.get("ACT")
        gpa = request.form.get("GPA")
        if not satr and not act:
            session["user_id"] = db.execute("INSERT INTO users(username,hash,email,name,GPA) VALUES (?,?,?,?,?)", (username, password, email, name, gpa))
        elif not satr:
            session["user_id"] = db.execute("INSERT INTO users(username,hash,email,name,ACT,GPA) VALUES (?,?,?,?,?,?)", (username, password, email, name, act, gpa))
        elif not act:
            session["user_id"] = db.execute("INSERT INTO users(username,hash,email,name,SATreading,SATmath,GPA) VALUES (?,?,?,?,?,?,?)", (username, password, email, name, satr, satm, gpa))
        else:
            session["user_id"] = db.execute("INSERT INTO users(username,hash,email,name,SATreading,SATmath,ACT,GPA) VALUES (?,?,?,?,?,?,?,?)", (username, password, email, name, satr, satm, act, gpa))
        db.commit()
        session.clear()


        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
