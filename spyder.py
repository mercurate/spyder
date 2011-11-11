#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, time, urllib, sgmllib, subprocess
from urlparse import urljoin

URL = 'http://pypi.python.org/simple/'
HERE = os.path.dirname(os.path.abspath(__file__))
POSTFIX = '.tar.gz'
# pkgs will be here
DEST = os.path.join(HERE, 'pypi/')
MD5_FILE = 'pkgs.md5'
# packages in this list will be downloaded first.
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
        
    def get_links(self, html):
        self.links = []
        self.feed(html)
        self.close()
        return self.links
        

def get_sub_links(link, filter = None):
    if not link.endswith('/'):
        link = link + '/'
    print 'get_sub_links from url', link
    return LinkPicker().get_sub_links(link, filter)

def download(link):
    print 'downloading', link
    
    # get filename form link
    b = link.rindex('/')
    e = link.index(POSTFIX)
    filename = link[b+1:e] + POSTFIX
    print 'file:', filename
    
    md5 = ''
    if '#md5=' in link:
        md5 = link[-32:]
        print 'md5:', md5
        if re.search('[0-9a-fA-F]{32}', md5):
            f = open(os.path.join(DEST, MD5_FILE), 'a')
            f.write('%s  %s\n' % (md5, filename))
            f.close()
    
    path = os.path.join(DEST, filename)
    if os.path.exists(path):
        if not md5:
            print '%s already exists, skip.(no md5 to checked)' % filename
            return
        # exists and has md5    
        tmp = 'tmp.md5'
        f = open(os.path.join(DEST, tmp), 'w')
        f.write('%s  %s\n' % (md5, filename))
        f.close()
        cmd = 'md5sum -c %s' % tmp
        try:
            subprocess.check_call(cmd.split(), cwd = DEST)
            # no check errors:
            print '%s already exists, skip.(md5 checked)' % filename
            return
        except Exception, e:
            print 'md5 check error:',e
            print 'downloading of %s will continue' % path
    # -C- 参数表示自动断点续传
    cmd = 'curl -C- -o %s %s' % (path, link)
    print cmd        
    subprocess.call(cmd.split(), cwd = HERE)

def main():    
    if not os.path.exists(DEST):
        os.makedirs(DEST)
    
    print 'DEST:', DEST    
    
    f = os.path.join(DEST, MD5_FILE)
    if os.path.exists(f):
        os.remove()
        
    print 'downloading...'
    
    links = get_sub_links(URL)
    
    with open('index.txt', 'w') as f:
        f.writelines(links)
        
    f = open('links.txt', 'w')
    
    PKGS.extend(links)
    for pkg in PKGS:
        if not pkg.endswith('/'):
            pkg = pkg + '/'
        pkg_home = urljoin(URL, pkg)
        sub_links = get_sub_links(pkg_home, lambda link: POSTFIX in link)
        
        for i in sub_links:
            if not i.startswith('http:'):
                i = urljoin(pkg_home, i)
            f.write(i + '\n')
            download(i)
    
    f.close()

import cmd
class Spyder(cmd.Cmd):
    
    def save_url(self, url):
        f = urllib.urlopen(url)
        c = f.read()
        f.close()
        c = c.replace('<br/>', '')
        finename = url.strip('/').split('/')[-1]
        if '.' not in filename:
            filename = filename + '.html'
        f = open(finename, 'w')
        f.write(c)
        f.close()
        print 'url %s save to %s' % (url, filename)
        return filename
        
    def get_links(self, filename):
        f = open(filename)
        c = f.read()
        f.close()
        links = LinkPicker().get_links(c)
        return links
        
    def save_links(self, links, filename):
        txt = os.path.join(filename, '.txt')
        f = open(txt, 'w')
        f.writelines(links)
        f.close()
        print 'all links in %s save to %s' % (filename, txt)        
    
    def do_update(self):
        f = urllib.urlopen(URL)
        c = f.read()
        f.close()
        c = c.replace('<br/>', '')
        links = LinkPicker().get_links(c)
        f = open('index.txt', 'w')
        f.writelines(links)
        f.close()
        
    def do_links(self):
        f = open('index.txt')
        x = open('links.txt', 'w')

        for line in f:
            if not line.endswith('/'):
                line = line + '/'
            base = urlparse.join(URL, line)
            links = LinkPicker().get_links(base)
            for link in links:
                if not link.startswith('http'):
                    link = urljoin(base, link)
                x.write(link + '/n')

        x.close()
        f.close()
            
    def do_download(self):
        m = open('links.md5', 'w')
        f = open('links.txt')
        for line in f:
            a = link.rindex('/')
            b = link.index('.tar.gz')
            filename = link[a+1:b] + '.tar.gz'
            if '#md5=' in link:
                md5 = link[-32:]
                m.write('%s  %s' % (md5, filename))
            fullname = os.join(DEST, filename)
            
            if os.path.exists(fullname):
                continue
            cmd = 'curl -C- -o %s %s' % (fullname, link)
            print cmd        
            subprocess.call(cmd.split(), cwd = HERE)

    def do_pkgs(self):
        links = get_links(self.index)
        save_links(links, self.index)
        f = open(html, 'r')
        links = LinkPicker().get_links(f.read())
        f.close()
        f = open('index.txt', 'w')
        f.writelines(links)
        f.close()
        print 'index.txt generated.'
        
    def do_links(self, index = 'index.txt'):
        f = open(index)
        links = open('links.txt', 'w')
        for line in f:
            links = LinkPicker().get_links(f.read())
                
    def do_EOF(self, line):
        return True
    
    def postloop(self):
        print

if __name__ == '__main__':
    Spyder().cmdloop()
