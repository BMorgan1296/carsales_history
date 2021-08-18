#https://stackoverflow.com/questions/64979042/how-to-run-seleniumchrome-on-raspberry-pi-4
#https://stackoverflow.com/questions/35956045/extract-title-with-beautifulsoup

import os
import sys
import time
import random
import pickle
import requests

from pyvirtualdisplay import Display

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, './bypass_geetest_slider')
from bypass_geetest_slider.captcha_solver.nocaptcha import CapatchaSolver

def log(logstr):
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print("%s: %s" % (current_time, logstr))

class carsales_scraper:
    def __init__(self, timeout):
        self.timeout = timeout
        log("Beginning virtual display setup")
        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()
        log("Virtual Display started, setting ChromeDriver options")

        self.chrome_options = Options()
        self.chrome_options.add_argument("--gpu_compositing")
        self.chrome_options.add_argument("--ignore-gpu-blocklist")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--allow-running-insecure-content");

        log("Starting ChromeDriver")
        self.driver = webdriver.Chrome(options=self.chrome_options, executable_path='/usr/lib/chromium-browser/chromedriver')
        log("ChromeDriver successfully setup")

    def load_page(self, url):
        website = None
        loading_finished = 0                   # Set flag to 0
        count = 0
        while loading_finished == 0:           # Repeat while flag = 0
            try:
                self.driver.set_page_load_timeout(self.timeout)
                time.sleep(random.uniform(0.1, 0.5)) # wait some time
                self.driver.get(url)       # try to load for n seconds
                loading_finished = 1                 # Set flag to 1 and exit while loop
            except KeyboardInterrupt:
                log("SIGINT Ctrl-C - Exiting")
                self.kill_driver()
                sys.exit(1)
            except:
                log("Timeout - retry")
            count += 1
            if(count == 25):
                log("Too many tries (25) - Exiting")
                self.kill_driver()
                sys.exit(1)
        else:
            log("Page loaded")
        return self.driver.page_source

    def test_captcha_exist(self, basepage):
        log("Checking CarSales for CAPTCHA")
        website = self.load_page(basepage)
        try:
            geetest = driver.find_element_by_class_name("geetest_radar_tip")
            print(geetest)
            log("Geetest CAPTCHA found")
            return 1
            # captcha_solver = CapatchaSolver(self.driver)
        except Exception as e:
            log("No Geetest CAPTCHA found")
            return 0

    def kill_driver(self):
        self.driver.close()
        self.driver.quit()

#Handles listing and updated data
class listing:
    def __init__(self, idx, title, ad_type, bodystyle, make, model, ad_state, price, picture_url):
        #Untracked data
        self.id = idx
        self.title = title
        self.ad_type = ad_type
        self.bodystyle = bodystyle
        self.make = make
        self.model = model
        self.ad_state = ad_state
        self.picture_url = picture_url
        self.url = "https://www.carsales.com.au/cars/details/x/"+self.id

        #Tracked data (will be one or more of these pieces of info)
        self.tracked_data = []
        #Price and time of query
        self.tracked_data.append((price, time.time()))

        self.picture = requests.get(picture_url)

        #0 sold, 1 alive. 2 on hold (need to find how to differentiate this)
        # Init as alive.
        self.status = 1

    def update(self, price):
        self.tracked_data.append((price, time.time()))

    def print_listing(self):
        print(self.title)
        print(self.id, self.ad_type, self.ad_state)
        print(self.bodystyle, self.make, self.model)
        print(self.url)
        print(self.picture_url)
        for p in self.tracked_data:
            print(p)

class saved_search:
    def __init__(self, name, search_url):
        self.name = name
        self.search_url = search_url
        self.listings = []
        self.last_updated = -1       

    def __add_listing(self, idx, title, ad_type, bodystyle, make, model, ad_state, price, picture_url):
        #Go through all listings, if ID found then update. Otherwise, add a new listing.
        for l in self.listings:
            if(l.id == idx):
                l.update(ad_type, price)
                return
        self.listings.append(listing(idx, title, ad_type, bodystyle, make, model, ad_state, price, picture_url))

    def __update_from_page(self, website):
        title = ""
        picture_url = ""
        page = BeautifulSoup(website, 'html.parser')
        listings = page.find_all("div", class_="listing-items")
        listings = listings[0].find_all('div', class_="listing-item", recursive=False)
        for listing in listings:
            #Get image url. Will save this at some point.
            for img in listing.find_all('img', recursive=True):
                try:
                    picture_url = img.attrs['src']
                except:
                    picture_url = "Picture unavailable"
                break
            #Get title
            for card in listing.find_all('div', class_="card-body", recursive=True):
                for inner in card.find_all('a', class_="js-encode-search", recursive=True): 
                    try:
                        title = inner.decode_contents()
                    except:
                        title = "Title unavailable"
                    break
            #Add the new listing, or update an existing one if this is found.
            try:
                self.__add_listing(
                    listing.attrs['id'], 
                    title,
                    listing.attrs['data-webm-vehcategory'],
                    listing.attrs['data-webm-bodystyle'],
                    listing.attrs['data-webm-make'],
                    listing.attrs['data-webm-model'],
                    listing.attrs['data-webm-state'],
                    listing.attrs['data-webm-price'],
                    picture_url)
            except Exception as e:
                log("Error parsing ID %s" % listing.attrs['id'])
                return -1
        return len(listings)

    def update(self, skip):
        log("Starting update for \"%s\"" % self.name)
        self.last_updated = time.time()
        d = carsales_scraper(45)
        time.sleep(3)
        #get first page
        if(skip or d.test_captcha_exist("https://www.carsales.com.au/cars/") == 0):
            #loop through all listings, see if any haven't been updated. If so, mark as sold or unavailable.
            page = 0
            num = 1
            while(num):
                url = self.search_url + "&offset=" + str(12*page)
                log("Querying: "+url)
                #start parsing
                #website = d.load_page(url)
                website = open("output1.txt", "r")
                num = self.__update_from_page(website)
                print(num)
                for l in self.listings:
                    l.print_listing()
                    print("")
                website.close()
                ###########BREAK EARLY################
                break
                page += 1
                #get next page
                #TODO
        #Check if any listing weren't updated after the last_updated time
        d.kill_driver()



def main():
    base_url = "https://www.carsales.com.au/cars/"
    search_url = "https://www.carsales.com.au/cars/?q=(And.Service.carsales._.Make.Nissan._.Drive.Rear+Wheel+Drive._.GenericGearType.Manual._.Induction.Turbo._.Year.range(..2001).)&sort=%7ePrice"
    search_url2 = "https://www.carsales.com.au/cars/nissan/skyline/coupe-bodystyle/manual-transmission/turbo-induction/6-cylinders/"

    searches_dir = "./saved_searches/"
    searches = []

    #load from pickle
    for file in os.listdir(searches_dir):
        if file.endswith("obj"):
            try:
                log("Found existing search \"%s\" - Loading" % file)
                file_pi = open(searches_dir+file, 'rb') 
                searches.append(pickle.load(file_pi))
                file_pi.close()
                log("Load successful")
            except:
                log("Failed to load \"%s\" - Exiting" % file)
                sys.exit(1)

    found = 0
    temp = saved_search("Nissan Turbo Search", search_url)
    for s in searches:
        if(s.name == temp.name):
            log("Search already exists - Continuing")
            found = 1

    if(found == 0):
        searches.append(temp)

    for s in searches:
        s.update(1)
        log("Update successful - Saving")
        file_pi = open(searches_dir+s.name+'.obj', 'wb') 
        pickle.dump(s, file_pi)
        log("Saved")

    log("All searches updated and saved, exiting")
    
if __name__ == "__main__":
    main()