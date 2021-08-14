#https://stackoverflow.com/questions/64979042/how-to-run-seleniumchrome-on-raspberry-pi-4

from pyvirtualdisplay import Display

display = Display(visible=0, size=(1600, 1200))
display.start()
driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')