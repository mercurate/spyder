#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os, re, time, shutil
import urllib, sgmllib, subprocess

from urlparse import urljoin
from optparse import OptionParser
INDEX_URL = 'http://pypi.python.org/simple/'
UPLOAD_URL = 'http://10.10.20.223:8088/'
UPLOAD_DIR = '/opt/chishop/media/dists/'
POSTFIX = '.tar.gz'
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ['HOME']
DEST = HERE

FILE_INDEX = os.path.join(HERE, 'requirements.txt')
FILE_LINKS = os.path.join(HERE, 'links.txt')
FILE_MD5   = os.path.join(DEST, 'links.md5')

MAIL_MSG = ['spyder log info:']

def touchfile(filename):
    os.system('touch %s' % filename)

def append2file(line, filename):
    os.system('echo "%s" >> %s' % (line, filename))

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
    print 'get links form', INDEX_URL
    links = get_links(INDEX_URL)
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
    PKGS = f.readlines()
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
        pkg_url = urljoin(INDEX_URL, line)
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
            print '%s exists here, skip.' % filename
            continue
        
        x = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(x):
            # this pkg is in chishop already
            print '%s exists in chishop, skip.' % x
            continue
        
        cmd = 'curl -C- -o %s %s' % (fullname, link)
        print cmd
        subprocess.call(cmd.split(), cwd = DEST)
        MAIL_MSG.append(cmd)
        
    f.close()

def md5check():
    fl = open(FILE_LINKS)
    fm = open(FILE_MD5, 'w')
    for link in fl:
        if link and 'md5' in link:
            link = link.strip()
            md5 = link[-32:]
            filename = get_filename(link)
            fm.write('%s  %s\n' % (md5, filename))
    fl.close()
    fm.close()
    cmd = 'md5sum -c %s' % FILE_MD5
    subprocess.call(cmd.split(), cwd = DEST)

def upload(path=DEST, delete=0):
    path = os.path.join(HERE, path)
    config()
    for entry in os.listdir(path):
        f = os.path.join(path, entry) # abs path
        if not os.path.isfile(f):
            continue
        if not f.endswith('.tar.gz'):# is not pkg
            continue
                
        if f.endswith('.tar.gz'):
            x = os.path.join(UPLOAD_DIR, entry)
            if os.path.exists(x):# in chishop already
                #~ os.remove(os.path.join(path, f))
                print '%s is in chishop already' % entry
                continue
            
            d = f[0:f.index('.tar.gz')]
            f = os.path.join(path, f)
            d = os.path.join(path, d)
            
            if os.path.exists(d):
                print '%s exists, rm it' % d
                shutil.rmtree(d)
            
            c = 'tar -xzf %s' % (f)
            print c
            try:
                subprocess.check_call(c.split(), cwd = path)
                # 解压没出错，就把文件删除
#                if delete:
#                    print 'rm',f
#                    os.remove(f)
            except Exception, e:
                print 'tar error:', e
                continue
    cmd = 'python setup.py register -r %s sdist upload -r %s' % (UPLOAD_URL, UPLOAD_URL)
    print 'uploading start...'
    for entry in os.listdir(path):
        print 'processing', entry
        d = os.path.join(path, entry)
        if not os.path.isdir(d):
            print '%s is not dir, skip' % d
            continue
        if not os.path.exists(os.path.join(d, 'setup.py')):# is not pkg
            print '%s is not a pkg dir, skip' % entry
            continue
        
        try:
            print 'uploading %s' % d
            subprocess.call(cmd.split(), cwd = d)
            print 'rm', d
            shutil.rmtree(d)
        except Exception, e:
            print 'error occurd while uploding:', e
            continue
                    
def collect(src):
    if not os.path.exists(src):
        print 'dir %s not found' % src
        return
    for root, dirs, files in os.walk(src):
        for f in files:
            if f.endswith('.tar.gz'):
                f = os.path.join(root, f)
                shutil.copy2(f, DEST)
                print 'cp %s %s' % (f, DEST)

CONFIG = '''
[distutils]
index-servers =
    pypi
    local

[pypi]
username:spig
password:ab12cd

[local]
repository:%s
username:spig
password:ab12cd
''' % UPLOAD_URL

def config():
    print 'override your ~/.pypirc'
    rc = os.path.join(HOME, '.pypirc')
    fp = open(rc, 'w')
    fp.write(CONFIG)
    fp.close()

def mail():
    import smtplib
    sender = 'spig@insigma.com.cn'
    receivers = ['guoqiao@insigma.com.cn']
    subject = 'chishop notification'
    message = '\n'.join(MAIL_MSG)
    mail = 'From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s\r\n' % (sender, ', '.join(receivers), subject, message)
    h = smtplib.SMTP('smtp.insigma.com.cn', 587)
    h.login(sender, '123456')
    h.sendmail(sender, receivers, mail)
    h.quit()
    print mail    

def main():
    parser = OptionParser()
    parser.add_option("-l", "--links", 
                      action="store_true", dest="links", default=False,
                      help="get dist links")
    parser.add_option("-d", "--download",
                      action="store_true", dest="download", default=False, 
                      help="download dists")
    parser.add_option("-u", "--upload",
                      action="store_true", dest="upload", default=False, 
                      help="register and upload all pkgs")
    parser.add_option("-c", "--check",
                      action="store_true", dest="check", default=False, 
                      help="md5 check for all dists")
    parser.add_option("-x", "--delete",
                      action="store_true", dest="delete", default=False, 
                      help="delete files after upload")                      
    parser.add_option("-s", "--start",
                      action="store", dest="start", default='', 
                      help="start from this keyword")
    parser.add_option("-e", "--collect",
                  action="store", dest="collect", default='', 
                  help="collect pkgs from some dir recursive")

    (options, args) = parser.parse_args()
    print options, args
    if options.links:
        links(options.start)
    elif options.download:
        download(options.start)
    elif options.upload:
        path = args[0] if args else DEST
        upload(path, options.delete)
    elif options.check:
        md5check()
    elif options.collect:
        collect(options.collect)
    else:
        links()
        download()
        upload(delete=1)
        mail()

if __name__ == '__main__':
    main()
    
