import os
import random
import string
from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_bootstrap import Bootstrap
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from database import Base, Author, Book, User

from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response, flash
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Great Books Quest Library"

app = Flask(__name__)
Bootstrap(app)

engine = create_engine('sqlite:///greatbookswithusers.db')
Base = declarative_base()
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # #Get auth code
    code = request.data

    try:
        # Upgrade auth code to credentials
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check validity of access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If error, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token used for correct user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's User ID is not the given User ID"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID doesn't match app's"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user already connected."), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store access token in session (for later use)
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: '
    output += '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user is not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # print 'In gdisconnect access token is %s' % login_session['access_token']
    # print 'User name is: '
    # print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # print 'Result is '
    # print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You have been logged out")
        return redirect(url_for('showAllAuthors'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/authors')
def showAllAuthors():
    authors = session.query(Author).order_by(Author.last_name).all()
    if 'username' in login_session:
        return render_template('index.html', authors=authors)
    return render_template('publicindex.html', authors=authors)


@app.route('/json')
@app.route('/authors/json')
def showAuthorsJSON():
    authors = session.query(Author).order_by(Author.last_name.desc()).all()
    return jsonify([author.serialize for author in authors])


@app.route('/books/json')
def showAllBooksJSON():
    books = session.query(Book).filter(Book.author_id == Author.id).order_by(Author.last_name).all()
    return jsonify([thebook.serialize for thebook in books])


@app.route('/<author>/json')
def showBooksbyAuthorJSON(author):
    books = session.query(Book).join(Author).filter(Author.last_name == author).all()
    return jsonify([thebooks.serialize for thebooks in books])


@app.route('/<author>/<book>/json')
def showBookJSON(author, book):
    author = session.query(Author).filter_by(last_name=author.title()).first()
    if author:
        book = session.query(Book).filter_by(name=book.title()).first()
        if book:
            return jsonify(book.serialize)
    return "Book not found"


@app.route('/<author>')
def showAuthor(author):
    theAuthor = session.query(Author).filter_by(last_name=author.title()).first()
    if theAuthor:
        books = session.query(Book).filter_by(author_id=theAuthor.id).all()
        if 'username' in login_session:
            if login_session['user_id'] == theAuthor.user_id:
                return render_template('authorpage.html', author=theAuthor, books=books)
        return render_template('publicauthorpage.html', author=theAuthor, books=books)
    else:
        return "Author doesn't exist!"


@app.route('/authors/add', methods=['GET', 'POST'])
def newAuthor():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        theAuthor = request.form['authorname'].title()
        theBio = request.form['bio']
        thePhoto = request.form['picture']
        userID = login_session['user_id']
        if theAuthor and theBio and thePhoto:
            session.add(Author(last_name=theAuthor, bio=theBio, photo=thePhoto,
                               user_id=userID))
            session.commit()
            flash("Author has been added!")
            return redirect(url_for('showAllAuthors'))
        else:
            flash("You need to fill out all the fields!")
            return render_template('newauthor.html')
    else:
        return render_template('newauthor.html')


@app.route('/<author>/edit', methods=['GET', 'POST'])
# @app.route('/<authorname>/edit')
def editAuthor(author):
    author = session.query(Author).filter_by(last_name=author.title()).first()
    if 'username' not in login_session:
        return redirect('/login')
    elif login_session['user_id'] != author.user_id:
        return redirect(url_for('showAuthor', author=author.last_name))
    if author:
        if request.method == 'POST':
            author.last_name = request.form['authorname'].title()
            author.bio = request.form['bio']
            author.photo = request.form['picture']
            session.commit()
            return redirect(url_for('showAuthor', author=author.last_name))
        else:
            return render_template('editauthor.html', author=author)
    else:
        return "Author doesn't exist!"


@app.route('/<author>/delete', methods=['GET', 'POST'])
def deleteAuthor(author):
    author = session.query(Author).filter_by(last_name=author).first()
    if 'username' not in login_session:
        return redirect('/login')
    elif login_session['user_id'] != author.user_id:
        return redirect(url_for('showAuthor', author=author.last_name))
    if request.method == 'POST':
        session.delete(author)
        session.commit()
        return redirect(url_for('showAllAuthors'))
    return render_template('deleteauthor.html', author=author)


@app.route('/<author>/<book>')
def showBook(author, book):
    author = session.query(Author).filter_by(last_name=author.title()).first()
    book = session.query(Book).filter_by(name=book.title()).first()
    if author and book and author.id == book.author_id:
        if 'username' in login_session:
            if login_session['user_id'] == book.user_id:
                return render_template('bookpage.html', author=author, book=book)
        return render_template('publicbookpage.html', author=author, book=book)
    else:
        return "Book doesn't exist!"


@app.route('/<author>/add', methods=['GET', 'POST'])
def addBook(author):
    author = session.query(Author).filter_by(last_name=author.title()).first()
    if 'username' not in login_session:
        return redirect('/login')
    elif login_session['user_id'] != author.user_id:
        return redirect(url_for('showAuthor', author=author.last_name))
    if request.method == 'POST':
        newBook = (request.form['name'].title(), request.form['image'],
                   request.form['amazon'], request.form['description'])
        if newBook:
            userID = login_session['user_id']
            session.add(Book(name=newBook[0], image=newBook[1],
                             amazon=newBook[2], description=newBook[3], author_id=author.id, user_id=userID))
            session.commit()
            flash("Book has been added!")
            return redirect(url_for('showBook', author=author.last_name, book=newBook[0]))
        else:
            flash("You need to fill out all the fields!")
            return render_template('addbook.html', author=author)

    return render_template('addbook.html', author=author)


@app.route('/<author>/<book>/edit', methods=['GET', 'POST'])
def editBook(author, book):
    author = session.query(Author).filter_by(last_name=author.title()).first()
    if 'username' not in login_session:
        return redirect('/login')
    elif login_session['user_id'] != author.user_id:
        return redirect(url_for('showAuthor', author=author.last_name))
    allauthors = session.query(Author).all()
    book = session.query(Book).filter_by(name=book.title()).first()
    if author and book:
        if request.method == 'POST':
            book.name = request.form['name'].title()
            book.image = request.form['image']
            book.amazon = request.form['amazon']
            book.description = request.form['description']
            thelastname = request.form['author']
            newauthor = session.query(Author).filter_by(last_name=thelastname).first()
            book.author_id = newauthor.id
            thelastname = request.form['author']
            session.commit()
            return redirect(url_for('showBook', author=book.author.last_name, book=book.name))
        else:
            return render_template('editbook.html', theauthor=author, author=allauthors, book=book)
    else:
        return "Book doesn't exist!"


@app.route('/<author>/<book>/delete', methods=['GET', 'POST'])
def deleteBook(author, book):
    author = session.query(Author).filter_by(last_name=author.title()).first()
    if 'username' not in login_session:
        return redirect('/login')
    elif login_session['user_id'] != author.user_id:
        return redirect(url_for('showAuthor', author=author.last_name))
    book = session.query(Book).filter_by(name=book).first()
    if request.method == 'POST':
        session.delete(book)
        session.commit()
        return redirect(url_for('showAuthor', author=author.last_name))
    return render_template('deletebook.html', author=author, book=book)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'iloveyou'
    app.run(host='0.0.0.0', port=5000)
