# inmatedb

A server application for collecting data about incarceration in the United States.

### Data Sources: 
https://www.capecountysheriff.org/roster.php?grp=10

### Technologies Used:
+ [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/#description) for web scraping
+ [TinyDB](https://tinydb.readthedocs.io/en/latest/) for database management
+ [Flask 2.0](https://flask.palletsprojects.com/en/2.0.x/api/) for RESTful api implementation
  + [Flask RESTful](https://flask-restful.readthedocs.io/en/latest/)
  + [Apache2](https://httpd.apache.org/docs/2.4/) http server
+ [Pushbullet Channels](https://blog.pushbullet.com/2014/09/30/introducing-pushbullet-channels/) for server notifications
  + [Pushbullet Python API](https://github.com/rbrcsk/pushbullet.py) for communicating with pushbullet servers


### API Documentation:
+ [inmatedb api docs](https://documenter.getpostman.com/view/16660912/Tzm9kaor) using postman documenter
+ [docs workspace](https://www.postman.com/cryosat-astronaut-60319953/workspace/36378a89-1b57-4545-8d17-00f2688fb29c/documentation/16660912-717899a6-ee46-486f-9a9f-0df0dad0b2be) postman docs workspace


### Test Server:
Temporarily, for one month, I'll host a test-server on linode.

<s>For now, you can test the api endpoints using this address: http://inmatedb.crabdance.com/api/</s>
(Temp server shutdown Aug 23, 2021.)



### Deployment Instructions:

#### My server configuration on [linode ($5/mo)](https://www.linode.com/):
 ```
 UbuntuServer 21.04
 RAM: 1GB
 CPU/CORES: 1
 ```

#### Instructions:
```
$ sudo apt update && sudo apt upgrade

# Clone the repo into /var/www
$ cd /var/www
$ git clone https://github.com/TheyCallMeTojo/inmatedb.git

# Install required python packages
$ cd inmatedb
$ sudo apt install python3-pip -y
$ sudo pip3 install -r requirements.txt

# Start scraper app
$ sudo python3 scraper_app.py
# Wait for first scrape to complete, then continue.
## Either terminate with CTRL-C, or create a new tmux pane/window.

# Install apache2
$ sudo apt install apache2
$ sudo apt-get install -y libapache2-mod-wsgi-py3 python3-dev

# Make sure that you see "active (running)"
$ sudo service apache2 status

# Set secret key for WSGI
$ export SECRET_KEY=your_secret_key

# Config apache for our server app
$ sudo nano inmatedb.conf
# Edit config file by replacing <SERVIER_IP> with your server's Public IP (or a sub/domain.)
$ sudo mv inmatedb.conf /etc/apache2/sites-available/
$ sudo a2ensite inmatedb.conf

# Change repo directory permissions so apache has access
$ cd /var/www/
$ sudo chown -R www-data:www-data inmatedb/
$ cd inmatedb

# Restart apache
$ systemctl reload apache2

# Restart the scraper app using www-data as the user
$ sudo -u www-data python3 scraper_app.py
```

