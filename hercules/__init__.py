import os
import sqlite3
import calendar

from flask import Flask, render_template, request, session, url_for, redirect, flash
from datetime import datetime
from passlib.hash import md5_crypt
from sqlite3 import OperationalError

from util import dbCommands as db


app = Flask(__name__)

app.secret_key = "\x16\xc6w\x1c.!-\xb5\x15\x82u\xbe\x01\xc5?[\x18\n~\x891_\xa3\x9a}\xe6\x13\xea~\xc1\x92\xb8"

curr_hr = datetime.now().hour
curr_min = datetime.now().minute
curr_sec = datetime.now().second

def is_logged_in():
    return "id" in session

@app.route("/")
def welcome():
    if(is_logged_in()):
        redirect(url_for("home"))
    return render_template("welcome.html")

@app.route("/login", methods = ["POST", "GET"])
def home():
    if( is_logged_in() ):
        userId = session["id"]
        day = datetime.now().day
        month = datetime.now().month
        month_name = calendar.month_abbr[month]
        year = datetime.now().year
        date = str(day) + "-" + month_name + "-" + str(year)
        template_stored = db.get_template_from_date(userId, date)
        if template_stored:
            template = db.get_template(userId, template_stored)
            print("template_stored", template)
            return render_template("home.html", task = template, month=month_name, date=day, year=year)
        else:
            flash("No template stored for " + date)
            return render_template("home.html")
    else:
        return render_template("login.html")


@app.route("/auth" , methods = ["POST"])
def authenticate():
    '''Checks if the username and password entered match what's on file'''
    user_data = db.get_all_user_data()
    username = request.form.get("username")
    password = request.form.get("password")
    session["username"] = username
    if username in user_data:
        if md5_crypt.verify(password, user_data[username]):
            id = db.get_user_id(username)
            session["id"] = id
        else:
            flash("Invalid password, try again!")
    else:
        flash("Invalid username, try again!")
    return redirect(url_for('home'))

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/registerAuth", methods = ["POST"])
def reg_auth():
    user_data = db.get_all_user_data()
    username = request.form.get("username")
    password = request.form.get("password")
    password2 = request.form.get("password2")
    if username in user_data:
        flash("Username already exists! Please pick another one!")
        return redirect(url_for("register"))
    elif len(username) < 4:
        flash("Username has to be at least 4 characters!")
        return redirect(url_for("register"))
    elif password != password2:
        flash("Input Same Password in Both Fields!")
        return redirect(url_for("register"))
    else:
        db.add_user(username, md5_crypt.encrypt(password))
        flash("Successfully Registered, Now Sign In!")
        return redirect(url_for('home'))


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("id")
    return redirect(url_for("welcome"))

@app.route("/add_to_cal", methods=["POST","GET"])
def add_to_cal():
    if( is_logged_in() ):
        userId=session["id"]
        print(request.form)
        name = request.form["tempname"]
        dates = request.form.getlist("selected")
        dates = dates[0].split(",")
        print("LENGTHHH:", len(dates))
        counter = 0
        while counter < len(dates):
            print("adding ", dates[counter])
            db.add_Calender(userId, dates[counter], name)
            print("added")
            counter += 1
        return redirect(url_for("home"))
    else:
        return render_template("login.html")


#called when you submit a template
@app.route("/calendar",methods=["POST","GET"])
def cal():
    if( is_logged_in() ):
        userId=session["id"]
        listotemps = []
        curr_month = datetime.now().month
        curr_year = datetime.now().year
        curr_table = calendar.monthcalendar(curr_year, curr_month)
        month_name = calendar.month_abbr[curr_month]
        curr_year = str(curr_year)
        nameDict = {}
        for row in curr_table:
            for day in row:
                date = str(day) + "-" + month_name + "-" + curr_year
                print(date)
                if (db.get_template_from_date(userId,date)):
                    nameDict[date] = db.get_template_from_date(userId,date)
        print("namedict:")
        print(nameDict)

        if request.method == 'POST':
            try:
                userId=session["id"]
                name = request.form["tempname"]
                task = request.form.getlist("task[]")
                start = request.form.getlist("start[]")
                end = request.form.getlist("end[]")
                counter = 0
                count = 0
                tempNames = db.get_all_templates(userId)
                if len(task)==0 or len(start) == 0 or len(end) == 0:
                    flash("Missing start time, end time or task name")
                    return redirect(url_for("create"))
                while count < len(tempNames):
                    tempNames[count] = str(tempNames[count])[2:len(str(tempNames[count]))-3]
                    count +=1
                    print(tempNames)
                if name in tempNames:
                    flash("template name already in use")
                    return redirect(url_for("create"))
                while counter < len(start):
                    if start[0] > end[0]:
                        flash("Start time can't be after end time!")
                        return redirect(url_for("create"))
                    counter +=1
                tempS = start.copy()
                tempS.sort()
                tempE = end.copy()
                tempE.sort()
                print(start)
                print(tempS)
                if (start != tempS):
                    flash("Please sort your tasks in ascending order")
                    return redirect(url_for("create"))
                counter = 0
                while counter < len(tempE) -1:
                    if end[counter] > start[counter+1]:
                        flash("Tasks can't overlap!")
                        return redirect(url_for("create"))
                    counter +=1
                counter = 0
                lists = []
                print("ADDING TO TEMPLATES")
                while counter < len(task):
                    lists.append([userId, name, task[counter], start[counter], end[counter]])
                    counter += 1
                db.add_All_to_template(lists)
                dates = request.form.getlist("selected")
                return render_template("formcalendar.html", month=month_name,year=curr_year,table=curr_table,template = name,dict = nameDict)
            except:
                name = request.form["template"]
                return render_template("formcalendar.html", month=month_name,year=curr_year,table=curr_table,template = name,dict = nameDict)

        #when you click on the calendar tab
        return render_template("calendar.html", month = month_name, year = curr_year, table = curr_table, dict = nameDict)
    else:
        return render_template("login.html")


@app.route("/templates", methods=["POST", "GET"])
def templates():
    if( is_logged_in() ):
        userId=session["id"]
        names = db.get_all_templates(userId)
        counter = 0
        while counter < len(names):
            names[counter]=str(names[counter])[2:len(str(names[counter]))-3]
            counter +=1
        return render_template("template.html",templates=names)
    else:
        return render_template("login.html")


@app.route("/create",methods=["POST","GET"])
def create():
    if( is_logged_in() ):
        if request.method == 'POST':   
            userId=session["id"]
            template_name = request.form.get("name")
            template = db.get_template(userId, template_name)
            return render_template("create.html", task= template, name=template_name)
        return render_template("create.html")
    else:
        return render_template("login.html")


@app.route("/disp_temp", methods=["POST", "GET"])
def disp_temp():
    if( is_logged_in() ):
        userId=session["id"]
        if request.method == 'POST':
            template_name = request.form.get("selected")
            template = db.get_template(userId, template_name)
            print(template)
        return render_template("tempcalendar.html", task=template, name=template_name)
    else:
        return render_template("login.html")

if __name__ == "__main__":
    app.debug = True
    app.run()
