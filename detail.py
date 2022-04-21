import time
import urllib

from flask import render_template, Blueprint, request, jsonify,redirect,url_for
import requests
from bs4 import BeautifulSoup
from urllib import parse
import datetime
import certifi






from pymongo import MongoClient
import jwt  #패키지 PyJWT
SECRET_KEY = 'sparta20'

client = MongoClient('mongodb+srv://test:sparta@cluster0.2rz7w.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=certifi.where())
# client = MongoClient('localhost', 27017)
db = client.netflix_comment

detail = Blueprint('detail', __name__)

# 사용자가 home 화면에서 영화를 클릭 시 호출되는 기능
@detail.route('/detail/<category>/<movie_name>')
def main(movie_name, category):
    from app import GetJwtId
    TokenUserId = GetJwtId()

    #파이썬에서 전달된 한글값으로 url 생성시 오류가 나기 때문에 퍼센트 인코딩을 진행
    movie_name = urllib.parse.quote(movie_name, safe='')
    category = parse.quote(category)
    # 처리된 퍼센트 인코딩으로 링크를 연결함
    url = f'https://www.justwatch.com/kr/{category}/{movie_name}'

    #영화에 대한 설명을 가져오기 위해 생성한 url 정보로 사이트를 접근
    data = requests.get(url)
    soup = BeautifulSoup(data.text, 'html.parser')

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})

        #변수를 global로 만들어 다른 함수에서도 현재 영화 제목을 참조할 수 있도록 설정
        global movieTitle
        movieTitle = soup.select_one(
            '#base > div.jw-info-box > div > div.jw-info-box__container-content > div:nth-child(2) > div.title-block__container > div.title-block > div').text
        print("movieTitle = " + movieTitle)

        if (movieTitle) != 'None':
            movieTitle = movieTitle
        else:
            movieTitle = ""

        movieGenre = soup.select_one(
            '#base > div.jw-info-box > div > div.jw-info-box__container-sidebar > div > aside > div.hidden-sm.visible-md.visible-lg.title-sidebar__desktop > div.title-info > div:nth-child(3) > div.detail-infos__value').text
        print("movieGenre = " + movieGenre)

        if (movieGenre) != 'None':
            movieGenre = movieGenre
        else:
            movieGenre = ""

        movieTime = soup.select_one(
            '#base > div.jw-info-box > div > div.jw-info-box__container-sidebar > div > aside > div.hidden-sm.visible-md.visible-lg.title-sidebar__desktop > div.title-info > div:nth-child(4) > div.detail-infos__value').text
        print("movieTime = " + movieTime)

        if (movieTime) != 'None':
            movieTime = movieTime
        else:
            movieTime = ""


        movieMainThumbnail = soup.select_one(
            '#base > div.backdrops > div > div > div:nth-child(2) > picture > img')
        print("dramaMainThumbnail = " + str(movieMainThumbnail))

        movieMainThumbnail2 = soup.select_one(
            '#base > div.backdrops.backdrops__carousel > div > div.swiper-container > div > div.swiper-slide.swiper-slide-active > picture > img')
        print("movieMainThumbnail2 = "+ str(movieMainThumbnail2))

        movieMainThumbnail3 = soup.select_one(
             '#base > div.backdrops.backdrops__carousel > div > div.swiper-container > div > div > picture > img')
        print("movieMainThumbnail3 = "+ str(movieMainThumbnail3))

        if str(movieMainThumbnail) != 'None':
            movieMainThumbnail = movieMainThumbnail["src"]

        elif str(movieMainThumbnail2) != 'None':
            movieMainThumbnail = movieMainThumbnail2["src"]
        elif str(movieMainThumbnail3) != 'None':
            movieMainThumbnail = movieMainThumbnail3["src"]
        else:
            movieMainThumbnail = ""


        movieImage = soup.select_one(
            '#base > div.jw-info-box > div > div.jw-info-box__container-sidebar > div > aside > div.hidden-xs.visible-sm.hidden-md.hidden-lg.title-sidebar__desktop > div > picture > source:nth-child(1)')[
            "data-srcset"].split(',')[0]

        if(movieImage) !='None':
            movieImage = movieImage
        else:
            movieImage = ""

        ###base > div.jw-info-box > div > div.jw-info-box__container-sidebar > div > aside > div.hidden-sm.visible-md.visible-lg.title-sidebar__desktop > div.title-poster.title-poster--no-radius-bottom > picture > source:nth-child(1)
        print("movieImage = " + movieImage)

        movieSummary = soup.select_one(
            '#base > div.jw-info-box > div > div.jw-info-box__container-content > div:nth-child(2) > div:nth-child(6) > div:nth-child(1) > div:nth-child(4) > p > span')

        dramaSummary = soup.select_one(
            '#base > div.jw-info-box > div > div.jw-info-box__container-content > div:nth-child(2) > div:nth-child(7) > div:nth-child(1) > div:nth-child(4) > p > span')



        if str(movieSummary) != 'None':
            movieSummary = movieSummary.text
            print(movieSummary)

        elif str(dramaSummary) != 'None':
            movieSummary = dramaSummary.text
            print(dramaSummary)
        else:
            movieSummary = ""

        #현재 참조중인 영화 제목에 연결된 리뷰를 불러옴
        read_reviews()
        
        # 과정중에 참조한 데이터들을 전부 묶어서 detail.html 페이지를 불러줌
        return render_template('detail.html', TokenUserId=TokenUserId, movieTitle=movieTitle, movieGenre=movieGenre,
                               movieTime=movieTime,
                               movieSummary=movieSummary, movieImage=movieImage,movieMainThumbnail=movieMainThumbnail, reviews=reviews)

        


    except jwt.ExpiredSignatureError:
        print('로그인 시간만료')
        return redirect(url_for('login_page'))
    except jwt.exceptions.DecodeError:
        print('로그인 정보 없음')
        return redirect(url_for('login_page'))

@detail.route('/review', methods=['POST'])
def write_review():
    from app import GetJwtId
    global TokenUserId
    TokenUserId = GetJwtId()
    now = datetime.datetime.now()
    review = request.form['Review']
    review = review.replace("  ", " ")
    starValue = request.form['starValue']
    movietitle = request.form['movieTitle']

    if starValue != "" and review != "":
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

        doc = {
            'userId': TokenUserId,
            'Review': review,
            'starValue': starValue,
            'movieTitle': movietitle,
            'nowDatetime': nowDatetime
        }
        db.review.insert_one(doc)
        return jsonify({'msg': '리뷰 등록 완료'})


@detail.route('/review', methods=['GET'])
def read_reviews():
    global reviews
    reviews = list(db.review.find({"movieTitle": movieTitle}, {'_id': False}))
    print(reviews)
    return jsonify({'msg': '리뷰 조회'})


@detail.route('/review', methods=['Delete'])
def del_reviews():
    from app import GetJwtId
    TokenUserId = GetJwtId()
    userId = request.form['userid']
    Review = request.form['review']
    starValue = request.form['starValue']
    nowDatetime = request.form['writeTime']
    if (TokenUserId == userId):
        db.review.delete_one({'userId': userId, 'nowDatetime': nowDatetime, 'Review': Review, 'starValue': starValue})
        review = db.review.find({'movieTitle': movieTitle})
        print(review)
        return jsonify({'msg': '삭제완료'})
    else:
        return jsonify({'msg': '본인이 작성한 리뷰만 삭제가능합니다.'})


@detail.route('/review', methods=['Put'])
def update_reviews():
    from app import GetJwtId
    TokenUserId = GetJwtId()
    userId = request.form['userid']
    Review = request.form['review']
    starValue = request.form['starValue']
    nowDatetime = request.form['writeTime']
    updateReview = request.form['updateReview']
    updateStarValue = request.form['updateStarValue']
    print("userId = " + userId + "Review = " + Review + "starValue = " + starValue + "nowDatetime = " + nowDatetime)
    if (TokenUserId == userId):
        db.review.update_one({'userId': userId, 'nowDatetime': nowDatetime, 'Review': Review, 'starValue': starValue},
                             {'$set': {'Review': updateReview, 'starValue': updateStarValue}})
        review = db.review.find({'movieTitle': movieTitle})
        print(review)
        return jsonify({'msg': '수정완료'})
    else:
        return jsonify({'msg': '본인이 작성한 리뷰만 수정가능합니다.'})


@detail.route('/allReview', methods=['GET'])
def read_all_Reviews():
    global reviews
    reviews = list(db.review.find({}, {'_id': False}))
    print(reviews)
    return jsonify({'reviews': reviews})
