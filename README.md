# rss-to-api

rss-to-api is a Flask API created from the Toronto RSS feed of justshows.com Currently deployed here: https://justshowsapi.herokuapp.com/api/latest

## Installation

The master branch requires Redis. If Redis isn't your thing please checkout the no-redis branch

```bash
pip install -r requirements.txt
```

## Usage

To run locally on port 8088

```bash
python3 main.py
```

Currently configured for deployment on Heroku. Be sure to disable/enable DEBUG and change password. Your mileage may vary.

## Endpoints

/api/latest?limit=20 => 20 most recently listed shows

/api/venue/<venuename> => All shows at <venuename>

/api/band/<bandname> => All shows featuring <bandname>

/api/date/<ddmmyy> => All shows on <ddmmyy>

/api/update?pw=<password> => With valid password will update the RSS feed.

POST route. Body with json {"bands": `[band1, band2, band3, ... ]`}

/api/bands => returns listOfBands`[listOfShows]`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
