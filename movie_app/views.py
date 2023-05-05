from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User, auth
from django.contrib import messages as msg
from .models import Profile, SearchHistory
from django.utils import timezone
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from pip._vendor import cachecontrol

from google.oauth2 import id_token
from google.auth.transport.requests import Request
from django.contrib.auth import login
import google.auth.transport.requests

import pickle
import requests
import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

flow = Flow.from_client_config(
        settings.GOOGLE_OAUTH_CLIENT_CONFIG,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", 'openid'],
        redirect_uri="http://localhost:8000/callback"
        # redirect_uri=request.build_absolute_uri('/auth/google/callback')
)

def google_login(request):

    authorization_url, state = flow.authorization_url()

    request.session['state'] = state
    return redirect(authorization_url)

def google_callback(request):
    state = request.session.pop('state', None)
    if state is None:
        return redirect('/')

    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    # Get the user's profile information from the Google API

    client_id = "532728207974-7vg5nna6vu3kvg4okjj9530j8hti9su0.apps.googleusercontent.com"
    idinfo = id_token.verify_oauth2_token(
        credentials.id_token, token_request, client_id
    )

    # Log in the user
    # print(idinfo)
    # print(idinfo['name'], idinfo['sub'])
    user = auth.authenticate(username = idinfo['name'], password=idinfo['sub'])
    if user is not None:
        request.session['username'] = idinfo['name']
        auth.login(request, user)
        return redirect('home')
    else:
        newuser = User.objects.create_user(username=idinfo['name'], password=idinfo['sub'])
        newuser.save()
        profile = Profile.objects.create(user=newuser, email=idinfo['email'])
        profile.save()

        auth.login(request, newuser)
        return redirect('home')

with open('movie_list.pkl', 'rb') as f:
    movies = pickle.load(f)

with open('similarity.pkl', 'rb') as s:
    similarity = pickle.load(s)

def add_search_history(query, user):
    search_history = SearchHistory(query=query, user=user, created_at=timezone.now())
    search_history.save()

def get_search_history(userName):
    return SearchHistory.objects.filter(username=userName).order_by('-created_at').values()

def landing(request):
    return redirect('login')

def login(request, user = "None"):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            request.session['username'] = username
            auth.login(request, user)
            return redirect('home')
        else:
            msg.info(request, 'Incorrect credentials')
            return redirect('/')
    else:
        return render(request, 'login.html')

def signUp(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        if User.objects.filter(username=username).exists():
            msg.info(request, 'Username already taken')
            return redirect('signup')
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            profile = Profile.objects.create(user=user, email=email)
            profile.save()
            return redirect('/')
    else:
        return render(request, 'signup.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

def fetch_yt(imdb_id):
    try:
        url= "https://api.themoviedb.org/3/movie/%s/videos?api_key=b67f4181f077fe214add89e512f1f575"%imdb_id
        data = requests.get(url)
        data_try = data.json()
        data= data_try['results']
        temp = None
    
        for i in data:
            
            if i['type'] == "Trailer":
           
                temp = i['key']
                break
        return temp
    except:
        return None

def popular_mov():
    url = "https://api.themoviedb.org/3/discover/movie?api_key=b67f4181f077fe214add89e512f1f575&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=true&page=1&with_watch_monetization_types=flatrate"
    data_try = requests.get(url)
    data_try = data_try.json()

    data= data_try['results']
    popular_movies= []
    popular_movies_poster= []
    popular_movies_back_poster= []
    popular_movies_id= []
    popular_movie_year=[]

    for i in data:
        path= "https://image.tmdb.org/t/p/original/%s"%i['poster_path']
        back_path= "https://image.tmdb.org/t/p/original/%s"%i['backdrop_path']

        popular_movies.append(i['original_title'])
        popular_movies_poster.append(path)
        popular_movies_back_poster.append(back_path)
        popular_movies_id.append(i['id'])

    return popular_movies, popular_movies_poster, popular_movies_back_poster ,  popular_movies_id      

def popular_movies_data(movie_name):
    
    url = "https://www.omdbapi.com/?t=%s&apikey=399a7c29"%movie_name
    data = requests.get(url)
    data = data.json()
    
    return data


def fetch_poster(imdb_id):

    url = "https://www.omdbapi.com/?i=%s&apikey=399a7c29"%imdb_id
    data = requests.get(url)
    data = data.json()

    poster_path= data.get('Poster')
    yt_link = fetch_yt(imdb_id)
    #full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return poster_path, data, yt_link

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]

    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    recommended_movie_data = []
    recommended_movie_ytLink = []

    for i in distances[0:8]:
        # fetch the movie poster
        imdb_id = movies.iloc[i[0]].imdb_id
        
        poster , data, yt_link = fetch_poster(imdb_id)

        recommended_movie_posters.append(poster)
        recommended_movie_names.append(movies.iloc[i[0]].title)
        recommended_movie_data.append(data)
        recommended_movie_ytLink.append(yt_link)
    return recommended_movie_names, recommended_movie_posters, recommended_movie_data, recommended_movie_ytLink

def merge2(list1, list2):
     
    merged_list = [(list1[i], list2[i]) for i in range(0, len(list1))]
    return merged_list


#popular series on tv

def popular_series():
    
    url ="https://api.themoviedb.org/3/trending/tv/week?api_key=b67f4181f077fe214add89e512f1f575"
    data_try = requests.get(url)
    data_try = data_try.json()

    data = data_try['results']

    pop_ser_name=[]
    pop_ser_id=[]
    pop_ser_poster=[]
    pop_ser_back_poster=[]
    for i in data:
        path= "https://image.tmdb.org/t/p/original/%s"%i['poster_path']
        back_path= "https://image.tmdb.org/t/p/original/%s"%i['backdrop_path']

        pop_ser_name.append(i['name'])
        pop_ser_poster.append(path)
        pop_ser_back_poster.append(back_path)
        pop_ser_id.append(i['id'])


    return pop_ser_name, pop_ser_poster, pop_ser_back_poster, pop_ser_id

def popular_series_ytlink(tv_id):

    url= "https://api.themoviedb.org/3/tv/%s/videos?api_key=b67f4181f077fe214add89e512f1f575&language=en-US"%tv_id
    data = requests.get(url)
    data_try = data.json()
    temp = None
    data = data_try['results']
    
        
    for i in data:
        
        if i['type'] == "Trailer":
            temp= i['key']
            break
    
    return temp

def cast_pics(code , id):
    
    if code == "movie":
        url ="https://api.themoviedb.org/3/movie/%s/credits?api_key=b67f4181f077fe214add89e512f1f575&language=en-US"%id
    
    else:
        url = "https://api.themoviedb.org/3/tv/%s/credits?api_key=b67f4181f077fe214add89e512f1f575&language=en-US"%id
    data_try = requests.get(url)
    data_try = data_try.json()


    data = data_try['cast']
    cast_name=[]
    cast_pic = []
    count =0
    for i in data:
        if i['known_for_department'] == 'Acting' and count<6:
            cast_name.append(i['name'])
            path="https://image.tmdb.org/t/p/original/%s"%i['profile_path']
            cast_pic.append(path)
            count += 1

    return cast_name, cast_pic

def home(request):
    pop_m, pop_m_path, pop_m_back_path, pop_m_id = popular_mov() 
    movies_list=movies['title']
    pop_movies= merge(pop_m, pop_m_path, pop_m_back_path, pop_m_id)

    request.session['pop'] = pop_movies

    #popular series
    pop_s, pop_s_path, pop_s_back_path, pop_s_id= popular_series()
    pop_series= merge(pop_s, pop_s_path, pop_s_back_path, pop_s_id)

    request.session['pop_s'] = pop_series
    tempt = get_search_history(request.session.get('username'))

    # print(tempt)

    return render(request,'index.html',{'movie_title':movies_list, 'pop_movie':pop_movies, 'pop_series':pop_series, 'search_history' : tempt})

@csrf_protect
def show_pop_series(request):
    if request.method == 'POST':
        series_name= request.POST.get('pop_series_button')
        
        
        temp = request.session['pop_s']

        series_data= popular_movies_data(series_name)
        
        count =0
        for i in temp:
           if i[0]== series_name:
                break
           else:
               count = count + 1
        series_yt = popular_series_ytlink(temp[count][3])

        cast_name, cast_photo= cast_pics("series", temp[count][3])

        cast_info= merge2(cast_name, cast_photo)
        series_back_poster= temp[count][2]
        series_poster = temp[count][1]
        username = request.session.get('username')
        seriesdata = {'data_of_clicked':series_data, 'yt_link': series_yt, 'poster':series_poster,'back_path':series_back_poster , 'cast_info':cast_info}
        # print("####################################")
        # print(username)
        db_obj = SearchHistory.objects.create(username = username, data = seriesdata, type = "Series")
        db_obj.save()
        return render(request,'data_fetching.html',seriesdata)



def show_pop_data(request):
    if request.method == 'POST':
        movie_name = request.POST.get('pop_button')
        list_of_data = request.session['pop']
         
        pop_data= popular_movies_data(movie_name)
        
        
        count = 0

        for i in list_of_data:
           if i[0]== movie_name:
                break
           else:
               count = count + 1
    
        pop_yt_id = fetch_yt(list_of_data[count][3])
        cast_name, cast_photo= cast_pics("movie" , list_of_data[count][3])

        cast_info= merge2(cast_name, cast_photo)
        # user_name = Profile.objects.filter()
        pop_mov_back_poster= list_of_data[count][2]
        pop_mov_poster= list_of_data[count][1]
        data = {'data_of_clicked':pop_data, 'yt_link': pop_yt_id, 'poster':pop_mov_poster,'back_path': pop_mov_back_poster, 'cast_info':cast_info}
        username = request.session.get('username')
        # print("####################################")
        # print(username)
        db_obj = SearchHistory.objects.create(username = username, data = data, type = "Movie")
        db_obj.save()
        return render(request,'data_fetching.html', data)
    else:
        return HttpResponse("ERROR")
    


def merge(list1, list2, list3, list4):
     
    merged_list = [(list1[i], list2[i], list3[i], list4[i]) for i in range(0, len(list1))]
    return merged_list

def show(request):
    if request.method == 'POST':
        movie_name = request.POST.get('searches')
        recommended_movie_names= [] 
        recommended_movie_posters =[]
        recommended_movie_data=[]
        recommended_movie_ytLink=[]
        pop_series_data = request.session['pop_s']
        recommended_movie_names, recommended_movie_posters, recommended_movie_data, recommended_movie_ytLink = recommend(movie_name)
        list_of_data = merge(recommended_movie_names, recommended_movie_posters, recommended_movie_data, recommended_movie_ytLink)
        request.session['list'] = list_of_data
        # print(pop_series_data)
        return render(request, 'search_results.html',{'data': list_of_data, 'pop_series' : pop_series_data})
    else:
        return HttpResponse("ERROR")

def data(request):
    temp = 0
    if request.method == 'POST':
        movie_name = request.POST.get('img_button', None)
        list_of_data = request.session['list']
        # recommended_movie_names, recommended_movie_posters, recommended_movie_data = recommend(movie_name)
        count=0
        for i in list_of_data:
            if(i[0]==movie_name):
                temp= count
                break
            else:
                count= count+1

        dict_of_data= list_of_data[temp][2]
        yt_of_data= list_of_data[temp][3]
        imdb_id = dict_of_data['imdbID']
        cast_name, cast_pic= cast_pics("movie", imdb_id)
        cast_info= merge2(cast_name, cast_pic)
        # index_of_clicked= 0
        # cnt=0
        # for i in recommended_movie_data:
        #     print(i['Title'])
        #     if i['Title']==movie_name:
        #        index_of_clicked=cnt
        #        print("Matched \n")
        #        break
        #     else:
        #         cnt=cnt+1
        
        #data_of_clicked = recommended_movie_data[index_of_clicked]


        return render(request,'data_fetching.html',{'data_of_clicked': dict_of_data , 'yt_link':yt_of_data, 'cast_info': cast_info})

# temp = SearchHistory.objects.filter(username = tempt).values()
# for i in temp:
#     print(i)