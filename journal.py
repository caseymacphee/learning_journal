# -*- coding: utf-8 -*-
import os
from flask import Flask
import psycopg2
from contextlib import closing
from flask import g


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
	
@app.route('/')
def hello():
	return u'Hello world!'
	

DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
	id serial PRIMARY KEY,
	title VARCHAR (127) NOT NULL,
	text TEXT NOT NULL,
	created TIMESTAMP NOT NULL
)
"""
if __name__ == '__main__':
	app.run(debug=True)
