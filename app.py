from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import random
import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

conn = sqlite3.connect('instance/db.sqlite')
cursor = conn.cursor()
json_file = 'instance/books_catalog.json'


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    surname = db.Column(db.String(250), unique=True, nullable=False)

    email = db.Column(db.String(250), unique=True, nullable=False)
    phone = db.Column(db.String(250), unique=True, nullable=False)

    password = db.Column(db.String(250), nullable=False)


class Genre(db.Model):
    __tablename__ = 'genre'
    genre_id = db.Column(db.Integer, primary_key=True, nullable=True)
    name_genre = db.Column(db.String(80), unique=True, nullable=True)

    def __repr__(self):
        return f"<Genre {self.name_genre}>"


class Subgenre(db.Model):
    __tablename__ = 'subgenre'
    name_subgenre_id = db.Column(db.Integer, primary_key=True, nullable=True)
    name_subgenre = db.Column(db.String(120), nullable=True)
    genre_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<Subgenre {self.name_subgenre}>"


class Book(db.Model):
    __tablename__ = 'book'
    book_id = db.Column(db.Integer, unique=True,
                        primary_key=True, nullable=True)
    title = db.Column(db.String(120), nullable=True)
    author = db.Column(db.String(120), nullable=True)
    price = db.Column(db.Integer)
    genre = db.Column(db.String(120), nullable=True)
    cover = db.Column(db.String(120), unique=True, nullable=True)
    description = db.Column(db.String(120), nullable=True)

    rating = db.Column(db.Integer, nullable=True)
    year = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<Book {self.title}>"


class CartItems(db.Model):
    __tablename__ = 'cartitems'
    id = db.Column(db.Integer, unique=True,
                   primary_key=True, nullable=True)

    book_id = db.Column(db.Integer, db.ForeignKey(
        'book.book_id'), nullable=True)

    def __repr__(self):
        return f"<Cart {self.book_id}>"


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, unique=True,
                   primary_key=True, nullable=True)
    ordernumber = db.Column(db.Integer, nullable=True)
    phone = db.Column(db.String(220), nullable=True)
    order_way = db.Column(db.String(220), nullable=True)
    message_purchase = db.Column(db.String(220), nullable=True)
    summ_order = db.Column(db.Integer, nullable=True)
    delivery_date = db.Column(db.String(220), nullable=True)

    def __repr__(self):
        return f"<Order {self.order_way}>"


with app.app_context():
    db.create_all()


def insert_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
            for item in data:
                cursor.execute('''
                INSERT OR IGNORE INTO book(book_id,title,author,price,genre,cover,description,rating,year) VALUES(?,?,?,?,?,?,?,?,?)''', (item['id'], item['title'], item['author'], item['price'], item['genre'], item['cover'], item['description'], item['rating'], item['year']))
            conn.commit()
            conn.close()
        except json.JSONDecodeError as e:
            print(f"Error JSON:{e}")


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/")
def base():
    genres = Genre.query.all()
    return render_template("home.html", genres=genres)


@app.route("/<int:id>")
def home(id):
    subgenres = Subgenre.query.filter_by(genre_id=id)
    return render_template("home.html", subgenres=subgenres)


@app.route("/<string:genre_name>")
def profile(genre_name):
    books = Book.query.filter_by(genre=genre_name)
    return render_template("home.html", books=books)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        surname = request.form.get("surname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        if Users.query.filter_by(email=email).first():
            return render_template("signup.html", error="Email already taken!")
        hashed_password = generate_password_hash(
            password, method="pbkdf2:sha256")
        new_user = Users(username=username.capitalize(), surname=surname.capitalize(),
                         email=email, phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = Users.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username and password")
    return render_template("login.html")


@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    books = Book.query.all()
    count = CartItems.query.count()
    if request.method == 'POST':
        book_id = request.form['book_id_cart']
        new_cart = CartItems(book_id=book_id)
        db.session.add(new_cart)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("dashboard.html", username=current_user.username, books=books, count=count)


@app.route("/cart", methods=['GET', 'POST'])
@login_required
def add_to_cart():
    books = Book.query.filter(Book.book_id == CartItems.book_id)

    # objects = CartItems.query.all()
    # values_unique = {}
    # print(objects)
    # for item in objects:
    #     if item.book_id in values_unique.items():
    #         values_unique[item.book_id] = values_unique[item.book_id] + 1
    #     else:
    #         values_unique.update({item.book_id: 1})
    # print(values_unique)

    if request.method == 'POST':
        book_id_rm = request.form['book_id_remove_cart']
        CartItems.query.filter_by(book_id=book_id_rm).delete()
        db.session.commit()
        return redirect(url_for('add_to_cart'))
    return render_template("cart.html", books=books)


@app.route("/create_order", methods=["GET", "POST"])
@login_required
def create_order():
    books_orders = Book.query.filter(Book.book_id == CartItems.book_id)
    sum_list = []
    for book in books_orders:
        sum_list.append(book.price)
        print(book.title)

    if request.method == "POST":
        ordernumber = request.form.get("ordernumber")
        phone = request.form.get("phone")
        order_way = request.form.get("order_way")
        message_purchase = request.form.get("message_purchase")
        delivery_date = request.form.get("delivery_date")
        CartItems.query.delete()
        new_order = Order(ordernumber=random.randrange(1000, 100000), phone=phone, order_way=order_way, message_purchase=message_purchase,
                          summ_order=sum(sum_list), delivery_date=datetime.datetime.now())
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("create_order.html", ordernumber=random.randrange(1000, 100000), summ=sum(sum_list), delivery_date=datetime.datetime.now())


@app.route('/order')
@login_required
def orderview():
    orders = Order.query.all()
    return render_template("orderview.html", orders=orders)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("logout"))


@app.route('/catalog')
def catalog():
    return redirect("/catalog")


if __name__ == "__main__":
    insert_data(json_file)
    app.run(debug=True)
