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

@app.route('/authors/<authorname>/edit', methods=['GET', 'POST'])
def editAuthor():
    return "Edit the author"

@app.route('/authors/<int:authorname>/delete', methods=['GET', 'POST'])
def deleteAuthor():
    return "Delete the author"

@app.route('/authors/<authorname>')
def showAuthor():
    return "This is the author page with a book list"

@app.route('/authors/<bookname>')
def showBook():
    return "This page will show the book by the author"

@app.route('/authors/<bookname>/edit')
def editBook():
    return "This page will edit the book"

@app.route('/authors/<bookname>/delete')
def deleteBook():
    return "This page will delete the book"

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'iloveyou'
    app.run(host='0.0.0.0', port = 5000)
