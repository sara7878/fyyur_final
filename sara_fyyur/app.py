
#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
#SARA

import logging
import sys
from logging import FileHandler, Formatter
import json
import os
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from datetime import datetime
import babel
import dateutil.parser
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from forms import *
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(250))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f'<Venue {self.id} name: {self.name}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f'<Artist {self.id} name: {self.name}>'


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
      return f'<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>'



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#



@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
  data = []
  venues = Venue.query.all()
  locations = set()
  now_date = datetime.now()

  for venue in venues:
    locations.add((venue.city, venue.state))

  for location in locations:
    data.append({
        "state": location[1],
        "city": location[0],
        "venues": []
    })

  for venue in venues:
    num_upcoming_shows = 0

    my_shows = Show.query.filter_by(venue_id=venue.id).all()
    for show in my_shows:
      if show.start_time > now_date:
          num_upcoming_shows += 1

    for location_of_venue in data:
      if venue.state == location_of_venue['state'] and venue.city == location_of_venue['city']:
        location_of_venue['venues'].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows
        })
  return render_template('pages/venues.html', areas=data)



@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

  response={
    "count": result.count(),
    "data": result
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  my_venue = Venue.query.get(venue_id)
  my_shows = Show.query.filter_by(venue_id=venue_id).all()
  past_shows = []
  upcoming_shows = []
  current_time = datetime.now()

  for show in my_shows:
    data = {
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
           "artist_image_link": show.artist.image_link,
           "start_time": format_datetime(str(show.start_time))
        }
    if show.start_time > current_time:
      upcoming_shows.append(data)
    else:
      past_shows.append(data)

  data={
    "id": my_venue.id,
    "name": my_venue.name,
    "genres": my_venue.genres,
    "address": my_venue.address,
    "city": my_venue.city,
    "state": my_venue.state,
    "phone": my_venue.phone,
    "website": my_venue.website,
    "facebook_link": my_venue.facebook_link,
    "seeking_talent": my_venue.seeking_talent,
    "seeking_description":my_venue.seeking_description,
    "image_link": my_venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }


  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm()
        my_venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data,
                  phone=form.phone.data, image_link=form.image_link.data,genres=form.genres.data, 
                  facebook_link=form.facebook_link.data, seeking_description=form.seeking_description.data,
                  website=form.website.data, seeking_talent=form.seeking_talent.data)
    
        db.session.add(my_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] +' was successfully listed!')

    except:
        db.session.rollback()
        print(sys.exc_info()) 
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')   
        
    finally:
        db.session.close()
             
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  my_artists = Artist.query.all()

  for artist in my_artists:
    data.append({
        "id": artist.id,
        "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term','')
  artists=Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()

  response={}
  response['count']=len(artists)
  response['data']=artists

  return render_template('pages/search_artists.html',
   results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  my_artist = Artist.query.get(artist_id)
  my_shows = Show.query.filter_by(artist_id=artist_id).all()
  past_shows = []
  upcoming_shows = []
  now_date = datetime.now()
  for show in my_shows:
    data = {
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": format_datetime(str(show.start_time))
        }
    if show.start_time > now_date:
      upcoming_shows.append(data)
    else:
      past_shows.append(data)

  data={
    "id": my_artist.id,
    "name": my_artist.name,
    "genres": my_artist.genres,
    "city": my_artist.city,
    "state": my_artist.state,
    "phone": my_artist.phone,
    "facebook_link": my_artist.facebook_link,
    "image_link": my_artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  artist_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link
    }

  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm()

    my_artist = Artist.query.get(artist_id)

    my_artist.name = form.name.data

    my_artist.name = form.name.data
    my_artist.phone = form.phone.data
    my_artist.state = form.state.data
    my_artist.city = form.city.data
    my_artist.genres = form.genres.data
    my_artist.image_link = form.image_link.data
    my_artist.facebook_link = form.facebook_link.data
    
    db.session.commit()
    flash('The Artist ' + request.form['name'] + ' has been successfully updated!')
  except:
    db.session.rolback()
    flash('An Error has occured and the update unsuccessful')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  my_venue = Venue.query.get(venue_id)
  venue={
    "id": my_venue.id,
    "name": my_venue.name,
    "genres": my_venue.genres,
    "address": my_venue.address,
    "city": my_venue.city,
    "state": my_venue.state,
    "phone": my_venue.phone,
    "website": my_venue.website,
    "facebook_link": my_venue.facebook_link,
    "seeking_talent": my_venue.seeking_talent,
    "seeking_description": my_venue.seeking_description,
    "image_link": my_venue.image_link,
  }
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm()
    my_venue = Venue.query.get(venue_id)
    my_venue.name = form.name.data
    my_venue.genres = form.genres.data
    my_venue.city = form.city.data
    my_venue.state = form.state.data
    my_venue.address = form.address.data
    my_venue.phone = form.phone.data
    my_venue.facebook_link = form.facebook_link.data
    my_venue.website = form.website.data
    my_venue.image_link = form.image_link.data
    my_venue.seeking_talent = form.seeking_talent.data
    my_venue.seeking_description = form.seeking_description.data

    db.session.commit()
    flash('Venue ' + name + ' has been updated')
  except:
    db.session.rollback()
    flash('An error occured while trying to update Venue')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    form = ArtistForm()

    my_artist = Artist(name=form.name.data,
     city=form.city.data, 
     state=form.city.data,
                    phone=form.phone.data, 
                    genres=form.genres.data, 
                    image_link=form.image_link.data,
                     facebook_link=form.facebook_link.data)
    
    db.session.add(my_artist)
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


@app.route('/artist/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:

    my_artist = Artist.query.get(artist_id)
    artist_name = artist.name

    db.session.delete(my_artist)
    db.session.commit()

    flash('Artist ' + artist_name + ' was deleted')
  except:
    flash('an error occured and Artist ' + artist_name + ' was not deleted')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  my_shows = Show.query.order_by(db.desc(Show.start_time))

  data = []

  for show in my_shows:
    data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    my_show = Show(artist_id=request.form['artist_id'], 
                venue_id=request.form['venue_id'],
                start_time=request.form['start_time'])

    db.session.add(my_show)
    db.session.commit()

    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# Launch.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

