# -*- coding: utf-8 -*-
import datetime
import os
from flask import Flask
import psycopg2
from contextlib import closing
from flask import g
from flask import render_template

app = Flask(__name__)

app.config['DATABASE'] = os.environ.get(
	'DATABASE_URL', 'dbname=learning_journal user =postgres password = becreative'
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
