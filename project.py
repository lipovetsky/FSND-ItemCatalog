import os
from flask import Flask, render_template, url_for, redirect, request, jsonify, flash
from flask_bootstrap import Bootstrap
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from database import Base, Author, Book

app = Flask(__name__)
Bootstrap(app)

engine = create_engine('sqlite:///greatbooks.db')
Base = declarative_base()
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/authors')
def showAllAuthors():
    authors = session.query(Author).all()
    return render_template('index.html', authors = authors)

@app.route('/<authorname>')
def showAuthor(authorname):
    return "This is %s's page with a book list" % authorname

@app.route('/authors/add', methods=['GET', 'POST'])
def newAuthor():
    if request.method == 'POST':
        theAuthor = request.form['authorname']
        theBio = request.form['bio']
        thePhoto = request.form['picture']
        session.add(Author(lastname=theAuthor, bio = theBio, photo = thePhoto))
        session.commit()
        flash("Author has been added!")
        return redirect(url_for('showAll'))
    else:
        return render_template('newauthor.html')

@app.route('/<authorname>/edit', methods=['GET', 'POST'])
def editAuthor(authorname):
    return "Edit %s" % authorname

@app.route('/<authorname>/delete', methods=['GET', 'POST'])
def deleteAuthor(authorname):
    return "Delete %s" % authorname

@app.route('/<authorname>/<bookname>')
def showBook(authorname, bookname):
    return "This page will show the book %s by the author %s" % (bookname, authorname)

@app.route('/<authorname>/add')
def addBook(authorname):
    return "This page will add a book for the author %s" % authorname

@app.route('/<authorname>/<bookname>/edit')
def editBook(authorname, bookname):
    return "This page will edit the book %s by the author %s" % (bookname, authorname)

@app.route('/<authorname>/<bookname>/delete')
def deleteBook(authorname, bookname):
    return "This page will delete the book %s by the author %s" % (bookname, authorname)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'iloveyou'
    app.run(host='0.0.0.0', port = 5000)
