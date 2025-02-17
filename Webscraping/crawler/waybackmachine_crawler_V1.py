import codecs
import re
import requests
import time
import datetime
import pdb
import os
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
import sys
sys.path.append(os.path.abspath('../download'))
from data_reader import data_reader

class waybackmachine_crawler:

    def __init__(self, website = None, output_folder="../../out", year_folder=False):
        if website is not None: 
            self.websites = [website]
        else: 
            self.websites = []
        self.output_folder = output_folder
        self.year_folder = year_folder
        print("Looking at new website {0}...".format(website))


    # Takes URL from split_url function, converts it into the correct format, and returns the domain as well as the adress
    def split_wayback_url(self, wayback_url):
        original_url = re.sub(r'http://web.archive.org/web/\d+/',"",wayback_url)
        website_piece = re.sub(r"http(s?)\://","", original_url)

        try:
            (domain, address) = website_piece.split("/", 1)            
        except ValueError:
            domain  = website_piece
            address = ""

        
        domain = data_reader.clean_domain_url(domain)
        
        return (domain, address)



    
    def store_page(self, url, html):

        (domain, address) = self.split_wayback_url(url) 
        if self.year_folder:                    # Checking whether directory stores by year or not
            base_directory = "{0}/{1}/{2}".format(self.output_folder, domain, self.crawled_year)
        else:
            base_directory = self.output_folder + "/" + domain
            
        # If no directory exists, creating a new one
        if not os.path.exists(base_directory):
                os.makedirs(base_directory)
                print('Directory not found. Creating a new base Directory!')

        if address == "":
            address = "homepage.html"
        
        # Saves html file
        file_path = base_directory +  "/" + address.replace("/","_")
        outfile = codecs.open(file_path, "w",'utf-8')
        outfile.write(html)
        outfile.close()
        print ("\t .Stored in: {0}".format(file_path))
        

        

    def is_valid_url(self, url):
        if url.endswith(".pdf") or url.contains("godaddy") or url.contains("bobparsons"):
            return False
        
        if url == "." or url == "..":
            return False

        return True

    
    def crawl(self, wayback_url, levels=1, done_urls={}): #'levels' describes the depth of recursive crawling
        #Recursive algorithm
        print ("\t .Crawl [L={0}].. {1}".format(levels, wayback_url))
        
        clean_url = re.sub("\?.*","",wayback_url)
        clean_url = re.sub(r"\#.*","",clean_url)

        try:                    # Saving html code of website
            response  = requests.get(clean_url)
            html = response.text
            self.store_page( clean_url, html)
        except ConnectionError as e:
            print ("Connection Error: Skipping") # If not possible: skipping to the next url
            return done_urls
            
            
        done_urls = self.add_done_url(clean_url, done_urls)     # Saving crawled urls
        
        counter = 0

        if levels > 0:

            (domain, address) = self.split_wayback_url(clean_url)
            
             # Parsing the HTML to find all hyperlinks
            soup = BeautifulSoup(html, features="html.parser")
            for link in soup.findAll('a', attrs={'href': re.compile(domain)}):            
                url = link['href']
                print("\t" + url)
                
                ## Skipping Conditions: Begin
                # Checking if url is valid for crawling
                if not self.is_valid_url(url):
                    print("\t .Skipped (not a valid url)")
                    continue

                if not url.startswith("http"):
                    url = "http://web.archive.org" + url

                # if url not done.. Scrape it.
                if self.url_done(url, done_urls):
                    print("\t .Skipped (already done)")

                counter += 1                
                if counter >= 9:
                    print("\t .10 links donwloaded for website. Done.")
                    break
                #Skipping Conditions: End
                    
                done_urls = self.crawl(url, levels-1, done_urls)



        return done_urls


    # Notes: If no year.. then stored under key value 0
    # Defining the function that keeps track of already analyzed urls
    def add_done_url(self, wayback_url, done_urls):
        
        if self.year_folder is True and self.crawled_year not in done_urls:
            done_urls[self.crawled_year] = []

        elif self.year_folder is False and done_urls  == {}:
            done_urls[0] = []

        ix = self.crawled_year if self.year_folder is True else 0
        
        done_urls[ix].append(wayback_url)

        return done_urls

    
    def url_done(self,url,done_urls):
        ix = self.crawled_year if self.year_folder is True else 0

        if url in done_urls[ix]:            
            return True

        if url.replace("www.","") in done_urls[ix]:
            return True

        return False

#### Main function that initializes the crawler
    def crawl_from_date(self, year, month, day): # I can keep the date list, and just put in the current data/ the date of data collection 
        snapshot = self.list_closest_snapshot(year,month,day)
        self.crawled_year = year
        
        if snapshot is not None:
            self.crawl(snapshot['url'])


    def is_valid_url(self, url):
        if "mailto" in url:
            return False

        if len(url) > 200:
            return False
        
        return True

        


        
    def list_closest_snapshot(self, year, month, day):
        timestamp = datetime.date(year = year, month = month, day = day).strftime("%Y%m%d")
        print("\t .Getting snapshots.  Timestamp = {0}".format(timestamp))
        url = "http://archive.org/wayback/available?url={0}&timestamp={1}".format(self.websites, timestamp)

        response = requests.get(url)
        snapshots = response.json()["archived_snapshots"]

        if len(snapshots) > 0:    
            return snapshots["closest"]
        else:
            return None
    
    def set_websites(self, websites):
        self.websites = websites


    #Starting Function
    def start_crawling(self, levels = 1):
        for website in self.websites:
            self.crawl(website, levels)


