from flask import Flask, request, jsonify, abort
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from .config import Config
from .models import db, Rating, Index

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
Migrate(app, db)

@app.before_request
def to_allowed_host():
    # if request.remote_addr != '127.0.0.1':
    #     abort(403)
    if 'host.docker.internal' not in request.url_root:
        abort(403)

@app.route("/")
def main():
  return "Hello!"


@app.route("/ratings/<int:book_id>")
def book_rating(book_id):
  ratings = Rating.query.filter(Rating.book_id == book_id).all()
  book_ratings = [rating.value for rating in ratings]

  if not book_ratings:
    return 'No ratings for this book yet.'

  rating_values = [{"value": rating} for rating in book_ratings ]
  average_rating = round(sum(book_ratings)/len(book_ratings), 2)

  return {"average": average_rating, "ratings": rating_values}

@app.route('/ratings/<int:book_id>', methods=['POST'])
def post_book_ratings(book_id):
    if not request.args:
        error_response = {'error': 'Bad data'}
        return jsonify(error_response), 400

    is_missing_args = not 'value' in request.args or not 'email' in request.args
    if is_missing_args:
        error_response = {'error': 'Missing arguments'}
        return jsonify(error_response), 400

    try:
        new_rating = {
            'id': len(Rating.query.all()) + 1,
            'book_id': book_id,
            'value': int(request.args.get('value')),
            'email': request.args.get('email')
        }
        rating = Rating(**new_rating)
        db.session.add(rating)
        db.session.commit()
        return jsonify(new_rating)
    except IntegrityError as e:
        print(e)
        error_response = {'error': 'Each user can only submit one rating per book.'}
        return jsonify(error_response), 400
