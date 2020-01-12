from flask import Flask, jsonify, request, session
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from lxml import html
import requests
import sqlite3
import os

app = Flask(__name__)
auth = HTTPBasicAuth()
app.secret_key = b'r2q35b4536y5yasdfg5656y98543h394yhtr7834t3490tsrtg'

@auth.verify_password
def verify_password(username, password):
    conn = sqlite3.connect('db.db')
    cur = conn.cursor()
    cur.execute('select * from users where username = ?', (username, ))
    try:
        userdata = cur.fetchone()
    except TypeError:  # If user not exists
        session['userid'] = None
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


@app.route('/db_refresh', methods=['POST'])
@auth.login_required
@db_connect
def refresh_db(cur, conn):
    cur.execute('delete from ingridients')
    conn.commit()
    cur.execute("delete from sqlite_sequence where name='ingridients'")
    conn.commit()
    try:
        req = requests.get('http://m.woman.ru/health/diets/article/88057/').text
    except ConnectionError:
        return jsonify({'Action': 'Refresh data', 'State': 'Error'})
    result = html.fromstring(req).xpath('//tr')
    for r in result[4:]:
        prod = r.text_content().split()
        if prod[0] != 'Продукт':
            cur.execute("""insert or ignore into ingridients(Name_nm, Bilki, Zhiri, Uglevodi, Voda, Kkal) 
            values (?, ?, ?, ?, ?, ?)""", (' '.join(prod[:-5]), prod[-4], prod[-3], prod[-2], prod[-5], prod[-1]))
            conn.commit()
    return jsonify({'Action': 'Refresh data', 'State': 'Success'})


@app.route('/products')
@auth.login_required
@db_connect
def get_all_products(cur, conn):
    format_data = request.args.get('format', default='ingridient_id,bilki,zhiri,uglevodi,voda,kkal') # bilki,zhiri,uglevodi,voda,kkal
    find = request.args.get('find', default=None)
    if set(format_data.split(',')) > set('ingridient_id,bilki,zhiri,uglevodi,voda,kkal'.split(',')):  # Все эл-ты format_data принадлежат всем возможным элементам
        return jsonify({'Action': 'get all products', 'State': 'Error'})
    cur.execute("select Name_nm, {} from ingridients".format(format_data))
    ingridients = {i[0]: dict(zip(format_data.split(','), i[1:])) for i in cur.fetchall() if find is None or i[0] == find}
    return jsonify(ingridients)


@app.route('/users', methods=['POST', 'GET'])
@auth.login_required
@db_connect
def users(cur, conn):
    if request.method == 'POST':
        username = request.args.get('username', default=None)
        password = request.args.get('password', default=None)
        if None in (username, password):
            return jsonify({'Action': 'Register user', 'State': 'Error'})
        else:
            cur.execute('insert into users(username, password) values(?, ?)', (username, generate_password_hash(password)))
            conn.commit()
            return jsonify({'Action': 'Register user', 'State': 'Success'})
    elif request.method == 'GET':
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



@app.route('/recieps', methods=['GET', 'POST'])
@auth.login_required
@db_connect
def recieps(cur, conn):
    if request.method == 'POST':
        components = request.args.get('components', default=None)
        if components is None:
            return jsonify({'Action': 'Add reciept', 'State': 'Error'})
        try:
            components = components.split(',')
            components = list(map(int, components))
        except ValueError:
            return jsonify({'Action': 'Add reciept', 'State': 'Error'})

        cur.execute('insert into user_recieps(user, components) values (?, ?)',
                    (session['userid'], ','.join(components)))
        conn.commit()
        return jsonify({'Action': 'Add reciept', 'State': 'Success'})
    elif request.method == 'GET':
        recieps = cur.execute("select * from user_recieps where user = ?", (session['userid'],)).fetchall()
        recieps_json = [dict(zip(('user', 'id_reciept', 'components'), reciep)) for reciep in recieps]
        return jsonify(recieps_json)


@app.route('/recieps/<rid>', methods=['PUT', 'GET', 'DELETE'])
@auth.login_required
@db_connect
def reciept(cur, conn, rid):
    try:
        rid = int(rid)
    except ValueError:
        return jsonify({'Action': 'Reciep', 'State': 'Error'})

    if request.method == 'PUT':
        components = request.args.get('components', default=None)
        if components is None:
            return jsonify({'Action': 'Add reciept', 'State': 'Error'})
        try:
            components = components.split(',')
            components = list(map(int, components))
        except ValueError:
            return jsonify({'Action': 'Add reciept', 'State': 'Error'})

        cur.execute('update user_recieps set components = ? where id_reciept = ? and user = ?',
                    (','.join(components), rid, session['userid']))
        conn.commit()
        return jsonify({'Action': 'Edit reciept', 'State': 'Success'})
    elif request.method == 'GET':
        recieps = cur.execute("select * from user_recieps where id_reciept = ?", (rid,)).fetchall()
        recieps_json = [dict(zip(('user', 'id_reciept', 'components'), reciep)) for reciep in recieps]
        for i in recieps_json:
            format_data = 'ingridient_id, bilki, zhiri, uglevodi, voda, kkal'
            cur.execute("select * from ingridients where ingridient_id in ({})".format(i['components']))
            ingridients = {i[0]: dict(zip(format_data.split(','), i[1:])) for i in cur.fetchall()}
            i['components'] = jsonify(ingridients)
        return jsonify(recieps_json)
    elif request.method == 'DELETE':
        cur.execute('delete from user_recieps where user = ? and id_reciept = ?', (session['userid'], rid))
        conn.commit()
        return jsonify({'Action': 'Delete reciept', 'State': 'Success'})


@app.route('/')
def index():
    return "<h1>IT works !!</h1>"


port = os.environ.get('PORT')

if __name__ == '__main__':
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

recieps             - GET/POST          - Отображает все !ваши! рецепты
                                        - Добавляет новый рецепт

recieps/<id>        - GET/PUT/DELETE    - Отображает данные о рецепте с таким ид, может быть не вашим
                                        - Изменяет рецепт, если он ваш
                                            Аргумент components
                                        - Удаляет рецепт, если он ваш

"""