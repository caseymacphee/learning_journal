# -*- coding: utf-8 -*-
import datetime
import os
from flask import Flask
import psycopg2
from contextlib import closing
from flask import g
from flask import render_template
from flask import abort
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from passlib.hash import pbkdf2_sha256


app = Flask(__name__)

app.config['DATABASE'] = os.environ.get(
	'DATABASE_URL', 'dbname=learning_journal user =postgres password = becreative'
	)
app.config['ADMIN_USERNAME'] = os.environ.get(
	'ADMIN_USERNAME', 'admin'
	)
app.config['ADMIN_PASSWORD'] = os.environ.get(
	'ADMIN_PASSWORD', pbkdf2_sha256.encrypt('admin')
	)
app.config['SECRET_KEY'] = os.environ.get(
    'FLASK_SECRET_KEY', '300000'
)

def connect_db():
	#return a connection to the db
	return psycopg2.connect(app.config['DATABASE'])

def init_db():
	#initializes using db schema !!! will drop existing schema

	with closing(connect_db()) as db:
		db.cursor().execute(DB_SCHEMA)
		db.commit()

def get_database_connection():
	db = getattr(g, 'db', None)
	if db is None:
		g.db = db = connect_db()
	return db

def do_login(username='', passwd=''):
    if username != app.config['ADMIN_USERNAME']:
        raise ValueError
    if not pbkdf2_sha256.verify(passwd, app.config['ADMIN_PASSWORD']):
        raise ValueError
    session['logged_in'] = True

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		if exception and isinstance(exception, psycopg2.Error):
			#if there's a problem with the databse rollback the transaction
			db.rollback()
		else:
			db.commit()
		db.close()

def write_entry(title, text):
	if not title or not text:
		raise ValueError("Title and text required for writing and entry")
	con = get_database_connection()
	cur = con.cursor()
	now = datetime.datetime.utcnow()
	cur.execute(DB_ENTRY_INSERT, [title, text, now])

def get_all_entries():
	"""return a list of all entries as dicts"""
	con = get_database_connection()
	cur = con.cursor()
	cur.execute(DB_ENTRIES_LIST)
	keys = ('id', 'title', 'text', 'created')
	return [dict(zip(keys, row)) for row in cur.fetchall()]


@app.route('/')
def show_entries():
	entries = get_all_entries()
	return render_template('list_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
	try:
		write_entry(request.form['title'], request.form['text'])
	except psycopg2.Error:
		abort(500)
	return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		try:
			do_login(request.form['username'].encode('utf-8'),
			request.form['password'].encode('utf-8'))
		except ValueError:
			error = "Login Failed"
		else:
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	return redirect(url_for('show_entries'))

DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
	id serial PRIMARY KEY,
	title VARCHAR (127) NOT NULL,
	text TEXT NOT NULL,
	created TIMESTAMP NOT NULL
)
"""
DB_ENTRY_INSERT = """
INSERT INTO entries (title, text, created) VALUES(%s, %s, %s)
"""
DB_ENTRIES_LIST = """
SELECT id, title, text, created FROM entries ORDER BY created DESC
"""

if __name__ == '__main__':
	app.run(debug=True)
