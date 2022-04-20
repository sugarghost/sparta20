# 강돌이

import hashlib
import datetime
from datetime import datetime, timedelta
import jwt  #패키지 PyJWT
from flask import Flask, render_template,jsonify, request,redirect,url_for
from pymongo import MongoClient
from home import home,main,save_movies
import certifi

from detail import detail


#암호화 키 / JWT 토큰을 사용할때 쓰는 비밀문자열
SECRET_KEY = 'sparta20'

client = MongoClient('mongodb+srv://test:sparta@cluster0.2rz7w.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=certifi.where())
# client = MongoClient('localhost', 27017)
db = client.netflix_comment
app = Flask(__name__)

app.register_blueprint(home)
app.register_blueprint(detail)

#jwt 체크 함수 모듈화 테스트중
def token_check():
    print('token_check')
    # token_receive = request.cookies.get('mytoken')
    # try:
    #     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    #     user_info = db.user.find_one({"id": payload['id']})
    #     return user_info['id']
    # except jwt.ExpiredSignatureError:
    #     print('로그인 시간만료')
    #     return redirect(url_for('main_page'))
    # except jwt.exceptions.DecodeError:
    #     print('로그인 정보 없음')
    #     return redirect(url_for('main_page'))


#메인페이지 로그인정보가있다면 홈으로 이동 아니면 로그인이동
@app.route('/')
def main_page():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.User.find_one({"id": payload['id']})

        # return render_template('detail.html')
        return redirect(url_for('home.main'))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login_page", msg="로그인 시간이 만료되었습니다."))

    except jwt.exceptions.DecodeError:
        return redirect(url_for("login_page", msg="로그인 정보가 존재하지 않습니다."))


#jwt id 값 모듈화
def GetJwtId():
    # token_check()
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.User.find_one({"id": payload['id']})
    return user_info['id']

# def token_check():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_info = db.User.find_one({"id": payload['id']})
#         return render_template('detail.html')
#
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login_page", msg="로그인 시간이 만료되었습니다."))
#
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login_page", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/')
def hello_world():  # put application's code here
    return redirect(url_for('login_page'))

# 로그인라우터
@app.route('/login', methods=['GET'])
def login_page():
    print('로그인 페이지 접속')

    msg = request.args.get("msg")
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
        user_info = db.User.find_one({"id":payload['id']})
        return redirect(url_for('home.main'))
        # return redirect(url_for('home_router.home'))

        # return redirect(url_for('home.main'))
    except jwt.ExpiredSignatureError:
        return render_template('login.html',msg=msg)
    except jwt.exceptions.DecodeError:
        return render_template('login.html',msg=msg)
    # except:
    #     return render_template('login.html',msg=msg)

# 회원가입 api
@app.route('/api/register',methods=['POST'] )
def register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # pwc_receive = request.form['pwc_give']
    #필요없나?

    #sha256방법으로 암호화해서 저장
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    doc = {
        'id':id_receive,
        'pw':pw_hash,
        'fav' : []
    }
    db.User.insert_one(doc)

    return jsonify({'msg':id_receive})

#즐겨찾기 추가
@app.route('/api/addfavorite', methods = ['POST'])
def addfavorite():
    fav = request.form['favorite_give']
    id = GetJwtId()
    dbid = db.User.find_one({'id':id})
    db.User.update_one({'id':dbid['id']},{'$push':{'fav':{'$each':[fav],'$position':0}}})
    # {'$push':  {'a': 5},'$position': 0}


    return jsonify({'msg':fav})

#즐겨찾기 삭제
@app.route('/api/delfavorite', methods = ['POST'])
def delfavorite():
    fav = request.form['favorite_give']
    id = GetJwtId()
    dbid = db.User.find_one({'id':id})
    db.User.update_one({'id':dbid['id']},{'$pull':{'fav':fav}})


    return jsonify({'msg':fav})




#회원가입 ID중복 확인
@app.route('/id_dup_check',methods=['POST'])
def id_dup_check():
    id = request.form['id_give']
    dup_check = bool(db.User.find_one({'id':id}))
    return jsonify({'msg':dup_check})

#로그인 성공 시 무비 데이터 로드하러 이동
@app.route('/api/login', methods=['POST'])
def login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    result = db.User.find_one({'id':id_receive,'pw':pw_hash})

    if result is not None:
        payload = {
            'id' : id_receive,
            'exp' : datetime.utcnow() + timedelta(seconds = 60 * 60 * 24) #24시간 유지
            # 'exp' : datetime.utcnow() + timedelta(seconds = 30) #test
            # 'exp' : datetime.utcnow() + timedelta(seconds = 5) #test
        }
        token = jwt.encode(payload,SECRET_KEY, algorithm='HS256')


        from home import save_movies
        # return redirect(url_for('home.save_movies'),{'result':'success','token':token})

        return jsonify({'result':'success','token':token})
    #로그인 실패 시(아이디/비번 다름)
    else:
        return jsonify({'result':'fail','msg':'아이디/비밀번호가 일치하지 않습니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
