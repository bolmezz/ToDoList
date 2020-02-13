from flask import Flask, render_template, redirect, url_for, request, session, logging, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, BooleanField
from wtforms.validators import Required, DataRequired
from passlib.hash import sha256_crypt
from functools import wraps # decorator'lar için

app = Flask(__name__)
# kendi db'mize bağlamak için todo.db uzantısı verdik
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/Beyza/Desktop/pythonFolder/TodoApp/todo.db'
#db = SQLAlchemy(app)

app.secret_key = "flasktodo" # kendimiz uydurabiliriz

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "flasktodo"
app.config["MYSQL_CURSORCLASS"] = "DictCursor" # aldığımız veriler sözlük yapısında gelir

# app ile mysql'i bağlamak istediğimiz için parametre olarak verdik. Flask ile MySql bağlantısını sağladık.
mysql = MySQL(app)

# Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f) # tüm decorator'larda aynı
    def decorated_function(*args, **kwargs): # tüm decorator'larda aynı
        if "logged_in" in session: # session'ın içinde "logged_in" diye bir key value var mı?
            return f(*args, **kwargs) # tüm decorator'larda aynı // session başlamışsa normal bir şekilde çalıştırır
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","warning")
            return redirect(url_for("login")) # giriş yapmamışsa eğer, login ekranına yönlendiriyoruz 
    return decorated_function # tüm decorator'larda aynı

# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(
        min=4, max=25)])  # StringField class'ından türettik
    username = StringField("Kullanıcı Adı", validators=[
                           validators.Length(min=5, max=35)])
    email = StringField("Email Adresi", validators=[
                        validators.Email(message="Geçerli mail adresi girin.")])
    password = PasswordField("Parola", validators=[validators.DataRequired(
        message="Lütfen bir parola belirleyin."), validators.EqualTo(fieldname="confirm", message="Parola uyuşmuyor.")])
    confirm = PasswordField("Parolayı Tekrar Girin")

# Kullanıcı Login Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı: ")
    password = PasswordField("Parola: ")

# class Todo(db.Model):  # db'de Todo tablosu eklenecek
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(80))
#     complete = db.Column(db.Boolean)

    
class Todo(Form): 
    title = StringField("Başlık", validators=[validators.Length(
        min=4, max=25)])  # StringField class'ından türettik
    complete = BooleanField()

@app.route("/")
@login_required # dashboard çalıştırılmadan önce login_required'a gidecek
def index():
    # todos = Todo.query.all()  # Todo class'ıb, tablonun adı
    # return render_template("index.html", todos=todos)

    cursor = mysql.connection.cursor()

    sorgu = "Select * from todos where owner = %s"

    result = cursor.execute(sorgu, (session["username"],))

    if result > 0:
        todos = cursor.fetchall()
        return render_template("index.html", todos = todos)
    else:
        return render_template("index.html")

@app.route("/complete/<string:id>", methods = ["POST", "GET"])
def completeTodo(id):
    # todo = Todo.query.filter_by(id=id).first()
    # todo.complete = not todo.complete

    # db.session.commit()
    # return redirect(url_for("index"))

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from todos where owner = %s and id = %s"

        result = cursor.execute(sorgu, (session["username"], id))

        if result == 0:
            flash("Böyle bir todo yok veya bu işleme yetkiniz yok.", "danger")
            return redirect(url_for("index"))
        else:
            todo = cursor.fetchone()
            form = Todo()

            form.title.data = todo["title"]
            form.complete.data = not todo["complete"]

            newComp = not todo["complete"]

            sorgu2 = "Update todos Set complete = %s where id = %s"

            cursor = mysql.connection.cursor()
            cursor.execute(sorgu2, (newComp, id))
            mysql.connection.commit()
            cursor.close()

            flash("Todo güncellendi!", "success")
            return redirect(url_for("index"))

    #  !!! KULLANILMIYOR BURASI !!!
    else: # POST request    
        #form = Todo(request.form)
        cursor = mysql.connection.cursor()
        sorgu = "Select * from todos where owner = %s and id = %s"
        todo = cursor.fetchone()

        newComp = not todo["complete"]

        sorgu2 = "Update todos Set complete = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2, (newComp, id))
        mysql.connection.commit()
        cursor.close()

        flash("Todo güncellendi!", "success")
        return redirect(url_for("index"))

@app.route("/delete/<string:id>")
def deleteTodo(id):
    # todo = Todo.query.filter_by(id=id).first()
    # db.session.delete(todo)

    # db.session.commit()
    # return redirect(url_for("index"))

    cursor = mysql.connection.cursor()

    sorgu = "Select * from todos where owner = %s and id = %s"

    result = cursor.execute(sorgu, (session["username"],id))

    if result > 0:
        sorgu2 = "Delete from todos where id = %s"

        cursor.execute(sorgu2, (id,))
        mysql.connection.commit()
        flash("Todo silindi.","success")
        return redirect(url_for("index"))  
    else:
        flash("Böyle bir todo yok veya bu işleme yetkiniz yok.", "danger")
        return redirect(url_for("index"))

@app.route("/addTodo", methods=["POST", "GET"])
def addTodo():
   
    # # index.html'de name = "title" olanı alacak
    # title = request.form.get("title")
    # # class'tan bir obje oluşturduk
    # newTodo = Todo(title=title, complete=False)
    # db.session.add(newTodo)
    # db.session.commit()

    # return redirect(url_for("index"))

    form = Todo(request.form)

    if request.method == "POST" and form.validate(): # makaleyi kaydedicez
        title = form.title.data
        #complete = form.complete.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into todos(owner,title) VALUES(%s, %s)"

        cursor.execute(sorgu, (session["username"],title))
        mysql.connection.commit()

        cursor.close()

        flash("Todo başarıyla eklenmiştir.","success")

        return redirect(url_for("index"))

    return render_template("addtodo.html", form = form)

 
# Kayıt Olma
@app.route("/register", methods = ["GET","POST"]) #hem get hem de post req alabilir
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate(): # submit butonuna basıldığında post req oluşur
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) 
        # şifreleri encrypt ederek saklamak istiyoruz

        cursor = mysql.connection.cursor()
         # mySQL vt üzerinde işlem yapabilmemizi sağlayacak yapı: cursor

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password)) 
        # değerleri demet olarak veriyoruz
        # sorgu = "Insert into users(name,email,username,password) VALUES({},{},{},{})".format(name,email,username,password)

        mysql.connection.commit() # vt'da güncelleme yaptığımız için commit yapmalıyız.

        cursor.close()
        flash("Başarıyla kayıt oldunuz..","success")

        return redirect(url_for("login")) #index metoduyla ilişkili olan url adresine gider
    else:
        return render_template("register.html", form = form)

# Login İşlemi
@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form) # http request

    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu, (username, )) # (username, ) -> tek elemanlı demet syntax'i

        if result > 0:
            data = cursor.fetchone()
            real_password =data["password"] # tablodaki password alanını alıyoruz
            if sha256_crypt.verify(password_entered,real_password):
                # session
                session["logged_in"] = True
                session["username"] = username
                 
                flash("Başarıyla giriş yapıldı.","success")
                return redirect(url_for("index"))
            else:
                flash("Parola yanlış!","warning")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı!","danger")
            return redirect(url_for("login"))

    return render_template("login.html", form = form)

# Logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



if __name__ == "__main__":  # server'ı ayağa kaldırmak için
    # db.create_all()  # class'ları tablo olarak ekleyecek/zaten önceden oluşmuş tabloları bir daha oluşturmaz
    # app.run(debug=True)
    app.run(debug=True)  # localhost'u çalıştır
