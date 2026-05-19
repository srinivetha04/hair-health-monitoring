from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import base64
import os
import random

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- MYSQL CONFIG ----------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'hair_db'

mysql = MySQL(app)

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = os.path.join("static", "uploads")
IMAGE_FOLDER = os.path.join("static", "images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------------- ROUTES ----------------

@app.route('/')
def welcome():
    return render_template('welcome.html')


# 🔥 LOGIN WITH DB SAVE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        session["username"] = username

        cur = mysql.connection.cursor()

        # check user exists
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        # insert if new
        if not user:
            cur.execute("INSERT INTO users (username) VALUES (%s)", (username,))
            mysql.connection.commit()

        cur.close()

        return redirect('/dashboard')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if "username" not in session:
        return redirect("/login")
    return render_template('dashboard.html', name=session.get("username"))


@app.route('/scan')
def scan():
    if "username" not in session:
        return redirect("/login")
    return render_template('scan.html')


@app.route("/loading")
def loading():
    if "username" not in session:
        return redirect("/login")
    return render_template("loading.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    if "username" not in session:
        return redirect("/login")

    username = session.get("username")

    image_data = request.form.get("captured_image")
    upload_image = request.files.get("upload_image")

    # ---------------- IMAGE SAVE ----------------
    if image_data:
        image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)

        filename = f"result_{random.randint(1000,9999)}.png"
        file_path = os.path.join(IMAGE_FOLDER, filename)

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        result_image = "images/" + filename

    elif upload_image:
        filename = f"upload_{random.randint(1000,9999)}_{upload_image.filename}"
        file_path = os.path.join(IMAGE_FOLDER, filename)
        upload_image.save(file_path)

        result_image = "images/" + filename

    else:
        return "No Image Provided"

    # ---------------- SCORE LOGIC ----------------
    cur = mysql.connection.cursor()

    # 🔥 CHECK EXISTING USER SCORE
    cur.execute("""
        SELECT score, health_status 
        FROM results 
        WHERE username=%s 
        ORDER BY id DESC LIMIT 1
    """, (username,))

    existing = cur.fetchone()

    if existing:
        # ✅ SAME SCORE REUSE
        score = existing[0]
        health_status = existing[1]

        if health_status == "Weak Hair":
            issues = ["Scalp Visible", "Low Hair Density"]

        elif health_status == "Moderate Hair":
            issues = ["Hair Thinning", "Mild Hair Fall"]

        else:
            issues = ["No Major Issues"]

    else:
        # 🆕 NEW USER → GENERATE
        rand = random.randint(1, 100)

        if rand <= 40:
            score = random.randint(40, 60)
            health_status = "Weak Hair"
            issues = ["Scalp Visible", "Low Hair Density"]

        elif rand <= 75:
            score = random.randint(61, 80)
            health_status = "Moderate Hair"
            issues = ["Hair Thinning", "Mild Hair Fall"]

        else:
            score = random.randint(81, 90)
            health_status = "Healthy Hair"
            issues = ["No Major Issues"]

    # ---------------- SAVE NEW RECORD ----------------
    cur.execute("""
        INSERT INTO results (username, score, health_status, issues, image_path)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        username,
        score,
        health_status,
        ",".join(issues),
        result_image
    ))

    mysql.connection.commit()
    cur.close()

    # ---------------- SESSION ----------------
    session["score"] = score
    session["issues"] = issues
    session["health_status"] = health_status
    session["result_image"] = result_image

    return redirect("/loading")


# ---------------- RESULT PAGE ----------------

@app.route("/result")
def result():

    if "username" not in session:
        return redirect("/login")

    username = session.get("username")
    result_image = session.get("result_image")
    score = session.get("score")
    issues = session.get("issues")
    health_status = session.get("health_status")

    # SOLUTIONS
    if health_status == "Weak Hair":
        natural = ["Onion Juice", "Castor Oil", "Aloe Vera"]
        chemical = ["Anti Hair Fall Shampoo", "Hair Growth Serum"]
        diet = ["Eggs", "Spinach", "Almonds"]

    elif health_status == "Moderate Hair":
        natural = ["Coconut Oil", "Fenugreek Pack"]
        chemical = ["Mild Shampoo", "Conditioner"]
        diet = ["Fruits", "Milk", "Vegetables"]

    else:
        natural = ["Weekly Oil Care"]
        chemical = ["Regular Shampoo"]
        diet = ["Balanced Diet", "Protein Foods"]

    return render_template(
        "result.html",
        score=score,
        issues=issues,
        health_status=health_status,
        natural=natural,
        chemical=chemical,
        diet=diet,
        result_image=result_image,
        username=username
    )


@app.route("/chemical")
def chemical():
    return render_template("chemical.html")


@app.route("/natural")
def natural():
    return render_template("natural.html")


@app.route("/diet")
def diet():
    return render_template("diet.html")


# ---------------- NO CACHE ----------------
@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response


if __name__ == "__main__":
    app.run(debug=True)