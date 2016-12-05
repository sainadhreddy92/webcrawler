import re
import sys
import time
import math
import urllib2
import urlparse
import optparse
from cgi import escape
from traceback import format_exc
from Queue import Queue, Empty as QueueEmpty

from bs4  import BeautifulSoup



USAGE = "%prog"
VERSION = "0.2"
__version__ = "0.2"

AGENT = "%s/%s" % (__name__, __version__)

class Fetcher(object):
  def __init__(self,url):
    self.url = url
    self.urls = []

  def __getitem__(self, x):
    return self.urls[x]

  def _addHeaders(self, request):
    request.add_header("User-Agent", AGENT)
  
  def open(self):
    url = self.url
    try:
      request = urllib2.Request(url)
      handle = urllib2.build_opener()
    except IOError:
      return None
    return (request, handle)

  def fetch(self):
    request, handle = self.open()
    self._addHeaders(request)
    if handle:
      try:
        #content = unicode(handle.open(request).read(), "utf-8",
                        #errors="replace")
        content = handle.open(request).read()
        soup = BeautifulSoup(content,"html.parser")
        tags = soup('a')
      except urllib2.HTTPError, error:
        if error.code == 404:
          print >> sys.stderr, "ERROR: %s -> %s" % (error, error.url)
        else:
          print >> sys.stderr, "ERROR: %s" % error
        tags = []
      except urllib2.URLError, error:
        print >> sys.stderr, "ERROR: %s" % error
        tags = []
      for tag in tags:
        href = tag.get("href")
        if href is not None:
          url = urlparse.urljoin(self.url, escape(href))
          if url not in self.urls:
            self.urls.append(url)


class Crawler(object):

    def __init__(self, root, depth):
        self.root = root
        self.depth = depth
        self.host = urlparse.urlparse(root)[1]
        self.urls = []
        self.links = 0
        self.followed = 0

    def crawl(self):
        page = Fetcher(self.root)
        page.fetch()
        q = Queue()
        for url in page.urls:
            q.put(url)
        followed = [self.root]

        n = 0

        while True:
            try:
                url = q.get()
            except QueueEmpty:
                break

            n += 1

            if url not in followed:
                try:
                    host = urlparse.urlparse(url)[1]
                    if  re.match(".*%s" % self.host, host):
                        followed.append(url)
                        self.followed += 1
                        page = Fetcher(url)
                        page.fetch()
                        for i, url in enumerate(page):
                            if url not in self.urls:
                                self.links += 1
                                q.put(url)
                                self.urls.append(url)
                        if n > self.depth and self.depth > 0:
                            break
                except Exception, e:
                    print "ERROR: Can't process url '%s' (%s)" % (url, e)
                    print format_exc()


def parse_options():
  parser = optparse.OptionParser(usage=USAGE, version=VERSION)

  parser.add_option("-q", "--quiet",
  	action="store_true", default=False, dest="quiet",
    	help="Enable quiet mode")

  parser.add_option("-l", "--links",
        action="store_true", default=False, dest="links",
        help="Get links for specified url only")

  parser.add_option("-d", "--depth",
        action="store", type="int", default=30, dest="depth",
        help="Maximum depth to traverse")

  opts, args = parser.parse_args()

  if len(args) < 1:
    parser.print_help()
    raise SystemExit, 1

  return opts, args



def get_links(url):
  pge = Fetcher(url)
  page.fetch()
  for i, url in enumerate(page):
     print "%d. %s" % (i, url)

def main():
  opts, args = parse_options()
  opts, args = parse_options()

  url = args[0]

  if opts.links:
    getLinks(url)
    raise SystemExit, 0

  depth = opts.depth

  sTime = time.time()

  print "Crawling %s (Max Depth: %d)" % (url, depth)
  crawler = Crawler(url, depth)
  crawler.crawl()
  print "\n".join(crawler.urls)

  eTime = time.time()
  tTime = eTime - sTime

  print "Found:    %d" % crawler.links
  print "Followed: %d" % crawler.followed
  print "Stats:    (%d/s after %0.2fs)" % (
            int(math.ceil(float(crawler.links) / tTime)), tTime)
  
if __name__=='__main__':
  main()
