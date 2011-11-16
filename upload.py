#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, subprocess, shutil

URL = 'http://10.10.20.223:8088'
HERE = os.path.abspath(os.path.dirname(__file__))
HOME = os.environ['HOME']
PYPI = os.path.join(HOME, '')
def main():    
    print 'start!'
    cmd = 'python setup.py register -r %s sdist upload -r %s' % (URL, URL)
    args = cmd.split(' ')
    for root, dirs, files in os.walk(PYPI):
        for d in dirs:
            try:
                shutil.rmtree(d)
            except:
                continue
                
        for f in files:
            if f.endswith('.tar.gz'):
                    d = f[0:f.index('.tar.gz')]
                    print f,d
                    print 'tar -xzf %s %s' % (f, d)
                    try:
                        subprocess.call(['tar', '-xzf', f, d], cwd = PYPI)
                        print 'uploading %s' % f
                        subprocess.call(args, cwd = d)
                        shutil.rmtree(d)
                    except:
                        os.remove(f)
                        continue
    return 0

if __name__ == '__main__':
    main()

