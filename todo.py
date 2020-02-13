from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# kendi db'mize bağlamak için todo.db uzantısı verdik
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/Beyza/Desktop/pythonFolder/TodoApp/todo.db'
db = SQLAlchemy(app)


@app.route("/")
def index():
    todos = Todo.query.all()  # Todo class'ıb, tablonun adı
    return render_template("index.html", todos=todos)


@app.route("/complete/<string:id>")
def completeTodo(id):
    todo = Todo.query.filter_by(id=id).first()
    todo.complete = not todo.complete

    db.session.commit()
    return redirect(url_for("index"))

@app.route("/delete/<string:id>")
def deleteTodo(id):
    todo = Todo.query.filter_by(id=id).first()
    db.session.delete(todo)

    db.session.commit()
    return redirect(url_for("index"))

@app.route("/add", methods=["POST"])
def addTodo():
    # index.html'de name = "title" olanı alacak
    title = request.form.get("title")
    # class'tan bir obje oluşturduk
    newTodo = Todo(title=title, complete=False)
    db.session.add(newTodo)
    db.session.commit()

    return redirect(url_for("index"))


class Todo(db.Model):  # db'de Todo tablosu eklenecek
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    complete = db.Column(db.Boolean)


if __name__ == "__main__":  # server'ı ayağa kaldırmak için
    db.create_all()  # class'ları tablo olarak ekleyecek/zaten önceden oluşmuş tabloları bir daha oluşturmaz
    app.run(debug=True)
