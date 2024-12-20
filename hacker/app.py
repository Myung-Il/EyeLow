from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect('test2.db')
    cursor = conn.cursor()

    # 테이블 생성 스크립트 실행
    cursor.executescript("""
    -- 유저 테이블 생성
    CREATE TABLE IF NOT EXISTS User (
        nickname TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        id TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );

    -- 학습 데이터 저장 테이블 생성
    CREATE TABLE IF NOT EXISTS TrainingData (
        nickname TEXT NOT NULL,
        title TEXT NOT NULL,
        explanation TEXT,
        code TEXT,
        output TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (title),
        FOREIGN KEY (nickname) REFERENCES User(nickname) ON DELETE CASCADE
    );

    -- 게시글 저장 테이블 생성
    CREATE TABLE IF NOT EXISTS Posts (
        title TEXT PRIMARY KEY,
        nickname TEXT NOT NULL,
        content TEXT NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (nickname) REFERENCES User(nickname) ON DELETE CASCADE
    );

    -- 댓글 저장 테이블 생성                     
    CREATE TABLE IF NOT EXISTS Comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_title TEXT NOT NULL,
        nickname TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_title) REFERENCES Posts(title) ON DELETE CASCADE,
        FOREIGN KEY (nickname) REFERENCES User(nickname) ON DELETE CASCADE
    );
    """)

    # 변경 사항 저장 및 연결 닫기
    conn.commit()
    conn.close()


# Flask 애플리케이션 생성
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 홈 페이지 라우트
@app.route('/', methods=['GET'])    
def home():
    return redirect(url_for('login'))

# 메인 페이지 라우트
@app.route('/main', methods=['GET', 'POST'])
def user_main():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_nickname = session['user']
    
    return render_template('main.html', user=user_nickname)

# 로그아웃 라우트
@app.route('/logout', methods=['GET'])
def logout():   
    session.pop('user', None)
    return redirect(url_for('login'))

# 로그인 페이지 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user_id = data.get('id')
        password = data.get('password')

        if not user_id or not password:
            return render_template('login.html', error="ID and password are required.")

        conn = sqlite3.connect('test2.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nickname, password, email FROM User WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        print(user)
        if user and check_password_hash(user[1], password):
            session['user'] = user[0]  # 세션에 닉네임 저장
            session['email'] = user[2]
            return redirect(url_for('user_main'))
        else:
            return render_template('login.html', error="Invalid ID or password.")

    return render_template('login.html')

# 회원가입 페이지 라우트
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        nickname = data.get('nickname')
        email = data.get('email')
        id = data.get('id')
        password = data.get('password')

        conn = sqlite3.connect('test2.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nickname, password FROM User WHERE id = ?", (user_id,))
        user = cursor.fetchone()


        if not nickname or not id or not password:
            return jsonify({"error": "Nickname, email, ID, and password are required."}), 400

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('test2.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO User (nickname, email, id, password) VALUES (?, ?, ?, ?)", (nickname, email, id, hashed_password))
            conn.commit()
            conn.close()
            return redirect("http://orion.mokpo.ac.kr:8473/login")
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Nickname or ID already exists.")

    return render_template('register.html')

@app.route('/unit1')
def unit1():
    return render_template('unit1.html')
@app.route('/unit2')
def unit2():
    return render_template('unit2.html')

# 학습 페이지 라우트
@app.route('/learn', methods=['GET', 'POST'])
def learn():
    if request.method == 'POST':
        # 폼에서 입력된 데이터 가져오기
        nickname = session['user']
        title = request.form.get('title')
        explanation = request.form.get('explanation')
        code = request.form.get('code')
        output = request.form.get('output')

        # DB 연결 및 데이터 삽입
        conn = sqlite3.connect('test2.db')
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO TrainingData (nickname, title, explanation, code, output)
                VALUES (?, ?, ?, ?, ?)
            """, (nickname, title, explanation, code, output))
            conn.commit()
        except sqlite3.IntegrityError:
            # 중복된 title로 인한 에러 처리
            return render_template('learn.html', error="This title already exists.")
        finally:
            conn.close()

        return redirect(url_for('learn'))

    # GET 요청일 경우 HTML 페이지 렌더링
    return render_template('learn.html')


@app.route('/review', methods=['GET', 'POST'])
def review():
    # 기본 쿼리 (최신 순으로 가져오기)
    query = "SELECT title, nickname, explanation, created_at FROM TrainingData ORDER BY created_at DESC"
    items = fetch_data(query)  # fetch_data 함수로 데이터 가져오기

    # POST 요청 처리
    if request.method == 'POST':
        # 검색 처리
        

        # 삭제 처리
        if 'delete' in request.form:
            selected_titles = request.form.getlist('item[]')  # 체크된 항목 가져오기
            print("Selected titles for deletion:", selected_titles)  # 디버깅: 서버로 넘어온 title 출력
            if selected_titles:
                delete_query = "DELETE FROM TrainingData WHERE title = ?"
                conn = sqlite3.connect('test2.db')
                cursor = conn.cursor()

                try:
                    for title in selected_titles:
                        print(f"Deleting title: {title}")  # 디버깅: 어떤 title을 삭제할지 출력
                        cursor.execute(delete_query, (title,))

                    conn.commit()  # 변경 사항 커밋
                    print("Delete successful")  # 디버깅: 삭제 성공 메시지
                except Exception as e:
                    print(f"Error during delete: {e}")  # 예외 처리 및 로그
                    conn.rollback()  # 오류 발생 시 롤백
                finally:
                    conn.close()

                return redirect(url_for('review'))  # 페이지 새로고침

        # Sort 처리
        elif 'sort' in request.form:
            # 이름(타이틀)순으로 정렬
            query = "SELECT title, nickname, explanation, created_at FROM TrainingData ORDER BY title ASC"
            items = fetch_data(query)  # 이름(타이틀)순으로 정렬된 데이터 가져오기

        elif 'search' in request.form:
            search_query = request.form['search']
            print("Search query:", search_query)  # 디버깅: 검색어 출력
            if search_query:
                # title 컬럼에서 검색어가 포함된 항목만 가져오기
                query = "SELECT title, nickname, explanation, created_at FROM TrainingData WHERE title LIKE ? ORDER BY created_at DESC"
                items = fetch_data(query, ('%' + search_query + '%',))  # %를 사용하여 부분 일치를 찾음

    # 템플릿 렌더링
    return render_template('review.html', items=items)


def get_all_data():
    query = "SELECT nickname, commend, role, code, output, created_at FROM TrainingData"  # created_at 추가
    return fetch_data(query)

def fetch_data(query, params=None):
    connection = sqlite3.connect('test2.db')  # 데이터베이스 파일명 확인
    connection.row_factory = sqlite3.Row  # 결과를 딕셔너리 형태로 반환
    cursor = connection.cursor()
    cursor.execute(query, params or [])
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


def get_db_connection():
    connection = sqlite3.connect('test2.db')  # SQLite 데이터베이스 파일 경로
    connection.row_factory = sqlite3.Row  # 결과를 딕셔너리 형태로 받기 위해 설정
    return connection

@app.route('/check_answer/<string:title>', methods=['POST'])
def check_answer(title):
    user_answer = request.form.get('user_answer')  # 사용자가 입력한 정답
    query = "SELECT nickname, title, explanation, code, output, created_at FROM TrainingData WHERE title = ?"
    result = fetch_data(query, (title,))
    
    if result:
        item = result[0]
        correct_answer = item['output']
        if user_answer.strip() == correct_answer.strip():  # 정답 확인
            message = "Correct! Great job."
        else:
            message = "Wrong! Try again"
        
        # 문제와 메시지를 함께 렌더링
        return render_template('detail.html', item=item, message=message)
    else:
        return "Item not found", 404


# 커뮤니티 페이지 라우트
@app.route('/community')
def community():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM Posts ORDER BY created_at DESC').fetchall()  # 최신 게시물 우선
    conn.close()
    return render_template('community.html', posts=posts)

# 게시물 상세 페이지
@app.route('/post/<string:title>')
def post(title):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM Posts WHERE title = ?', (title,)).fetchone()  # 특정 게시물 가져오기
    comments = conn.execute('SELECT * FROM Comments WHERE post_title = ?', (title,)).fetchall()  # 해당 게시물의 댓글들 가져오기
    conn.close()
    return render_template('post_detail.html', post=post, comments=comments)

# 댓글 작성 처리
@app.route('/post/<string:title>/comment', methods=['POST'])
def comment(title):
    nickname = session['user']
    content = request.form['content']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO Comments (post_title, nickname, content) VALUES (?, ?, ?)', (title, nickname, content))
    conn.commit()
    conn.close()
    
    return redirect(f'/post/{title}')  # 댓글 작성 후 해당 게시물 상세 페이지로 리디렉션

# 새로운 게시물 작성 페이지
@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        nickname = session['user']
        comments = ""
        
        conn = get_db_connection()
        conn.execute('INSERT INTO Posts (title, content, nickname, comments) VALUES (?, ?, ?, ?)', (title, content, nickname, comments))
        conn.commit()
        conn.close()
        
        return redirect('/community')  # 새 게시물 작성 후 게시물 목록 페이지로 리디렉션
    
    return render_template('new_post.html')

# 게시물 상세 페이지
@app.route('/post/<string:title>', methods=['GET', 'POST'])
def post_detail(title):
    conn = get_db_connection()
    
    # 게시물 가져오기
    post = conn.execute('SELECT * FROM Posts WHERE title = ?', (title,)).fetchone()
    if not post:
        conn.close()
        return "Post not found", 404

    # 댓글 작성 처리
    if request.method == 'POST':
        nickname = session['user']
        comment = request.form.get('comment')

        if not comment:
            conn.close()
            return render_template('post_detail.html', post=post, comments=[], error="Comment cannot be empty.")

        conn.execute("""
            INSERT INTO Comments (post_title, nickname, comment)
            VALUES (?, ?, ?)
        """, (title, nickname, comment))
        conn.commit()

    # 댓글 가져오기
    comments = conn.execute('SELECT * FROM Comments WHERE post_title = ? ORDER BY created_at ASC', (title,)).fetchall()
    conn.close()

    return render_template('post_detail.html', post=post, comments=comments)



@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

#@app.route('/unit1')
#def unit1():
#    return render_template('unit1.html')

#@app.route('/unit2')
#def unit2():
#    return render_template('unit2.html')

@app.route('/detail/<string:title>', methods=['GET'])
def detail(title):
    query = "SELECT nickname, title, explanation, code, output, created_at FROM TrainingData WHERE title = ?"
    item = fetch_data(query, (title,))
    
    if item:
        return render_template('detail.html', item=item[0])  # 첫 번째 결과 전달
    else:
        return "Item not found", 404


@app.route('/alart')
def alart():
    email = session['email']
    
    return render_template('alart.html', email=email)



if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=3000)
