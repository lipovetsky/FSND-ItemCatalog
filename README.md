# FSND-Item-Catalog

Are you a fan of great literature? Philosophy? History? Western Civilization?
Boy, have I got an app for you! How about a Great Books of the Western World
digital bookshelf? One that you can add and edit and remove books and authors
from! That's right. It's all here for you. It's even got 4 authors preloaded.

You may ask yourself: how do I get it running? I'm glad you asked! I will
show you how in this Readme.

## Download the Files

Make sure you have Git installed. That being covered, it's time to clone the
git repository to your machine. Here is the command:

`git clone https://github.com/lipovetsky/FSND-ItemCatalog.git`


## Run the database

Now that you have a copy of the program, it's time to run it! Make sure you
change into the directory of the repository you cloned:

`cd FSND-ItemCatalog`

Next, set up the vagrant environment! It may take a long time,
but it's got what you need!

`vagrant up`

Then, once it loads:

`vagrant ssh`

Finally, change to the directory:

`cd /vagrant`

You may also have to install Flask_Bootstrap with the following command:

`sudo pip install flask_bootstrap`

## Enjoy the Show

Now, with a simple command, we can make this come to life!

`python project.py`

Just enter the following in your web browser to access the site:

`http://localhost:5000/`

Enjoy all the sights and sounds! Explore. Dream. Discover.


## Concluding Words

This project is part of the Full Stack Nanodegree for Udacity. You can make
something similar, should you choose to enroll. The course is full of magic.
