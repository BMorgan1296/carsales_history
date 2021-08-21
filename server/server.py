import sys
import os 
import time
import pickle

from flask import *

from filelock import Timeout, FileLock

def log(logstr):
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print("%s: %s" % (current_time, logstr))

class listing:
    def __init__(self, idx, title, ad_type, bodystyle, make, model, odometer, ad_state, price, picture_url):
        #Untracked data
        self.id = idx
        self.title = title
        self.ad_type = ad_type
        self.bodystyle = bodystyle
        self.make = make
        self.model = model
        self.odometer = -1
        self.ad_state = ad_state
        self.picture_url = picture_url
        self.url = "https://www.carsales.com.au/cars/details/x/"+self.id

        #Tracked data (will be one or more of these pieces of info)
        self.price_history = []
        #Price and time of query
        self.price_history.append((price, time.time()))
        res = requests.get(picture_url)
        if(res.status_code == 200):
            self.picture = res.raw
        else:
            self.picture = None

        #0 sold, 1 alive. 2 on hold (need to find how to differentiate this)
        # Init as alive.
        self.status = 1

class saved_search:
    def __init__(self, name, search_url):
        self.name = name
        self.search_url = search_url
        self.listings = []
        self.last_updated = -1

class saved_searches():
    def __init__(self, searches_dir):
        self.searches_dir = searches_dir
        self.searches = []
        self.__load_searches()

    def __load_searches(self):
        #load from pickle
        for file in os.listdir(self.searches_dir):
            if file.endswith("obj"):
                try:
                    log("Found existing search \"%s\" - Loading" % file)

                    filename = self.searches_dir+file
                    filelockname = filename+".lock"
                    #open lock and load with pickle
                    with FileLock(filelockname):
                        open(filelockname, "rb")
                        file_pi = open(filename, 'rb') 
                        self.searches.append(pickle.load(file_pi))
                        file_pi.close()
                    log("Load successful")
                except Exception as e:
                    log("Failed to load \"%s\" - Exiting" % file)
                    print(e)
                    sys.exit(1)

############################################################################################

server = Flask(__name__)

searches = saved_searches("../saved_searches/")

@server.route("/")
def hello():
    return send_file("web/html/index.html")

@server.route('/getsearches', methods = ['POST'])
def getsearches():
    s_json = []
    for s in searches.searches:
        s_json.append(s.name)
    s_json = json.dumps(s_json)
    return s_json

@server.route('/getsearch', methods = ['POST'])
def getsearch():
    s_query = request.get_json()
    l_json = []
    search = None
    for s in searches.searches:
        if(s.name == s_query['search']):
            for listing in s.listings:
                status = "N/A"
                if(listing.status == 0):
                    status = "Sold"
                elif(listing.status == 1):
                    status = "Available"
                elif(listing.status == 2):
                    status = "On Hold"
                else:
                    status = "N/A"
                temp = {'id' : listing.id,
                        'title' : listing.title,
                        'ad_type' : listing.ad_type,
                        'bodystyle' : listing.bodystyle,
                        'make' : listing.make,
                        'model' : listing.model,
                        'odometer' : listing.odometer,
                        'ad_state' : listing.ad_state,
                        'picture_url' : listing.picture_url,
                        'price_history' : listing.price_history,
                        'status' : status,
                    }
                l_json.append(temp)
            break
    l_json = json.dumps(l_json)
    return l_json

@server.route('/img/<idx>.jpg')
def index(idx):
    path = "../saved_images/%s/%s.jpg" % (idx, idx)
    if(os.path.exists(path)):
        return send_file(path)
    else:
        return "404 Not Found"

@server.route('/favicon.ico', methods = ['GET'])
def favicon():
    return send_file("web/icons/favicon.ico")

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=8080, debug=True)