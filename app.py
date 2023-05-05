import pickle
import streamlit as st
import pandas
import requests
def fetch_poster(imdb_id):
    # poster_path = ""
    # for i in movies:
    #       if imdb_id==i['imdb_id']:
    url = "https://www.omdbapi.com/?i=%s&apikey=399a7c29"%imdb_id
    data = requests.get(url)
    data = data.json()

    poster_path= data.get('Poster')
    return poster_path

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:8]:
        # fetch the movie poster
        imdb_id = movies.iloc[i[0]].imdb_id
        recommended_movie_posters.append(fetch_poster(imdb_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names,recommended_movie_posters


st.header('Movie Recommender System')
movies = pickle.load(open(r'C:\Users\ACER\Desktop\mpr\movie_list.pkl','rb'))
similarity = pickle.load(open(r'C:\Users\ACER\Desktop\mpr\similarity.pkl','rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names,recommended_movie_posters = recommend(selected_movie)
    col1, col2, col3, col4, col5 , col6, col7= st.beta_columns(7)
    with col1:
        st.text(recommended_movie_names[0])
        st.image(recommended_movie_posters[0])
    with col2:
        st.text(recommended_movie_names[1])
        st.image(recommended_movie_posters[1])

    with col3:
        st.text(recommended_movie_names[2])
        st.image(recommended_movie_posters[2])
    with col4:
        st.text(recommended_movie_names[3])
        st.image(recommended_movie_posters[3])
    with col5:
        st.text(recommended_movie_names[4])
        st.image(recommended_movie_posters[4])
    with col6:
        st.text(recommended_movie_names[5])
        st.image(recommended_movie_posters[5])
    with col7:
        st.text(recommended_movie_names[6])
        st.image(recommended_movie_posters[6])