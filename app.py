from flask import Flask, jsonify, request, session
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from lxml import html
import requests
import sqlite3
import os
import csv


app = Flask(__name__)
auth = HTTPBasicAuth()
app.secret_key = b'r2q35b4536y5yasdfg5656y98543h394yhtr7834t3490tsrtg'

@auth.hash_password
def hash_pw(username, password):
    salt = get_salt(username)
    return hash(password, salt)

@auth.verify_password
def verify_password(username, password):
	conn = sqlite3.connect('db.db')
	cur = conn.cursor()
	cur.execute('select * from users where username like ?', (username, ))
	try:
		userdata = cur.fetchone()
		id = userdata[0]
	except TypeError:  # If user not exists
		session['userid'] = None
		conn.close()
		return False
	is_authenticated = check_password_hash(userdata[2], password)
	if is_authenticated:
		session['userid'] = int(userdata[0])
	else:
		session['userid'] = None
	conn.close()
	return is_authenticated


def db_connect(function_to_decorate):
	def wrapper(*args, **kwargs):
		conn = sqlite3.connect('db.db')
		cur = conn.cursor()
		res = function_to_decorate(cur, conn, *args, **kwargs)  # Сама функция
		conn.close()
		return res
	wrapper.__name__ = function_to_decorate.__name__
	return wrapper

#delete all users even if you not logged in
@app.route('/users_clear_force', methods=['GET'])
@db_connect
def force_refresh_users_db(cur, conn):
	cur.execute('delete from users')
	conn.commit()
	return jsonify({'Action': 'Force users clear', 'State': 'Success'})

#delete all users exepct current
@app.route('/users_clear', methods=['GET'])
@auth.login_required
@db_connect
def refresh_users_db(cur, conn):
	cur.execute("delete from users where username not like '%" + auth.username() + "'")
	conn.commit()
	return jsonify({'Action': 'Users clear', 'State': 'Success'})
	
@app.route('/db_refresh', methods=['POST'])
@auth.login_required
@db_connect
def refresh_db(cur, conn):
	cur.execute('delete from water')
	conn.commit()
	cur.execute("delete from sqlite_sequence where name='water'")
	conn.commit()
	with open('water.csv') as csvfile:
		readCSV = csv.reader(csvfile, delimiter=';')
		for row in readCSV:
			print(row)
			if len(row[0]) > 0 and row[0] != 'Name':
				cur.execute("""insert or ignore into water(Name, Ca, Mg, F, Z) 
				values (?, ?, ?, ?, ?)""", (row[0], row[1], row[2], row[3], row[4]))
				conn.commit()
							
	return jsonify({'Action': 'Refresh data', 'State': 'Success'})

@app.route('/products')
@auth.login_required
@db_connect
def get_all_products(cur, conn):
	format_data = request.args.get('format', default='Ca,Mg,F,Z')
	find = request.args.get('find', default=None)
	if set(format_data.split(',')) > set('waterid,Ca,Mg,F,Z'.split(',')):  # Все эл-ты format_data принадлежат всем возможным элементам
		return jsonify({'Action': 'get all products', 'State': 'Error'})
	print(format_data)
	cur.execute("select Name {} from water".format( ', '+format_data if len(format_data) > 0 else ''))
	water = {i[0]: dict(zip(format_data.split(','), i[1:])) for i in cur.fetchall() if find is None or i[0] == find}
	return jsonify(water)

@app.route('/users', methods=['POST'])
@db_connect
def signup(cur, conn):
	username = request.args.get('username', default=None)
	password = request.args.get('password', default=None)
	if None in (username, password):
		return jsonify({'Action': 'Register user', 'State': 'Error'})
	else:
		try:
			cur.execute('insert into users(username, password) values(?, ?)', (username, generate_password_hash(password)))
			conn.commit()
		except sqlite3.Error:
			return jsonify({'Action': 'Register user', 'State': 'Already exists'})
		return jsonify({'Action': 'Register user', 'State': 'Success'})

@app.route('/users', methods=['GET'])
@auth.login_required
@db_connect
def users(cur, conn):
	users = cur.execute("select userid, username from users").fetchall()
	users_json = [dict(zip(('userid', 'username'), user)) for user in users]
	return jsonify(users_json)


@app.route('/users/<userid>', methods=['PUT', 'GET', 'DELETE'])
@auth.login_required
@db_connect
def user(cur, conn, userid):
	try:
		userid = int(userid)
	except ValueError:
		return jsonify({'Action': 'User', 'State': 'Error'})
	if request.method == 'PUT':
		password = request.args.get('password', default=None)
		if password is None or userid != session['userid']:
			return jsonify({'Action': 'Edit user', 'State': 'Error'})
		else:
			cur.execute('update users set password = ? where userid = ?',
						(generate_password_hash(password), userid))
			conn.commit()
			return jsonify({'Action': 'Edit user', 'State': 'Success'})
	elif request.method == 'GET':
		users = cur.execute("select userid, username from users where userid = ?", (userid, )).fetchall()
		users_json = [dict(zip(('userid', 'username'), user)) for user in users]
		return jsonify(users_json)
	elif request.method == 'DELETE':
		userid = request.args.get('userid', default=None)
		if userid == session['userid']:
			cur.execute('delete from users where userid = ?', (userid ,))
			conn.commit()
			return jsonify({'Action': 'Delete user', 'State': 'Success'})
		else:
			return jsonify({'Action': 'Delete user', 'State': 'Error'})


@app.route('/')
def index():
	return "<h1>Finally, works!</h1>"

@db_connect
def init(cur, conn):
	cur.execute("""
		create table IF NOT EXISTS users (
		 userid INTEGER PRIMARY KEY AUTOINCREMENT,
		 username TEXT NOT NULL UNIQUE,
		 password TEXT NOT NULL
		)
		""")
	conn.commit()
	cur.execute("""
		create table IF NOT EXISTS water (
		 waterid INTEGER PRIMARY KEY AUTOINCREMENT,
		 Name TEXT NOT NULL UNIQUE,
		 Ca TEXT NOT NULL,
		 Mg TEXT NOT NULL,
		 F TEXT NOT NULL
		)
		""")
	conn.commit()

port = os.environ.get('PORT')

if __name__ == '__main__':
	init()
	app.run(host= '0.0.0.0', threaded=True, port=port)

"""

refresh_db          - POST              - обновляет данные в бд о продуктах. Не принимает аргументов

products            - GET               - Отображает для пользователя все продукты. 
											Аргумент format задаёт последовательность/полноту данных для пользователя
											Аргумент find задаёт фразу для поиска по словарю

users               - POST/GET          - добавляет пользователя.
											Аргумент usename 
											Аргумент password
										- Отображает всех пользователей

users/<userid>      - GET/PUT/DELETE    - Отображает пользователя с таким ИД, может быть не вашим
										- Редактирует пользователя с таким ИД, если он ваш
											Аргумент password
										- Удаляет пользователя с таким ИД, если он ваш

"""