from flask import Flask, render_template, request, abort, redirect, url_for, session, flash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = 'fungroup_secret_key_change_me'

def get_db_connection():
    conn = sqlite3.connect('fungroup.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('fungroup.db')
    cursor = conn.cursor()
    
    # Таблица игр
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            letter TEXT NOT NULL,
            icon_url TEXT
        )
    ''')
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            reg_date TEXT NOT NULL,
            is_online INTEGER DEFAULT 1
        )
    ''')
    
    # Таблица анкет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            title TEXT NOT NULL,
            username TEXT NOT NULL,
            rank TEXT,
            description TEXT,
            price_or_type TEXT,
            FOREIGN KEY (game_id) REFERENCES games (id)
        )
    ''')
    
    # Таблица чатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1 TEXT NOT NULL,
            user2 TEXT NOT NULL,
            last_message_time TEXT
        )
    ''')
    
    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
    ''')
    
    # Заполнение играми включая новые (Terraria, Garry's mod, Soul Knight, Lethal company)
    cursor.execute('SELECT COUNT(*) FROM games')
    if cursor.fetchone()[0] == 0:
        games_data = [
            ('Apex Legends', 'apex-legends', 'A', '/static/images/apex.png'),
            ('Among Us', 'among-us', 'A', '/static/images/amongus.png'),
            ('Brawl Stars', 'brawl-stars', 'B', '/static/images/brawlstars.png'),
            ('Battlefield', 'battlefield', 'B', '/static/images/battlefield.png'),
            ('Counter-Strike 2', 'cs2', 'C', '/static/images/cs2.png'),
            ('Call of Duty', 'cod', 'C', '/static/images/cod.png'),
            ('Dota 2', 'dota-2', 'D', '/static/images/dota2.png'),
            ('Dead by Daylight', 'dbd', 'D', '/static/images/dbd.png'),
            ('EA Sports FC', 'ea-fc', 'E', '/static/images/eafc.png'),
            ('Escape from Tarkov', 'tarkov', 'E', '/static/images/tarkov.png'),
            ('Fortnite', 'fortnite', 'F', '/static/images/fortnite.png'),
            ('Garry\'s Mod', 'garrys-mod', 'G', '/static/images/gmod.png'),
            ('Genshin Impact', 'genshin', 'G', '/static/images/genshin.png'),
            ('Lethal Company', 'lethal-company', 'L', '/static/images/lethal.png'),
            ('Roblox', 'roblox', 'R', '/static/images/roblox.png'),
            ('Soul Knight', 'soul-knight', 'S', '/static/images/soulknight.png'),
            ('Standoff 2', 'standoff-2', 'S', '/static/images/standoff2.png'),
            ('Terraria', 'terraria', 'T', '/static/images/terraria.png')
        ]
        cursor.executemany('INSERT INTO games (name, slug, letter, icon_url) VALUES (?, ?, ?, ?)', games_data)
        
        # Получаем ID новых игр для добавления стартовых анкет
        # Находим ID по их slug
        cursor.execute("SELECT id FROM games WHERE slug = 'garrys-mod'")
        gmod_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM games WHERE slug = 'lethal-company'")
        lethal_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM games WHERE slug = 'soul-knight'")
        sk_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM games WHERE slug = 'terraria'")
        terraria_id = cursor.fetchone()[0]

        profiles_data = [
            (gmod_id, 'Ищем людей для игры в DarkRP', 'GModFan', '1000+ часов', 'Строим базу, играем по вечерам.', 'Клан'),
            (lethal_id, 'Иду в сквад за ценным ломом', 'CompanyEmployee', 'Профессионал', 'Знаю все лунные карты, не боюсь собак.', 'Пати'),
            (sk_id, 'Ищу напарника на прохождение Boss Rush', 'KnightHero', 'Макс. прокачка', 'Играем на кошмаре.', 'Дуэт'),
            (terraria_id, 'Создаем новый мир на эксперте', 'Terrarian', 'Опытный строитель', 'Убиваем Глаза Ктулху, ищу мага/стрелка.', 'Бесплатно')
        ]
        cursor.executemany('INSERT INTO profiles (game_id, title, username, rank, description, price_or_type) VALUES (?, ?, ?, ?, ?, ?)', profiles_data)
        
    conn.commit()
    conn.close()

def send_bot_welcome(username):
    conn = get_db_connection()
    bot_name = "FunGroup bot"
    
    chat = conn.execute('SELECT * FROM chats WHERE (user1 = ? AND user2 = ?) OR (user1 = ? AND user2 = ?)', 
                        (username, bot_name, bot_name, username)).fetchone()
    
    now = datetime.datetime.now().strftime('%H:%M')
    full_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    
    if not chat:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chats (user1, user2, last_message_time) VALUES (?, ?, ?)', 
                       (username, bot_name, full_time))
        chat_id = cursor.lastrowid
        conn.commit()
    else:
        chat_id = chat['id']
        
    welcome_text = "Привет! Добро пожаловать на FunGr😊up! 🎉 Пожалуйста, будь аккуратен в интернете: не сообщай никому свои пароли, личные данные и будь бдителен при общении с незнакомцами."
    conn.execute('INSERT INTO messages (chat_id, sender, text, timestamp) VALUES (?, ?, ?, ?)',
                 (chat_id, bot_name, welcome_text, now))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    search_query = request.args.get('q', '')
    
    if search_query:
        games = conn.execute('SELECT * FROM games WHERE name LIKE ? ORDER BY name', (f'%{search_query}%',)).fetchall()
    else:
        games = conn.execute('SELECT * FROM games ORDER BY name').fetchall()
    
    grouped_games = {}
    for game in games:
        let = game['letter'].upper()
        if let not in grouped_games:
            grouped_games[let] = []
        grouped_games[let].append(game)
        
    total_users_row = conn.execute('SELECT COUNT(*) as cnt FROM users').fetchone()
    total_users = total_users_row['cnt'] if total_users_row else 0
    
    stats = {
        'total_users': total_users,
        'popular_game': 'Counter-Strike 2',
        'user_reg_date': session.get('user_reg_date', 'Не авторизован')
    }
    
    recent_games = conn.execute('SELECT * FROM games LIMIT 3').fetchall()
    conn.close()
    
    current_theme = session.get('theme', 'light')
    logged_in_user = session.get('username')
    
    return render_template('index.html', grouped_games=grouped_games, stats=stats, recent_games=recent_games, search_query=search_query, theme=current_theme, logged_in_user=logged_in_user)

# Страница конкретной игры со списком анкет
@app.route('/game/<slug>')
def game_profiles(slug):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE slug = ?', (slug,)).fetchone()
    if game is None:
        abort(404)
    profiles = conn.execute('SELECT * FROM profiles WHERE game_id = ?', (game['id'],)).fetchall()
    conn.close()
    
    current_theme = session.get('theme', 'light')
    logged_in_user = session.get('username')
    return render_template('game_profile.html', game=game, profiles=profiles, theme=current_theme, logged_in_user=logged_in_user)

# Подробная страница конкретной анкеты
@app.route('/profile/<int:profile_id>')
def profile_detail(profile_id):
    conn = get_db_connection()
    profile = conn.execute('SELECT p.*, g.name as game_name FROM profiles p JOIN games g ON p.game_id = g.id WHERE p.id = ?', (profile_id,)).fetchone()
    conn.close()
    if profile is None:
        abort(404)
        
    current_theme = session.get('theme', 'light')
    logged_in_user = session.get('username')
    return render_template('profile_detail.html', profile=profile, theme=current_theme, logged_in_user=logged_in_user)

@app.route('/messages')
def messages_page():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user_search = request.args.get('user_search', '')
    
    if user_search:
        chats = conn.execute('''
            SELECT * FROM chats 
            WHERE (user1 = ? AND user2 LIKE ?) OR (user2 = ? AND user1 LIKE ?)
            ORDER BY last_message_time DESC
        ''', (username, f'%{user_search}%', username, f'%{user_search}%')).fetchall()
    else:
        chats = conn.execute('''
            SELECT * FROM chats 
            WHERE user1 = ? OR user2 = ?
            ORDER BY last_message_time DESC
        ''', (username, username)).fetchall()
        
    formatted_chats = []
    for chat in chats:
        partner = chat['user2'] if chat['user1'] == username else chat['user1']
        partner_obj = conn.execute('SELECT * FROM users WHERE username = ?', (partner,)).fetchone()
        is_online = partner_obj['is_online'] if partner_obj else (1 if partner == "FunGroup bot" else 0)
        
        formatted_chats.append({
            'id': chat['id'],
            'partner': partner,
            'is_online': is_online,
            'last_time': chat['last_message_time']
        })
        
    active_chat_id = request.args.get('chat_id', type=int)
    active_messages = []
    active_partner = None
    
    if active_chat_id:
        chat_check = conn.execute('SELECT * FROM chats WHERE id = ? AND (user1 = ? OR user2 = ?)', 
                                  (active_chat_id, username, username)).fetchone()
        if chat_check:
            active_partner = chat_check['user2'] if chat_check['user1'] == username else chat_check['user1']
            active_messages = conn.execute('SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC', (active_chat_id,)).fetchall()
            
    conn.close()
    current_theme = session.get('theme', 'light')
    
    return render_template('messages.html', 
                           chats=formatted_chats, 
                           active_chat_id=active_chat_id, 
                           active_messages=active_messages, 
                           active_partner=active_partner,
                           logged_in_user=username,
                           theme=current_theme,
                           user_search=user_search)

@app.route('/send_message/<int:chat_id>', methods=['POST'])
def send_message(chat_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
        
    text = request.form.get('text', '').strip()
    if text:
        now_time = datetime.datetime.now().strftime('%H:%M')
        full_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (chat_id, sender, text, timestamp) VALUES (?, ?, ?, ?)',
                     (chat_id, username, text, now_time))
        conn.execute('UPDATE chats SET last_message_time = ? WHERE id = ?', (full_time, chat_id))
        conn.commit()
        conn.close()
        
    return redirect(url_for('messages_page', chat_id=chat_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Пароли не совпадают! Повторите ввод.', 'error')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            conn.close()
            flash('Этот никнейм уже занят! Выберите другой, чтобы зарегистрироваться.', 'error')
            return redirect(url_for('register'))
        
        reg_date = datetime.datetime.now().strftime('%d.%m.%Y')
        conn.execute('INSERT INTO users (username, password, reg_date, is_online) VALUES (?, ?, ?, 1)',
                     (username, password, reg_date))
        conn.commit()
        conn.close()
        
        send_bot_welcome(username)
        
        session['username'] = username
        session['user_reg_date'] = reg_date
        
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and user['password'] == password:
            conn.execute('UPDATE users SET is_online = 1 WHERE username = ?', (username,))
            conn.commit()
            conn.close()
            
            session['username'] = user['username']
            session['user_reg_date'] = user['reg_date']
            return redirect(url_for('index'))
        else:
            conn.close()
            flash('Неверный никнейм или пароль!', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username:
        conn = get_db_connection()
        conn.execute('UPDATE users SET is_online = 0 WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        
    session.pop('username', None)
    session.pop('user_reg_date', None)
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        session['theme'] = request.form.get('theme', 'light')
        session['notifications'] = 'notifs' in request.form
        return redirect(url_for('settings'))
    
    current_theme = session.get('theme', 'light')
    notifications = session.get('notifications', True)
    return render_template('settings.html', theme=current_theme, notifications=notifications)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
