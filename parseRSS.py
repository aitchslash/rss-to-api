import feedparser
from datetime import datetime
import requests
import os

"""Parses the JustShows RSS feed."""

"""Will need to check if 'updated' ever comes up."""


class Show(object):
    """Show object docstring."""
    def __init__(self, headliner, date, openers, venue, date_listed, summary, url):
        self.headliner = headliner
        self.date = date  # string, for now
        self.openers = openers  # array
        self.venue = venue  # string
        self.date_listed = date_listed  # time.struct_time, could use 'published for string'
        self.summary = summary  # string
        self.url = url  # string

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


# not currently being used but I like the vars(show) conversion of
# the Show object into a dictionary.
def make_shows_array(band, band_dict):
    show_array = []
    bands_Shows = band_dict[band]
    for show in bands_Shows:
        show_array.append(vars(show))
    return show_array


def parse_summary(listing_summary):
    """Extract all opening acts and venue."""
    openers = []
    # extract venue
    at_index = listing_summary.find(' at ')
    venue = listing_summary[at_index + 4:]
    venue = clean_ascii(venue)
    # truncate string if venue present
    if at_index > 0:
        listing_summary = listing_summary[:at_index]

    """Try to extract all opening acts.
        opening acts start the string w/ 'with'
        continuing issues with commas/ands """
    if listing_summary.find('with') == 0:
        listing_summary = listing_summary[5:]  # truncate
        if listing_summary.find(' and ') > 0:
            first_bit, second_bit = listing_summary.rsplit(' and ', 1)
            if first_bit.find(' and ') != -1:
                print("MANY AND PROBLEM W/ " + first_bit)
            first_split = first_bit.split(', ')

            openers = first_split
            openers.append(second_bit)
        elif listing_summary.lower().find("special guest") != -1:  # might want to lowercase this
            openers = []
        elif listing_summary.lower().find("estival") != -1:
            openers = []

        else:
            openers = [listing_summary]
    return venue, openers


def add_show(show, band, band_dict):
    """Adds a show to the band dict."""
    band = clean_ascii(band.lower())
    if band in band_dict.keys():
        band_dict[band].append(vars(show))
    else:
        band_dict[band] = [vars(show)]
    return band_dict


def clean_headliner(headliner_string):
    """Deal with Fesivals. Can't just use find (':')
        Might want to make array a global."""
    festivals = ['estival:', 'CMW:', 'ield Trip:', 'inato:', 'NXNE:']
    for fest in festivals:
        if headliner_string.find(fest) != -1:
            # finding (' ') after fest might be better
            colon_index = headliner_string.find(':')
            if colon_index == -1:
                print("Fest w/o colon: " + headliner_string)
            headliner_string = headliner_string[colon_index + 1:]
    # clean up things like "Queen's Plate w/ Brad Paisley"
    w_index = headliner_string.find('w/')
    if w_index > 1:
        print("Removing str up to 'w/' for: " + headliner_string)
        headliner_string = headliner_string[w_index + 3:]
    headliner_string = headliner_string.strip()  # spaces but it would be less robust
    coheadliner_array = []
    if headliner_string.find(' and ') != -1:
        # print("AND WARNING: " + headliner_string)
        # OK, if and is followed by the (n.b. lowercase 't') it's often à la the Attractions
        # If it's an uppercase 'The' it's likely another band
        first_and_index = headliner_string.find(' and ')

        if headliner_string[first_and_index: first_and_index + 9] != ' and the ':
            # print (headliner_string)
            head, rest = headliner_string.split(' and ', 1)
            headliner_string = head
            coheadliner_array.append(rest)
            if rest.find(' and ') != -1:
                print("REST w/ and : " + rest)

        # Use first listed band as headliner, use others as openers
    return headliner_string, coheadliner_array


def clean_ascii(target):
    """Replace all hard/impossible to type ascii from dictionary keys."""
    """Is there a library for this?"""

    # get rid of ampersands
    # if target.find('&') != -1:
    #     target.replace('&', 'and')
    # get rid of trailing underscore
    if target and target[-1] == "_":
        target = target[:-1] + "."

    clean_target = target

    tar = target.encode('utf-8')

    # bad hyphen size three
    bad_hyphen = tar.find(b'\xe2\x80\x90')  # takes 3 indicies
    if bad_hyphen != -1:
        clean_target = tar[:bad_hyphen].decode() + '-' + tar[bad_hyphen + 3:].decode()
        tar = clean_target.encode('utf-8')
        bad_hyphen = tar.find(b'\xe2\x80\x90')  # takes 3 indicies
        if bad_hyphen != -1:
            clean_target = tar[:bad_hyphen].decode() + '-' + tar[bad_hyphen + 3:].decode()
    # clean_ascii(clean_target)
    # recursion would be better but not working
    # bad_hyphen2 = tar.find(b'\xe2\x80\x90') # takes 3 indicies
    # if bad_hyphen2 != -1:
    #     tar = clean_target.encode('utf-8')
    #      clean_target= tar[:bad_hyphen2].decode() + '-' + tar[bad_hyphen2 + 3:].decode()

    # 'o' with umlaut b'\xc3\xb6' size two
    umlaut = tar.find(b'\xc3\xb6')
    if umlaut != -1:
        clean_target = tar[:umlaut].decode() + 'o' + tar[umlaut + 2:].decode()
        tar = clean_target.encode('utf-8')

    # 'u' with umlaut, may have to do twice for husker du
    if b'\xc3\xbc' in tar:
        ind = tar.find(b'\xc3\xbc')
        clean_target = tar[:ind].decode() + 'u' + tar[ind + 2:].decode()

    # accent aigu 'é' \xc3\xa9
    if b'\xc3\xa9' in tar:
        ind = tar.find(b'\xc3\xa9')
        clean_target = tar[:ind].decode() + 'e' + tar[ind + 2:].decode()
    # ó alà sigur rós
    if b'\xc3\xb3s' in tar:
        ind = tar.find(b'\xc3\xb3s')
        clean_target = tar[:ind].decode() + 'o' + tar[ind + 2:].decode()
    # janelle monae, aigu above the last a
    if b'\xc3\xa1e' in tar:
        ind = tar.find(b'\xc3\xa1e')
        clean_target = tar[:ind].decode() + 'a' + tar[ind + 2:].decode()
    # dalava, aigu on the first a
    if b'\xc3\xa1' in tar:
        ind = tar.find(b'\xc3\xa1')
        clean_target = tar[:ind].decode() + 'a' + tar[ind + 2:].decode()
    # Umit Davala, umlaut over the U
    if b'\xc3\x9c' in tar:
        ind = tar.find(b'\xc3\x9c')
        clean_target = tar[:ind].decode() + 'U' + tar[ind + 2:].decode()
    # Brujeria, aigu over the i
    if b'\xc3\xad' in tar:
        ind = tar.find(b'\xc3\xad')
        clean_target = tar[:ind].decode() + 'i' + tar[ind + 2:].decode()
    # Chingón, aigu over the 'o'
    if b'\xc3\xb3' in tar:
        ind = tar.find(b'\xc3\xb3')
        clean_target = tar[:ind].decode() + 'o' + tar[ind + 2:].decode()
    # Jacqueline Taïeb
    if b'\xc3\xaf' in tar:
        ind = tar.find(b'\xc3\xaf')
        clean_target = tar[:ind].decode() + 'i' + tar[ind + 2:].decode()
    # Stupid non-apostrophe apostrophies, may need in db dealt w/ in band_in_db
    if b'\xe2\x80\x99' in tar:
        ind = tar.find(b'\xe2\x80\x99')
        clean_target = tar[:ind].decode() + "'" + tar[ind + 3:].decode()

    return clean_target


def refresh_rss():
    """Checks if stored rss.txt is less than a day old.  Updates if necessary."""
    rss = "justShowsRss.txt"
    r = feedparser.parse(rss)
    last_updated = r.feed.updated
    # convert to datetime
    last_updated = datetime.strptime(last_updated, "%a, %d %b %Y %X %z")
    # get rss from just_shows
    justShowsRss = "http://feeds.justshows.net/rss/toronto/"

    response = requests.get(justShowsRss)
    if not response.ok:
        return False
    else:
        with open("rss_request.txt", 'w', encoding="utf-8") as rr:
            for line in response.text:
                rr.write(line)

        new_feed = feedparser.parse("rss_request.txt")
        new_updated = new_feed.feed.updated
        new_updated = datetime.strptime(new_updated, "%a, %d %b %Y %X %z")
        # if new_date is != and newer AND entries are within expected range
        if new_updated > last_updated and (0 < len(new_feed.entries) < 800):
            try:
                os.rename('justShowsRss.txt', 'justShowsRss.old')
            except OSError as e:
                # os.remove('justShowsRss.old')
                # os.rename('justShowsRss.txt', 'justShowsRss.old')
                print("Error1: " + str(e))
            try:
                os.rename('rss_request.txt', 'justShowsRss.txt')
            except OSError as e:
                # os.remove('justShowsRss.txt')
                # os.rename('rss_request.txt', 'justShowsRss.txt')
                print("Error2: " + str(e))
            return True
        else:
            return False


def load_data(rss="justShowsRss.txt"):
    """Return an array of Shows and a dict mapping bandnames to array of their shows."""
    # if more cities than TO have function take a feed
    band_dict = {}
    show_array = []
    # coheads = [] # unused for now
    # justShowRss = "http://feeds.justshows.net/rss/toronto/"
    # justShowRss = "rss26102019.txt"  # text file for experimenting.

    if refresh_rss():
        print("RSS updated!")

    r = feedparser.parse(rss)  # this might be redundant, could use output from refresh
    # print(r.feed.title)
    # print("There are " + str(len(r.entries)) + " listings.")

    # check if feed is more than a day old
    # last_updated = r.feed.updated
    # if it's too old
    #   request new rss
    #   check if it's new
    #   if so
    #       backup the old rss
    #       write new feed to
    #       parse the new feed.
    #       make sure its long enough.

    for listing in r.entries:
        date, headliner = listing['title'].split('—')
        date = date.strip()  # could change the split to include
        headliner, coheadliner_array = clean_headliner(headliner)

        if headliner.find(":") != -1:
            print("WARNING: colon!" + headliner)
        venue, openers = parse_summary(listing.summary)
        if len(coheadliner_array) > 0:
            openers.append(coheadliner_array[0])
            if len(coheadliner_array) > 1:
                print("WARNING many coheads: " + str(coheadliner_array))
        # append cohead to openers
        # openers.append(coheadliner_array[0])
        date_listed = listing.published_parsed
        summary = headliner + " " + listing.summary
        url = listing.link
        show = Show(headliner, date, openers, venue, date_listed, summary, url)
        show_array.append(vars(show))
        band_dict = add_show(show, headliner, band_dict)
        for band in openers:
            band_dict = add_show(show, band, band_dict)
        show_array = sorted(show_array, key=lambda sa: datetime.strptime(sa['date'], "%B %d, %Y"))
    return band_dict, show_array
