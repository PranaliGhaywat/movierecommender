import time
import requests
from flask import Flask, render_template, request
import pickle
from requests.exceptions import RequestException

app = Flask(__name__)

# Load pre-saved data
movie_name_list = pickle.load(open("movie_list.pkl", "rb"))
similar = pickle.load(open("Cos_similarity.pkl", "rb"))




def fetch_poster(id):
    url = f"https://api.themoviedb.org/3/movie/{id}/images?api_key=8fcfde04dd3861aeebecf2a298331762"
    headers = {
        'accept': 'application/json'
    }

    # Retry logic: try up to 3 times if connection is reset or times out
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)  # Set a timeout (e.g., 10 seconds)
            response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)

            data = response.json()
            if 'backdrops' in data and data['backdrops']:
                poster_path = data['backdrops'][0]["file_path"]
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
            else:
                return "Poster not available"  # Return a fallback message if no backdrops found

        except RequestException as e:
            # Log the error for debugging purposes (e.g., print to console or log to a file)
            print(f"Error fetching poster (Attempt {attempt + 1}): {e}")

            # Wait for a short period before retrying (e.g., 2 seconds)
            time.sleep(20)

    # If all attempts fail, return a generic error message
    return "Failed to fetch poster after multiple attempts"

@app.route('/')
def home():
    # Render the homepage with a dropdown of movie titles
    return render_template('index_sir.html', movies=movie_name_list['original_title'].values)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get movie title from the form
        movie_title = request.form.get('M_title')
        if not movie_title:
            return render_template('index_sir.html', movies=movie_name_list['original_title'].values, error="No movie title provided.")

        # Find the movie index
        movie_index = movie_name_list[movie_name_list['original_title'] == movie_title].index
        if len(movie_index) == 0:
            return render_template('index_sir.html', movies=movie_name_list['original_title'].values, error="Movie not found in the database.")

        movie_index = movie_index[0]

        # Calculate similarity scores and get top recommendations
        similarity_scores = list(enumerate(similar[movie_index]))
        sorted_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        top_movies = [movie_name_list.iloc[i[0]].original_title for i in sorted_scores[1:6]]
        pos = [fetch_poster(movie_name_list.iloc[i[0]].id) for i in sorted_scores[1:6]]

        return render_template('index_sir.html', movies=movie_name_list['original_title'].values, rec_movies=top_movies, posters=pos)

    except Exception as e:
        # Handle unexpected errors
        return render_template('index_sir.html', movies=movie_name_list['original_title'].values, error=str(e))

@app.template_filter('zip')
def zip_lists(list1, list2):
    """A custom filter to zip two lists together."""
    return zip(list1, list2)



if __name__ == "__main__":
    app.run(debug=True)
