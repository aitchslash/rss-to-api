from flask import Flask, jsonify, request
from datetime import datetime
from parseRSS import load_data
import shutil

app = Flask(__name__)

# memcache_dict = {}  # setup memcache here

password = "secret" # this is obviously unsecure

# Get Data:
band_dict, show_array = load_data()


@app.route('/api/ping', methods=['GET'])
def ping_response():
    """Simple ping response."""
    return jsonify({"success": True}), 200


@app.route('/api/band/<bandname>', methods=['GET'])
def get_band_showlistings(bandname):
    """Get shows for one band."""
    if bandname.lower() not in band_dict.keys():
        return jsonify({'error': 'Unknown band name'}), 400
    else:
        # check if request is in memcache
        # check if results are sorted
        # return jsonified response
        return jsonify({bandname: band_dict[bandname.lower()]}), 200


@app.route('/api/venue/<venue>', methods=['GET'])
def get_shows_by_venue(venue):
    # filter show_array by venue
    shows = list(filter(lambda x: x['venue'].lower() == venue.lower(), show_array))
    if not shows:
        return jsonify({"error": "Unkown venue: " + venue}), 400
    else:
        return jsonify({venue: shows})


@app.route('/api/date/<int:date>', methods=['GET'])  # maybe set default to today?
def get_shows_by_date(date):
    if not (0 < date < 311299):
        return jsonify({"error": "Bad date. Try format: ddmmyy"})
    else:
        pydate = datetime.strptime(str(date), "%d%m%y")
    shows = list(filter(lambda x: datetime.strptime(x['date'], "%B %d, %Y") == pydate, show_array))
    if not shows:
        return jsonify({"error": 'No results or bad date try: ddmmyy'})
    else:
        return jsonify({date: shows})


@app.route('/api/latest', methods=['GET'])
def get_latest_added():
    limit = int(request.args.get('limit', 10))
    if not (0 < limit < len(show_array)):
        return jsonify({"error": "Bad limit request"})
    shows_by_added = sorted(show_array, key=lambda sa: sa['date_listed'], reverse=True)
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
