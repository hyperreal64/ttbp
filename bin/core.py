#!/usr/bin/python

'''
ttbp: tilde town blogging platform
(also known as the feels engine)
a console-based blogging program developed for tilde.town
copyright (c) 2016 ~endorphant (endorphant@tilde.town)

core.py:
this is a core handler for some ttbp standalone/output functions

GNU GPL BOILERPLATE:

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

the complete codebase is available at:
https://github.com/modgethanc/ttbp
'''

import os
import time
import subprocess
import re
import mistune

import chatter

SOURCE = os.path.join("/home", "endorphant", "projects", "ttbp", "bin")
USER = os.path.basename(os.path.expanduser("~"))
PATH = os.path.join("/home", USER, ".ttbp")

LIVE = "http://tilde.town/~"
WWW = os.path.join(PATH, "www")
CONFIG = os.path.join(PATH, "config")
DATA = os.path.join(PATH, "entries")
FEED = os.path.join(SOURCE, "www", "index.html")
DOCS = os.path.join(SOURCE, "www", "help.html")
NOPUB = os.path.join(CONFIG, "nopub")

HEADER = ""
FOOTER = ""
FILES = []

def load():
    '''
    get all them globals set up!!
    '''

    global HEADER
    global FOOTER

    HEADER = open(os.path.join(CONFIG, "header.txt")).read()
    FOOTER = open(os.path.join(CONFIG, "footer.txt")).read()

    load_files()

def load_files():
    '''
    file loader

    * reads user's nopub file
    * loads all valid filenames that are not excluded in nopub to global files list
    '''

    global FILES

    exclude = []

    if os.path.isfile(NOPUB):
        for line in open(NOPUB, "r"):
            exclude.append(line.rstrip())

    FILES = []
    for filename in os.listdir(DATA):
        if filename in exclude:
            continue
        filename = os.path.join(DATA, filename)
        if os.path.isfile(filename) and valid(filename):
            FILES.append(filename)

    FILES.sort()
    FILES.reverse()

def write(outurl="default.html"):
    '''
    main page renderer

    * takes everything currently in FILES and writes a single non-paginated html
    file
    * calls write_page() on each file to make permalinks
    '''

    outfile = open(os.path.join(WWW, outurl), "w")

    outfile.write("<!--generated by the tilde.town blogging platform on "+time.strftime("%d %B %y")+"\nhttp://tilde.town/~endorphant/ttbp/-->\n\n")

    for line in HEADER:
        outfile.write(line)

    outfile.write("\n")

    for filename in FILES:
        write_page(filename)
        for line in write_entry(filename):
            outfile.write(line)

        outfile.write("\n")

    for line in FOOTER:
        outfile.write(line)

    outfile.close()

    return os.path.join(LIVE+USER,os.path.basename(os.path.realpath(WWW)),outurl)

def write_page(filename):
    '''
    permalink generator

    * makes a page out of a single entry for permalinking, using filename/date as
    url
    '''

    outurl = os.path.join(WWW, "".join(parse_date(filename))+".html")
    outfile = open(outurl, "w")

    outfile.write("<!--generated by the tilde.town blogging platform on "+time.strftime("%d %B %y")+"\nhttp://tilde.town/~endorphant/ttbp/-->\n\n")

    for line in HEADER:
        outfile.write(line)

    outfile.write("\n")

    for line in write_entry(filename):
        outfile.write(line)

    outfile.write("\n")

    for line in FOOTER:
        outfile.write(line)

    outfile.close()

    return outurl

def write_entry(filename):
    '''
    entry text generator

    * dump given file into entry format by parsing file as markdown
    * return as list of strings
    '''

    date = parse_date(filename)

    entry = [
        "\t\t<p><a name=\""+date[0]+date[1]+date[2]+"\"></a><br /><br /></p>\n",
        "\t\t<div class=\"entry\">\n",
        "\t\t\t<h5><a href=\"#"+date[0]+date[1]+date[2]+"\">"+date[2]+"</a> "+chatter.month(date[1])+" "+date[0]+"</h5>\n"
        #"\t\t\t<P>"
    ]

    raw = []
    rawfile = open(os.path.join(DATA, filename), "r")

    for line in rawfile:
        raw.append(line)
    rawfile.close()

    entry.append("\t\t\t"+mistune.markdown("".join(raw), escape=False, hard_wrap=False))

    #for line in raw:
        #entry.append(line+"\t\t\t")
        #if line == "\n":
        #    entry.append("</p>\n\t\t\t<p>")

    #entry.append("</p>\n")
    entry.append("\t\t\t<p style=\"font-size:.6em; font-color:#808080; text-align: right;\"><a href=\""+"".join(date)+".html\">permalink</a></p>\n")
    entry.append("\n\t\t</div>\n")

    return entry

def parse_date(file):
    '''
    parses date out of pre-validated filename

    * assumes a filename of YYYYMMDD.txt
    * returns a list:
      [0] 'YYYY'
      [1] 'MM'
      [2] 'DD'
    '''

    rawdate = os.path.splitext(os.path.basename(file))[0]

    date = [rawdate[0:4], rawdate[4:6], rawdate[6:]]

    return date

def meta(entries = FILES):
    '''
    metadata generator

    * takes a list of filenames and returns a 2d list:
      [0] absolute path
      [1] ctime
      [2] wc -w
      [3] timestamp "DD month YYYY at HH:MM"
      [4] entry date YYYY-MM-DD
      [5] author

    * sorted in reverse date order by [4]
    '''

    meta = []

    for filename in entries:
      ctime = os.path.getctime(filename)
      wc = subprocess.check_output(["wc","-w",filename]).split()[0]
      timestamp = time.strftime("%Y-%m-%d at %H:%M", time.localtime(ctime))
      date = "-".join(parse_date(filename))
      author = os.path.split(os.path.split(os.path.split(os.path.split(filename)[0])[0])[0])[1]


      meta.append([filename, ctime, wc, timestamp, date, author])

    meta.sort(key = lambda filename:filename[4])
    meta.reverse()

    return meta

def valid(filename):
    '''
    filename validator

    * check if the filename is YYYYMMDD.txt
    '''

    filesplit = os.path.splitext(os.path.basename(filename))

    if filesplit[1] != ".txt":
        return False

    pattern = '^((19|20)\d{2})(0[1-9]|1[0-2])(0[1-9]|1\d|2\d|3[01])$'

    if not re.match(pattern, filesplit[0]):
        return False

    return True

def write_global_feed(blogList):
    '''
    main ttbp index printer

    * sources README.md for documentation
    * takes incoming list of formatted blog links for all publishing blogs and
      prints to blog feed
    '''

    outfile = open(FEED, "w")

    ## header
    outfile.write("""\
<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 3.2//EN\">
<html>
    <head>
        <title>tilde.town feels engine</title>
        <link rel=\"stylesheet\" href=\"style.css\" />
    </head>
    <body>
        <div class="meta">
        <h1>tilde.town feels engine</h1>

        <h2><a href="https://github.com/modgethanc/ttbp">github
        repo</a> | <a
        href="http://tilde.town/~endorphant/blog/20160510.html">state
        of the ttbp</a></h2>
        <!--<p>curious? run <b>~endorphant/bin/ttbp</b> while logged in to tilde.town.</p>
        <p>it's still a little volatile. let me know if anything breaks.</p>---></div>
        <p>&nbsp;</p>
""")

    ## docs
    outfile.write("""\
        <div class="docs">""")
    outfile.write(mistune.markdown(open(os.path.join(SOURCE, "..", "README.md"), "r").read()))
    outfile.write("""\
        </div>""")

    ## feed
    outfile.write("""\
        <p>&nbsp;</p>
        <div class=\"feed\">
        <h3>live feels-sharing:</h3>
            <ul>""")
    for blog in blogList:
        outfile.write("""
                <li>"""+blog+"""</li>\
                    """)

    ## footer
    outfile.write("""
            </ul>
        </div>
  </body>
</html>
""")

    outfile.close()

#############
#############
#############

def test():
    load()

    metaTest = meta()

    for x in metaTest:
      print(x)
