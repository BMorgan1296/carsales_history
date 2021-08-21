#https://stackoverflow.com/questions/64979042/how-to-run-seleniumchrome-on-raspberry-pi-4

import os
import sys
import time
import random
import pickle
import requests

from filelock import Timeout, FileLock

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
        time.sleep(1)
        log("ChromeDriver successfully setup")

    def load_page(self, url):
        website = None
        loading_finished = 0                   # Set flag to 0
        count = 0
        while loading_finished == 0:           # Repeat while flag = 0
            try:
                self.driver.set_page_load_timeout(self.timeout)
                time.sleep(random.uniform(0.1, 0.5))    # wait some time
                self.driver.get(url)                    # try to load for n seconds
                loading_finished = 1                    # Set flag to 1 and exit while loop
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

    def check_captcha(self, website):
        log("Checking CarSales for CAPTCHA")
        if(website.find("captcha") != -1):
            try:
                self.driver.save_screenshot("screenshot1.png")
                log("Geetest CAPTCHA found")
                time.sleep(30)
                captcha_solver = CapatchaSolver(self.driver)
                log("CAPTCHA solved")
                self.driver.save_screenshot("screenshot2.png")
                return 1
            except Exception as e:
                log("No Geetest CAPTCHA found")
                print(e)
                return 0
        else:
            log("No CAPTCHA found")

    def kill_driver(self):
        self.driver.close()
        self.driver.quit()

#Handles listing and updated data
class listing:
    def __init__(self, idx, title, ad_type, bodystyle, make, model, odometer, ad_state, price, picture_url):
        #Untracked data
        self.id = idx
        self.title = title
        self.ad_type = ad_type
        self.bodystyle = bodystyle
        self.make = make
        self.model = model
        self.odometer = odometer
        self.ad_state = ad_state
        self.picture_url = picture_url.replace("&pxc_size=720,480", "&pxc_size=1440,1080")
        self.url = "https://www.carsales.com.au/cars/details/x/"+self.id

        #Tracked data (will be one or more of these pieces of info)
        self.price_history = []
        #Price and time of query
        self.price_history.append((price, time.time()))

        filename = "./saved_images/%s/%s.jpg" % (self.id, self.id)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as handle:
            response = requests.get(self.picture_url, stream=True)
            if not response.ok:
                log("Could not save picture for ID %s : %d", (self.id, response))
            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)

        #0 sold, 1 alive. 2 on hold (need to find how to differentiate this)
        # Init as alive.
        self.status = 1

    def update_listing(self, price):
        self.price_history.append((price, time.time()))

    def print_listing(self):
        print(self.title)
        print(self.id, self.ad_type, self.ad_state)
        print(self.bodystyle, self.make, self.model, self.odometer)
        print(self.url)
        print(self.picture_url)
        for p in self.price_history:
            print(p)
        print(self.status)

class saved_search:
    def __init__(self, name, search_url):
        self.name = name
        self.search_url = search_url
        self.listings = []
        self.last_updated = -1

    def __add_listing(self, idx, title, ad_type, bodystyle, make, model, odometer, ad_state, price, picture_url):
        #Go through all listings, if ID found then update. Otherwise, add a new listing.
        for l in self.listings:
            if(l.id == idx):
                l.update_listing(price)
                return
        self.listings.append(listing(idx, title, ad_type, bodystyle, make, model, odometer, ad_state, price, picture_url))

    def __update_from_page(self, website):
        title = ""
        picture_url = ""
        odemeter = -1
        page = BeautifulSoup(website, 'html.parser')
        listings = page.find_all("div", class_="listing-items")
        if(len(listings) == 0):
            log("Error, does CAPTCHA exist?")
            return 0
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
            #Get Odo
            for details in listing.find_all('li', class_="key-details__value", recursive=True):
                try:
                    if(details['data-type'] == "Odometer"):
                        odometer = details.decode_contents()
                        break
                except Exception as e:
                    print(e)
                    odometer = -2
            #Add the new listing, or update an existing one if this is found.
            try:
                self.__add_listing(
                    listing.attrs['id'], 
                    title,
                    listing.attrs['data-webm-vehcategory'],
                    listing.attrs['data-webm-bodystyle'],
                    listing.attrs['data-webm-make'],
                    listing.attrs['data-webm-model'],
                    odometer,
                    listing.attrs['data-webm-state'],
                    listing.attrs['data-webm-price'],
                    picture_url)
            except Exception as e:
                log("Error parsing ID %s" % listing.attrs['id'])
                log(e)
        return len(listings)

    def update_search(self, skip):
        log("---- Starting update for %s ----" % self.name)
        self.last_updated = time.time()
        d = carsales_scraper(600)
        #get first page
        #loop through all listings, see if any haven't been updated. If so, mark as sold or unavailable.
        page = 0
        total = 0
        num = 1
        while(num):
            url = self.search_url + "&offset=" + str(12*page)
            log("Querying page %d" % (page+1))
            #start parsing
            website = d.load_page(url)
            d.check_captcha(website)            
            #website = open("output1.txt", "r")
            log("Finding listings on current page")
            num = self.__update_from_page(website)
            log("%d listings added" % num)
            #website.close()
            ###########BREAK EARLY################
            total += num
            #break
            page += 1
            #get next page
            #TODO
        log("---- No more listings found, exiting. Total: %d ----" % total)
        #Check if any listing weren't updated after the last_updated time, and then change the status
        #TODO change this to check for listings which have sold and whether they were put on hold, unavailable or sold.
        #Need more processing power to do this.
        for l in self.listings:
            if(l.price_history[-1][1] < self.last_updated):
                l.status = 0
            else:
                l.status = 1
        d.kill_driver()

    def print_listings(self):        
        for l in self.listings:
            l.print_listing()
            print("")

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
                except:
                    log("Failed to load \"%s\" - Exiting" % file)
                    sys.exit(1)

    def add_search(self, name, url):
        found = 0
        temp = saved_search(name, url)
        for s in self.searches:
            if(s.name == temp.name):
                log("Search already exists - Continuing")
                found = 1
        if(found == 0):
            self.searches.append(temp)

    def update_all_searches(self):
        log("Updating %d searches" % len(self.searches))
        for s in self.searches:
            #skip captcha, update this search.
            s.update_search(0)
            log("Update successful - Saving")
            #init filenames and lock
            filename = self.searches_dir+s.name+".obj"
            filelockname = filename+".lock"
            #open lock and save with pickle 
            with FileLock(filelockname):
                open(filelockname, "wb")
                file_pi = open(filename, 'wb') 
                pickle.dump(s, file_pi)
                file_pi.close()
            log("Saved")
        log("All searches updated and saved, exiting")



def main():
    base_url = "https://www.carsales.com.au/cars/"
    search_url = "https://www.carsales.com.au/cars/?q=(And.Service.carsales._.Make.Nissan._.Drive.Rear+Wheel+Drive._.GenericGearType.Manual._.Induction.Turbo._.Year.range(..2001).)&sort=%7ePrice"

    s = saved_searches("./saved_searches/")
    s.add_search("nissan_turbo_search", search_url)
    s.update_all_searches()

    s.searches[0].print_listings()

    
if __name__ == "__main__":
    main()
