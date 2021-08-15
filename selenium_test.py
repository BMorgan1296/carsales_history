#https://stackoverflow.com/questions/64979042/how-to-run-seleniumchrome-on-raspberry-pi-4
#https://stackoverflow.com/questions/35956045/extract-title-with-beautifulsoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup, NavigableString, Tag

from pyvirtualdisplay import Display

import atexit
import sys
import time
import random
  
sys.path.insert(0, './bypass_geetest_slider')

#from bypass_geetest_slider.captcha_solver.nocaptcha import CapatchaSolver

driver = None

def log(logstr):
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print("%s: %s" % (current_time, logstr))



    #https://www.carsales.com.au/cars/used/nissan/south-australia-state/adelaide-region/para-hills-5096-suburb/manual-transmission/turbo-induction/under-3000/over-10000km-kilometres/over-1500cc-engine-size/over-80kw-power/over-1500kg-towing-brakes/
class carsales_scraper:
    def __init__(self):
        log("Beginning display setup")
        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()
        log("Display started, setting Driver options")

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

        log("Starting Driver")
        self.driver = webdriver.Chrome(options=self.chrome_options, executable_path='/usr/lib/chromium-browser/chromedriver')

    def load_page(self, url):
        website = None
        loading_finished = 0                   # Set flag to 0
        while loading_finished == 0:           # Repeat while flag = 0
            try:
                self.driver.set_page_load_timeout(45)
                time.sleep(random.uniform(0.1, 0.5)) # wait some time
                loading_finished = 1            # Set flag to 1 and exit while loop
            except:
                log("Timeout - retry")
        else:
            log("Page loaded")

    def get_curr_webpage(self):
        website = self.driver.get(url)       # try to load for n seconds
        return website

    def test_captcha_exist(self, basepage):
        self.load_page(basepage)
        try:
            geetest = driver.find_element_by_class_name("geetest_radar_tip")
            print(geetest)
            log("Geetest captcha found")
            # captcha_solver = CapatchaSolver(self.driver)
        except Exception as e:
            log("No Geetest captcha found")

    def get_curr_listings(self, html):
        print("TODO")

    def kill_driver(self):
        self.driver.close()
        self.driver.quit()

class car_advert():
    def __init__(self, id):
        self.id = id
        #self.last_updated = time.now()

def main():
    url = "https://www.carsales.com.au/cars/"
    url2 = "https://www.carsales.com.au/cars/?q=(And.Service.carsales._.Make.Nissan._.Drive.Rear+Wheel+Drive._.GenericGearType.Manual._.Induction.Turbo._.Year.range(..2001).)&sort=%7ePrice"

    #d = carsales_scraper()
    
    # log("Driver setup, querying CarSales")
    # time.sleep(3)
    # d.test_captcha_exist(url)

    # log("Querying Carsales for given URL")
    # d.load_page(url2)
    # page = d.get_curr_webpage()

    f = open("output1.txt", "r")
    page = BeautifulSoup(f, 'html.parser')
    listings = page.find_all("div", class_="listing-items")
    for listing in listings[0].find_all('div', class_="listing-item", recursive=False):
        print(listing.attrs['id'])
    f.close()
    
if __name__ == "__main__":
    main()