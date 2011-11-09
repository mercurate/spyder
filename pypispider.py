#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, time, urllib, sgmllib, subprocess
from urlparse import urljoin

URL = 'http://pypi.python.org/simple/'
HERE = os.path.dirname(os.path.abspath(__file__))

POSTFIX = '.tar.gz'

# packages in this list will be downloaded first.
LINKS = ['Django', 'mercurial'] 

class LinkPicker(sgmllib.SGMLParser):
    def __init__(self, verbose=0):
        self.links = []
        sgmllib.SGMLParser.__init__(self, verbose)

    def start_a(self, attributes):
        for key, value in attributes:
            if key == 'href':
                if self.filter and not self.filter(value):
                    continue
                self.links.append(value)
    
    def get_sub_links(self, link, filter = None):
        self.filter = filter
        r = urllib.urlopen(link)
        c = r.read()
        r.close()
        # <br/> tag in pypi site will cause SGMLParser find only the first link, remove it here.
        # though, <br /> will be OK, too.
        c = c.replace('<br/>', '')
        self.feed(c)
        self.close()
        return self.links
        

def get_sub_links(link, filter = None):
    if not link.endswith('/'):
        link = link + '/'
    print 'get_sub_links from url', link
    return LinkPicker().get_sub_links(link, filter)

def download(link, filename = ''):
    if not filename:
        b = link.rindex('/')
        e = link.index(POSTFIX)
        filename = link[b+1:e] + POSTFIX
    cmd = 'curl -o %s %s' % (os.path.join(HERE, filename), link)
    print cmd        
    subprocess.check_call(cmd.split(), cwd = HERE)


if __name__ == '__main__':
    
    print 'downloading...'
    LINKS.extend(get_sub_links(URL))
    for link in LINKS:
        if not link.endswith('/'):
            link = link + '/'
        home = urljoin(URL, link)
        sublinks = get_sub_links(home, lambda link: POSTFIX in link)

        for i in sublinks:
            x = urljoin(home, i)
            download(x)
