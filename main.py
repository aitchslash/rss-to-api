from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from parseRSS import data_loader
import json
import redis
import os

app = Flask(__name__)

password = "secret"  # this is obviously insecure

# Use remote (heroku) db if available, else use locally
if os.environ.get("REDISCLOUD_URL"):
    redis_url = os.environ.get("REDISCLOUD_URL")
    db = redis.from_url(redis_url)
else:
    db = redis.Redis()


lastBuildDate = db.get("lastBuildDate")
if lastBuildDate:
    lastBuildDate = datetime.strptime(
        lastBuildDate.decode("utf-8"), '%Y-%m-%d %H:%M:%S.%f')
    expiry_time = datetime.now() - timedelta(hours=36)
if not lastBuildDate or expiry_time > lastBuildDate:
    print("NEED TO REFRESH REDIS TAKE 2")
    data_loader()


@app.route('/api/ping', methods=['GET'])
def ping_response():
    """Simple ping response."""
    return jsonify({"lastBuildDate": db.get("lastBuildDate").decode("utf-8")}), 200


@app.route('/api/band/<bandname>', methods=['GET'])
def get_band_showlistings(bandname):
    """Get shows for one band."""
    result = db.get(bandname.lower())
    if not result:
        return jsonify({'error': 'Unknown band name'}), 400
    else:
        result = json.loads(result.decode("utf-8"))
        return jsonify({bandname: result}), 200


@app.route('/api/bands', methods=['POST'])
def get_shows_from_list():
    """Return a list of a list of band shows."""
    """i.e. if a band is playing more than once len(list) > 1"""
    band_json = request.json
    band_list = band_json['bands']
    show_list = db.mget(band_list)
    if show_list:
        show_list = [show.decode("utf-8") for show in show_list if show]
    return jsonify({"shows": show_list})


@app.route('/api/venue/<venue>', methods=['GET'])
def get_shows_by_venue(venue):
    limit = int(request.args.get('limit', 10))
    venue_shows = db.lrange(venue, 0, limit)
    if not venue_shows:
        return jsonify({"error": "Unkown venue: " + venue}), 400
    else:
        shows = [json.loads(show.decode("utf-8"))
                 for show in venue_shows if show]
        return jsonify({venue: shows})


# maybe set default to today?
@app.route('/api/date/<int:date>', methods=['GET'])
def get_shows_by_date(date):
    if not (0 < date < 311299):
        return jsonify({"error": "Bad date. Try format: ddmmyy"})
    else:
        shows = db.hgetall("date:" + str(date))
    if not shows:
        return jsonify({"error": 'No results or bad date try: ddmmyy'})
    else:
        show_array = [json.loads(key.decode("utf-8")) for key in shows.keys()]
        return jsonify({date: show_array})


@app.route('/api/latest', methods=['GET'])
def get_latest_added():
    limit = int(request.args.get('limit', 20))
    latest_shows_added = db.lrange("dateListed", 0, limit - 1)
    if not latest_shows_added:
        return jsonify({"error": "something wrong with latest"}), 400
    else:
        shows = [json.loads(show.decode("utf-8"))
                 for show in latest_shows_added if show]
        return jsonify({"latest added": shows})


"""This could be improved. PUT would be better."""
@app.route('/api/update', methods=['GET'])
def update_rss():
    pw = request.args.get("pw", "")
    if pw == password:
        data_loader()
        return jsonify({"success":
                        "checked for new data. Please test and revert if unexpected results"})
    else:
        return jsonify({"error": "Password required."})


if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port=8088)
