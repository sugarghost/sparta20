import re

import jwt
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import certifi

SECRET_KEY = 'sparta20'

client = MongoClient('mongodb+srv://test:sparta@cluster0.2rz7w.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=certifi.where())
# client = MongoClient('localhost', 27017)
db = client.netflix_comment
home = Blueprint('home', __name__)


# #jwt id 값 모듈화
def GetJwtId():
    # token_check()
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.User.find_one({"id": payload['id']})
    return user_info['id']


# home 라우터 (컨텐츠 디비에서 가져온 후 보여줌)
@home.route('/home')
def main():
    # r = requests.get('http://127.0.0.1:5000/movies')
    # response = r.json()
    # movie_title = response['movie_title']
    # movie_image = response['movie_image']
    # movie_href = response['href']
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('home.html')

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login_page", msg="로그인 시간이 만료되었습니다."))

    except jwt.exceptions.DecodeError:
        return redirect(url_for("login_page", msg="로그인 정보가 존재하지 않습니다."))



    return render_template('home.html')


# 모든 컨텐츠 디비에서 가져오고 즐겨찾기 인덱스 반환
@home.route("/movies")
def read_movies():
    # 사용자 즐겨찾기 목록
    id = GetJwtId()
    dbid = db.User.find_one({'id': id})
    fav = db.User.find_one({'id': dbid['id']})

    # 모든 영화 목록
    movies = list(db.movie.find({}, {'_id': False}))

    # 일치하는지 확인 후 인덱스 배열 반환
    fav_list = fav['fav']
    title = []
    tmp = []
    for i in movies:
        title.append(i['movie_title'])
    for i in fav_list:
        tmp.append(title.index(i))
    return jsonify(
        {'all_movies': movies, "fav": tmp}
    )


# 사용자 즐겨찾기 목록 가져오기
@home.route('/check_bookmark', methods=['GET'])
def read_bookmark():
    id = GetJwtId()
    dbid = db.User.find_one({'id': id})
    fav = db.User.find_one({'id': dbid['id']})
    return jsonify({"fav": fav['fav']})


# 모든 컨텐츠 디비에 저장 (❗️한 번만 실행되야함)
@home.route("/save_movies")
def save_movies():
    url = 'https://www.justwatch.com/kr/%EB%8F%99%EC%98%81%EC%83%81%EC%84%9C%EB%B9%84%EC%8A%A4/netflix'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url, headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')

    new_tags = soup.select(
        '#base > div.title-list.title-list--CLS-block > div div:nth-child(2) > div:nth-child(1) > div > div > a')

    #db전부 삭제 후 진행
    db.movie.delete_many({})
    # 컨텐츠 각 항목에 접근 후 디비에 저장
    for tags in new_tags:
        title = tags.img.get('alt')
        href_tag = re.sub('/kr', '/detail', tags['href'])
        star = 0
        if tags.img.get('data-src'):
            src = tags.img.get('data-src')
        else:
            src = tags.img.get('src')

        doc = {
            'movie_title': title,
            'movie_image': src,
            'href': href_tag,
            'star': star,
        }

        db.movie.insert_one(doc)
    return redirect(url_for('home.main'))
    # return jsonify({'msg': '성공'})
