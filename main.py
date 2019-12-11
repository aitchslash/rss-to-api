from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from parseRSS import load_data, test_redis
import shutil
import json
import redis
import os

app = Flask(__name__)

# memcache_dict = {}  # setup memcache here

password = "secret"  # this is obviously insecure

# Get Data:
band_dict, show_array = load_data()

# r1 = redis.Redis(db=1)
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
    test_redis()


@app.route('/api/ping', methods=['GET'])
def ping_response():
    """Simple ping response."""
    return jsonify({"lastBuildDate": db.get("lastBuildDate").decode("utf-8")}), 200


@app.route('/api/band/<bandname>', methods=['GET'])
def get_band_showlistings(bandname):
    """Get shows for one band."""
    result = db.get(bandname.lower())
    # result = json.loads(r1.get(bandname.lower()).decode("utf-8"))
    if not result:
        return jsonify({'error': 'Unknown band name'}), 400
    else:
        # check if request is in memcache
        # check if results are sorted
        # return jsonified response
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
    # filter show_array by venue
    shows = list(
        filter(lambda x: x['venue'].lower() == venue.lower(), show_array))
    if not shows:
        return jsonify({"error": "Unkown venue: " + venue}), 400
    else:
        return jsonify({venue: shows})


# maybe set default to today?
@app.route('/api/date/<int:date>', methods=['GET'])
def get_shows_by_date(date):
    if not (0 < date < 311299):
        return jsonify({"error": "Bad date. Try format: ddmmyy"})
    else:
        pydate = datetime.strptime(str(date), "%d%m%y")
    shows = list(filter(lambda x: datetime.strptime(
        x['date'], "%B %d, %Y") == pydate, show_array))
    if not shows:
        return jsonify({"error": 'No results or bad date try: ddmmyy'})
    else:
        return jsonify({date: shows})


@app.route('/api/latest', methods=['GET'])
def get_latest_added():
    limit = int(request.args.get('limit', 10))
    if not (0 < limit < len(show_array)):
        return jsonify({"error": "Bad limit request"})
    shows_by_added = sorted(
        show_array, key=lambda sa: sa['date_listed'], reverse=True)
    return jsonify({'latest': shows_by_added[:limit]})


"""This could be vastly improved.  For use w/o db.  PUT would be better."""
@app.route('/api/update', methods=['GET'])
def update_rss():
    pw = request.args.get("pw", "")
    if pw == password:
        global band_dict, show_array
        band_dict, show_array = load_data()
        return jsonify({"success":
                        "checked for new data. Please test and revert if unexpected results"})
    else:
        return jsonify({"error": "Password required."})


"""This could be vastly improved.  For use w/o db.  PUT would be better."""
@app.route('/api/revert', methods=['GET'])
def revert_rss():
    pw = request.args.get("pw", "")
    if pw == password:
        shutil.copyfile("justShowsRss.old", "justShowsRss.txt")
        global band_dict, show_array
        band_dict, show_array = load_data()
        return jsonify({"success": "Data reverted to old version."})
    else:
        return jsonify({"error": "Password required."})


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8088)
