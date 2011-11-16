#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os, re, time
import urllib, sgmllib, subprocess

from urlparse import urljoin
from optparse import OptionParser
HERE = os.path.dirname(os.path.abspath(__file__))

URL = 'http://pypi.python.org/simple/'
POSTFIX = '.tar.gz'
DEST = os.path.join(HERE, 'pypi/')

FILE_INDEX = os.path.join(HERE, 'index.txt')
FILE_LINKS = os.path.join(HERE, 'links.txt')
FILE_MD5   = os.path.join(HERE, 'dists.md5')

PKGS = [
         'Django', 
         'django-cpserver',
         'django-celery',
         'django-auth-ldap',
         'flup',
         'MySQL-python', 
         'mercurial', 
         'Pygments',
         'python-ldap',
         'South',
         'pyquery',
         'virtualenv',
         'setuptools',
        ] 

class LinkPicker(sgmllib.SGMLParser):
    def __init__(self, verbose=0):
        self.links = []
        sgmllib.SGMLParser.__init__(self, verbose)

    def start_a(self, attributes):
        for key, value in attributes:
            if key == 'href':
                if self.re and not re.search(self.re, value):
                    continue
                self.links.append(value)
    
    def parse(self, url, re=''):
        self.re = re
        f = urllib.urlopen(url)
        c = f.read()
        f.close()
        c = c.replace('<br/>', '')
        self.filter = filter
        self.links = []
        self.feed(c)
        self.close()
        return self.links

def get_links(url, re=''):
    return LinkPicker().parse(url, re)

def index():
    print 'get links form', URL
    links = get_links(URL)
    s = '\n'.join(links)
    print s
    with open(FILE_INDEX, 'w') as f:
        f.write(s)
    print 'index save to', FILE_INDEX

def get_filename(link):
    b = link.rindex('/')
    e = link.index(POSTFIX)
    filename = link[b+1:e] + POSTFIX
    return filename


def get_latest_version(links):
    if not links:
        return ''
    d = {}
    for link in links:
        if not link:
            continue
        link = link.strip()
        if not link:
            continue
        filename = get_filename(link)
        d[filename] = link
    keys = d.keys()
    keys.sort()
    return d[keys[-1]]


def links(start=''):
    
    f = open(FILE_INDEX)
    PKGS.extend(f.readlines())
    f.close()
    
    if not start:
        if os.path.exists(FILE_LINKS):
            os.rename(FILE_LINKS, FILE_LINKS + '.bak')
        f = open(FILE_LINKS, 'w')
    else:
        f = open(FILE_LINKS, 'a')
    
    matched = False
    
    for line in PKGS:
        if not line:
            continue
        line = line.strip()
        if start and not matched:
            matched = start in line
            if not matched:
                print 'start from %s, %s skiped.' % (start, line)
                continue
        if not line.endswith('/'):
            line = line + '/'
        print 'get links for', line
        pkg_url = urljoin(URL, line)
        links = get_links(pkg_url, re='.tar.gz')
        link = get_latest_version(links)
        if link:
            if not link.startswith('http'):
                link = urljoin(pkg_url, link)
            print 'latest version for %s is %s' % (line, link)
            f.write(link + '\n')
            
    f.close()
    print 'links save to', FILE_LINKS

def download(start=''):    
    f = open(FILE_LINKS)
    matched = False
    for link in f:
        if not link:
            continue
            
        if start and not matched:
            matched = start in link
            if not matched:
                print 'start from %s, %s skiped.' % (start, link)
                continue            

        filename = get_filename(link)
        print 'file:', filename
        
        fullname = os.path.join(DEST, filename)
        if os.path.exists(fullname):
            print '%s exists, skip.' % fullname
            continue
            
        if '#md5=' in link:
            md5 = link[-32:]
            print 'md5:', md5
            if re.search('[0-9a-fA-F]{32}', md5):
                fmd5 = open(FILE_MD5, 'a')
                fmd5.write('%s  %s\n' % (md5, filename))
                fmd5.close()
        cmd = 'curl -C- -o %s %s' % (filename, link)
        print cmd        
        subprocess.call(cmd.split(), cwd = HERE)
        
    f.close()

def md5check():
    cmd = 'md5sum %s' % FILE_MD5
    subprocess.call(cmd.split(), cwd == HERE)

def main():
    parser = OptionParser()
    parser.add_option("-i", "--index", 
                      action="store_true", dest="index", default=False,
                      help="get pkg index")
    parser.add_option("-l", "--links", 
                      action="store_true", dest="links", default=False,
                      help="get dist links")
    parser.add_option("-d", "--download",
                      action="store_true", dest="download", default=False, 
                      help="download dists")
    parser.add_option("-s", "--start",
                      action="store", dest="start", default='', 
                      help="start from this keyword")
    parser.add_option("-c", "--check",
                      action="store_true", dest="check", default=False, 
                      help="md5 check for all dists")                       

    (options, args) = parser.parse_args()
    print options, args
    
    if options.index:
        index()
    elif options.links:
        links(options.start)
    elif options.download:
        download(options.start)
    elif options.check:
        md5check()
   

def test():
    f = open('links.txt')
    links = f.readlines()
    v = get_latest_version(links)
    print 'latest version is', v
    f.close()

if __name__ == '__main__':
    main()
    
