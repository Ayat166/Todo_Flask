from flask import (
    redirect,
    render_template,
    request,
    session,
    url_for,
    flash,
    jsonify,
    make_response,
)
from application import app, db
from .forms import ToDoForm, RegisterForm, LoginForm
from datetime import datetime
from bson import ObjectId
from flask_jwt_extended import (
    decode_token,
    jwt_required,
    create_access_token,
    JWTManager,
)
from werkzeug.security import generate_password_hash, check_password_hash
import traceback

# db is the database we are working with and todo_flask is the collection name for todos
# api register and login routes
@app.route("/api/register", methods=["POST"])
def register_api():
    try:
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not password or not email:
            return (
                jsonify({"message": "Username and password and email are required!"}),
                400,
            )
        if db.users.find_one({"username": username}):
            return jsonify({"message": "Username already exists!"}), 400
        if db.users.find_one({"email": email}):
            return jsonify({"message": "Email already exists!"}), 400

        hashed_password = generate_password_hash(password)
        db.users.insert_one(
            {"username": username, "email": email, "password": hashed_password}
        )
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        print(traceback.format_exc(), e)
        return jsonify({"message": "An error occurred!"})


@app.route("/api/login", methods=["POST"])
def login_api():
    try:
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username and not email:
            return jsonify({"message": "Username or email is required!"}), 400
        if not password:
            return jsonify({"message": "Password is required!"}), 400
        if username:
            user = db.users.find_one({"username": username})
        else:
            user = db.users.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return jsonify({"message": "Invalid credentials!"}), 401
        access_token = create_access_token(identity={"username": user["username"]})
        return (
            jsonify(token=access_token, email=user["email"], username=user["username"]),
            200,
        )
    except Exception as e:
        print(traceback.format_exc(), e)
        return jsonify({"message": "An error occurred!"})


# register for flask app
@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        if request.method == "POST":
            form = RegisterForm(request.form)
            if form.validate_on_submit():
                username = form.username.data
                email = form.email.data
                password = form.password.data
                confirm_password = form.confirm_password.data
                if password != confirm_password:
                    flash("Passwords do not match!", "danger")
                    return redirect(url_for("register"))
                if db.users.find_one({"username": username}):
                    flash("Username already exists!", "danger")
                    return redirect(url_for("register"))
                if db.users.find_one({"email": email}):
                    flash("Email already exists!", "danger")
                    return redirect(url_for("register"))
                db.users.insert_one(
                    {
                        "username": username,
                        "email": email,
                        "password": password,
                    }
                )
                flash("User registered successfully!", "success")
                return redirect(url_for("login"))
        else:
            form = RegisterForm()
        return render_template("register.html", title="Register", form=form)
    except Exception as e:
        print(traceback.format_exc(), e)
        flash("An error occurred during registration", "danger")
        return redirect(url_for("register"))


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            form = LoginForm(request.form)
            if form.validate_on_submit():
                username = request.form["username"]
                password = request.form["password"]
                user = db.users.find_one({"username": username})
                if not username and not password:
                    flash("Username or email is required!", "danger")
                    return redirect(url_for("login"))
                if user and check_password_hash(user["password"], password):
                    access_token = create_access_token(
                        identity={"username": user["username"]}
                    )
                    # Set the JWT token in the session
                    session["token"] = access_token
                    flash("Login successful!", "success")
                    return redirect(url_for("index"))
                else:
                    flash("Invalid username or password", "danger")
        form = LoginForm()
        return render_template("login.html", title="Login", form=form)
    except Exception as e:
        print(traceback.format_exc(), e)
        flash("An error occurred during login", "danger")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # Remove the JWT token from the session
    session.pop("token", None)
    # you can also invalidate the token on the server side if needed

    flash("Logout successful!", "success")
    return redirect(url_for("index"))


def get_current_user():
    """Helper to decode token and return user"""
    if "token" not in session:

        return None
    try:
        decoded_token = decode_token(session["token"])
        identity = decoded_token.get("sub")
        if not identity:
            return None
        return db.users.find_one({"username": identity["username"]})
    except Exception as e:
        print("Token decode failed:", e)
        return None


@app.route("/")
def index():
    todos = []
    user = get_current_user()
    if user:
        for todo in db.todo_flask.find({"user_id": user["_id"]}):
            todos.append(
                {
                    "id": str(todo["_id"]),
                    "name": todo["name"],
                    "description": todo["description"],
                    "completed": todo["completed"],
                    "created_at": todo["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return render_template("view_todos.html", title="Home", todos=todos)


@app.route("/add_todo", methods=["GET", "POST"])
def add_todo():
    user = get_current_user()
    if not user:
        flash("You need to be logged in to add a todo!", "danger")
        return redirect(url_for("login"))

    form = ToDoForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        db.todo_flask.insert_one(
            {
                "name": form.name.data,
                "description": form.description.data,
                "completed": form.completed.data,
                "user_id": user["_id"],
                "created_at": datetime.utcnow(),
            }
        )
        flash("Todo added successfully!", "success")
        return redirect(url_for("index"))
    return render_template("add_todo.html", title="Add Todo", form=form)


@app.route("/edit_todo/<todo_id>", methods=["GET", "POST"])
def edit_todo(todo_id):
    user = get_current_user()
    if not user:
        flash("You need to be logged in to edit a todo!", "danger")
        return redirect(url_for("login"))

    todo = db.todo_flask.find_one({"_id": ObjectId(todo_id)})
    if not todo:
        flash("Todo not found!", "danger")
        return redirect(url_for("index"))

    if user["_id"] != todo["user_id"]:
        flash("You are not authorized to edit this todo!", "danger")
        return redirect(url_for("index"))

    form = ToDoForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        db.todo_flask.update_one(
            {"_id": ObjectId(todo_id)},
            {
                "$set": {
                    "name": form.name.data,
                    "description": form.description.data,
                    "completed": form.completed.data,
                    "created_at": datetime.utcnow(),
                }
            },
        )
        flash("Todo updated successfully!", "success")
        return redirect(url_for("index"))

    form.name.data = todo["name"]
    form.description.data = todo["description"]
    form.completed.data = todo["completed"]
    return render_template("add_todo.html", title="Edit Todo", form=form)


@app.route("/delete_todo/<todo_id>")
def delete_todo(todo_id):
    user = get_current_user()
    if not user:
        flash("You need to be logged in to delete a todo!", "danger")
        return redirect(url_for("login"))

    todo = db.todo_flask.find_one({"_id": ObjectId(todo_id)})
    if not todo:
        flash("Todo not found!", "danger")
        return redirect(url_for("index"))

    if user["_id"] != todo["user_id"]:
        flash("You are not authorized to delete this todo!", "danger")
        return redirect(url_for("index"))

    db.todo_flask.delete_one({"_id": ObjectId(todo_id)})
    flash("Todo deleted successfully!", "success")
    return redirect(url_for("index"))
