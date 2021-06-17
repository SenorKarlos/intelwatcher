# Intel Watcher

A script that allows you to scrape the Ingress Intel Map and use that information to fill a database or update Stops/Gyms that have missing info.

This fork optimized ClarkyKent's code and adds multithreading, making it run about 50 times faster for me (10 minutes to 10 seconds). It also adds options to update the login cookie automatically, by logging into Intel on its own.

### Credits

- [ClarkyKent](https://github.com/ClarkyKent/ingress_scraper) who made the original Scraper
- [The Ingress API](https://github.com/lc4t/ingress-api) this is based on

## Setup

### Database

Intel Watcher uses PMSFs database structure. If you have PMSF set up, just put its DB name in your config to also have Portals shown on your Map. Else, you can run `mysql your_db_name < ingress_portals.sql` to create a new table.

By default, the credentials you put in will also be used to access both your RDM/MAD and Portal database. If you have them running on different servers, you can add `scan_host`, `scan_port`, `scan_user` and/or `scan_password` to the config and put in different options to define access to your MAD/RDM database.

### Cookies

Intel Watcher needs to be able to log into the Intel Map in order to get Portal info. It does that with the login cookie.

#### Notes

- Use a burner Account to log into Intel (!!) **Scraper Accounts have been banned before**
- A Cookie runs out after 14 days. Explained below are a few ways you can get a new one.
- When using Facebook to automatically log in, you might have to wait an hour after creating the FB account.

### How to get Cookies

#### Automatic

Intel Watcher has the ability to log into the Intel Map and renew the cookie on its own. It does that by simulating a browser, which can be done in different ways. In case logging in fails, you'll receive a Webhook (if enabled) and it tries again after an hour.

**Mechanize**: Mechanize allows easy and light-weight web-browsing in Python but comes with a few disadvantages. **It only allows logging into Intel using Facebook**. So open your Ingress App, log into your burner Ingress Account and link it to a burner Facebook Account. Now log into Intel using Facebook once.

In the config you then have to set `module` to `mechanize`, put in your login data and set `enable` to `True`. Ignore the Selenium section.

**Selenium**: Selenium basically allows to drive a whole Webbrowser with Python, this means you'll have to install Chrome, Chromium or Firefox on your machine. [Quick installation can be found here](https://selenium-python.readthedocs.io/installation.html) anything else you'll have to google.

You can then fill out the config: Set `module` to `selenium`, put in your Google/Facebook login and set `enable` to `True`. Under the Selenium section you can set the type of Browser you installed and what logintype you want to use.

#### Manual

1. Create an Ingress account using the Ingress Prime app on your phone
2. Run `intel_watcher.py` once and let it fail to create a cookie.txt file
3. Open a new incognito window in your browser
4. Log into your burner account [here](https://intel.ingress.com/intel) with the same Email
5. Zooming into your area *may* improve results.
6. Press F12 and go to the Network tab, refresh the site (F5), then select `intel` in left coulumn and your window should look something like the Screenshot below. (Chrome)

![csrftoken-same-cookie](https://i.imgur.com/y7KFNI0.png)

7. Now copy everything after `cookie:` (the content highlighted in the red box) and paste it into `cookie.txt`
8. You can repeat these steps when your cookie runs out. But begin with 3.

### BBOX

To set up an area to scrape, go to [bboxfinder.com](http://bboxfinder.com) and select your desired area using the rectangle tool. Now copy the String after `Box` in the bottom field.

Note that you can use multiple bboxes in your config by seperating them with `;`. e.g. `-0.527344,5.441022,27.246094,20.138470;2.245674,48.795557,2.484970,48.912572`

![BBOX params](https://i.imgur.com/QKROPSU.jpg)

### Running the script

Now proceed as usual: `pip3 install -r requirements.txt`, fill in the config and you're done.

- `python3 intel_watcher.py` to scrape the area
- `python3 intel_watcher.py -u` to update Gyms and Stops with missing title and photo

### Faster runtimes

Intel Watcher works by requesting X map tiles from the IntelMap. You can set X using the `-t` argument. Default is 15, max is 25.

The requests are happening within threads. You can set the amount of threads running simultaneously (= workers) in the config and with the `-w` argument. 

I recommend only setting a few workers in your config, since the script will be running in the background anyway and use less resources that way.

When running the script manually, a command similiar to this will produce the fastest runtime possible: `python intel_watcher.py -w 50 -t 20`. You can play around with the numbers and see what works best for you.
