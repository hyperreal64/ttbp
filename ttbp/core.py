#!/usr/bin/python

'''
ttbp: tilde town blogging platform
(also known as the feels engine)
a console-based blogging program developed for tilde.town
copyright (c) 2016 ~endorphant (endorphant@tilde.town)

core.py:
this is a core handler for some ttbp standalone/output functions

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

the complete codebase is available at:
https://github.com/modgethanc/ttbp
'''

import os
import time
import subprocess
import re
import mistune
import json

from . import chatter
from . import config
from . import gopher
from . import util

FEED = os.path.join("/home", "endorphant", "public_html", "ttbp", "index.html")
SETTINGS = {}

HEADER = ""
FOOTER = ""
FILES = []
NOPUBS = []

def load(ttbprc={}):
    '''
    get all them globals set up!!
    '''

    global HEADER
    global FOOTER
    global SETTINGS

    HEADER = open(os.path.join(config.USER_CONFIG, "header.txt")).read()
    FOOTER = open(os.path.join(config.USER_CONFIG, "footer.txt")).read()
    SETTINGS = ttbprc

    load_nopubs()
    load_files()

def reload_ttbprc(ttbprc={}):
    '''
    reloads new ttbprc into current session
    '''

    global SETTINGS

    SETTINGS = ttbprc

def get_files(feelsdir=config.MAIN_FEELS):
    """Returns a list of user's feels in the given directory (defaults to main
    feels dir)"""

    files = []
    for filename in os.listdir(feelsdir):
        if nopub(filename):
            unpublish_feel(filename)
        else:
            filename = os.path.join(feelsdir, filename)
            if os.path.isfile(filename) and valid(filename):
                files.append(filename)

    files.sort()
    files.reverse()

    return files

def load_files(feelsdir=config.MAIN_FEELS):
    '''
    file loader

    * reads user's nopub file
    * calls get_files() to load all files for given directory
    * re-renders main html file and/or gopher if needed
    '''

    global FILES

    load_nopubs()
    FILES = get_files(feelsdir)
    if publishing():
        write_html("index.html")
        if SETTINGS.get('gopher'):
            gopher.publish_gopher('feels', FILES)

def load_nopubs():
    """Load a list of the user's nopub entries.
    """

    global NOPUBS

    NOPUBS = []

    if os.path.isfile(config.NOPUB):
        for line in open(config.NOPUB, "r"):
            if not re.match("^# ", line):
                NOPUBS.append(line.rstrip())

    return len(NOPUBS)

## html outputting

def write_html(outurl="default.html"):
    '''
    main page renderer

    * takes everything currently in FILES and writes a single non-paginated html
    file
    * calls write_page() on each file to make permalinks
    '''

    outfile = open(os.path.join(config.WWW, outurl), "w")

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

    return os.path.join(config.LIVE+config.USER,os.path.basename(os.path.realpath(config.WWW)),outurl)

def write_page(filename):
    '''
    permalink generator

    * makes a page out of a single entry for permalinking, using filename/date as
    url
    '''

    outurl = os.path.join(config.WWW, "".join(util.parse_date(filename))+".html")
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

    date = util.parse_date(filename)

    entry = [
        "\t\t<p><a name=\""+date[0]+date[1]+date[2]+"\"></a><br /><br /></p>\n",
        "\t\t<div class=\"entry\">\n",
        "\t\t\t<h5><a href=\"#"+date[0]+date[1]+date[2]+"\">"+date[2]+"</a> "+chatter.month(date[1])+" "+date[0]+"</h5>\n"
        #"\t\t\t<P>"
    ]

    raw = []
    rawfile = open(os.path.join(config.MAIN_FEELS, filename), "r")

    for line in rawfile:
        raw.append(line)
    rawfile.close()

    entry.append("\t\t\t"+mistune.markdown("".join(raw), escape=False, hard_wrap=False))

    #for line in raw:
        #entry.append(line+"\t\t\t")
        #if line == "\n":
        #    entry.append("</p>\n\t\t\t<p>")

    #entry.append("</p>\n")
    entry.append("\t\t\t<p class=\"permalink\"><a href=\""+"".join(date)+".html\">permalink</a></p>\n")
    entry.append("\n\t\t</div>\n")

    return entry

def write_global_feed(blogList):
    '''
    main ttbp index printer

    * sources README.md for documentation
    * takes incoming list of formatted blog links for all publishing blogs and
      prints to blog feed
    '''

    try: 
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
        outfile.write(mistune.markdown(open(os.path.join(config.INSTALL_PATH, "..", "README.md"), "r").read()))
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
        #subprocess.call(['chmod', 'a+w', FEED])
    except FileNotFoundError:
        pass

## misc helpers

def meta(entries = FILES):
    '''
    metadata generator

    * takes a list of filenames and returns a 2d list:
      [0] absolute path
      [1] mtime
      [2] wc -w
      [3] timestamp "DD month YYYY at HH:MM"
      [4] entry date YYYY-MM-DD
      [5] author

    * sorted in reverse date order by [4]
    '''

    meta = []

    for filename in entries:
      mtime = os.path.getmtime(filename)
      try:
        wc = int(subprocess.check_output(["wc","-w",filename], stderr=subprocess.STDOUT).split()[0])
      except subprocess.CalledProcessError:
        wc = "???"
      timestamp = time.strftime("%Y-%m-%d at %H:%M", time.localtime(mtime))
      date = "-".join(util.parse_date(filename))
      author = os.path.split(os.path.split(os.path.split(os.path.split(filename)[0])[0])[0])[1]

      meta.append([filename, mtime, wc, timestamp, date, author])

    #meta.sort(key = lambda filename:filename[4])
    #meta.reverse()

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

def find_ttbps():
    '''
    returns a list of users with a ttbp by checking for a valid ttbprc
    '''

    users = []

    for townie in os.listdir("/home"):
        if os.path.exists(os.path.join("/home", townie, ".ttbp", "config", "ttbprc")):
            users.append(townie)

    return users

def publishing(username=config.USER):
    '''
    checks .ttbprc for whether or not user opted for www publishing
    '''

    ttbprc = {}

    if username == config.USER:
        ttbprc = SETTINGS

    else:
        ttbprc = json.load(open(os.path.join("/home", username, ".ttbp", "config", "ttbprc")))

    return ttbprc.get("publishing")

def www_neighbors():
    '''
    takes a list of users with publiishing turned on and prepares it for www output
    '''

    userList = []

    for user in find_ttbps():
        if not publishing(user):
            continue

        userRC = json.load(open(os.path.join("/home", user, ".ttbp", "config", "ttbprc")))

        url = ""
        if userRC["publish dir"]:
            url = config.LIVE+user+"/"+userRC["publish dir"]

        lastfile = ""
        try:
            files = os.listdir(os.path.join("/home", user, ".ttbp", "entries"))
        except OSError:
            files = []
        files.sort()
        for filename in files:
            if valid(filename):
                lastfile = os.path.join("/home", user, ".ttbp", "entries", filename)

        if lastfile:
            last = os.path.getctime(lastfile)
            timestamp = time.strftime("%Y-%m-%d at %H:%M", time.localtime(last)) + " (utc"+time.strftime("%z")[0]+time.strftime("%z")[2]+")"
        else:
            timestamp = ""
            last = 0

        userList.append(["<a href=\""+url+"\">~"+user+"</a> "+timestamp, last])

    # sort user by most recent entry
    userList.sort(key = lambda userdata:userdata[1])
    userList.reverse()
    sortedUsers = []
    for user in userList:
        sortedUsers.append(user[0])

    write_global_feed(sortedUsers)

def nopub(filename):
    '''
    checks to see if given filename is in user's NOPUB
    '''

    return os.path.basename(filename) in NOPUBS

def toggle_nopub(filename):
    """toggles pub/nopub status for the given filename

    if the file is to be unpublished, delete it from published locations
    """

    global NOPUBS

    action = "unpublishing"

    if nopub(filename):
        action = "publishing"
        NOPUBS.remove(filename)
    else:
        NOPUBS.append(filename)
        unpublish_feel(filename)

    nopub_file = open(config.NOPUB, 'w')
    nopub_file.write("""\
# files that don't get published html/gopher. this file is
# generated by ttbp; editing it directly may result in unexpected
# behavior. if you have problems, back up this file, delete it, and
# rebuild it from ttbp.\n""")
    for entry in NOPUBS:
        nopub_file.write(entry+"\n")
    nopub_file.close()

    load_files()

    return action

def bury_feel(filename):
    """buries given filename; this removes the feel from any publicly-readable
    location, and moves the textfile to user's private feels directory"""

    pass

def delete_feel(filename):
    """deletes given filename; removes the feel from publicly-readable
    locations, then deletes the original file."""

    feel = os.path.join(config.MAIN_FEELS, filename)
    if os.path.exists(feel):
        subprocess.call(["rm", feel])
        load_files(config.MAIN_FEELS)

def unpublish_feel(filename):
    """takes given filename and removes it from public_html and gopher_html, if
    those locations exists. afterwards, regenerate index files appropriately."""

    live_html = os.path.join(config.WWW,
            os.path.splitext(os.path.basename(filename))[0]+".html")
    if os.path.exists(live_html):
        subprocess.call(["rm", live_html])
    live_gopher = os.path.join(config.GOPHER_PATH, filename)
    if os.path.exists(live_gopher):
        subprocess.call(["rm", live_gopher])

def process_backup(filename):
    """takes given filename and unpacks it into a temp directory, then returns a
    list of filenames with collisions filtered out.

    ignores any invalidly named files or files that already exist, to avoid
    clobbering current feels. ignored files are left in the archive directory
    for the user to manually sort out."""

    backup_dir = os.path.splitext(os.path.splitext(os.path.basename(filename))[0])[0]
    backup_path = os.path.join(config.BACKUPS, backup_dir)

    if not os.path.exists(backup_path):
        subprocess.call(["mkdir", backup_path])

    subprocess.call(["chmod", "700", backup_path])
    subprocess.call(["tar", "-C", backup_path, "-xf", filename])
    backup_entries = os.path.join(backup_path, "entries")

    backups = os.listdir(backup_entries)
    current = os.listdir(config.MAIN_FEELS)

    imported = []

    for feel in backups:
        if os.path.basename(feel) not in current:
            imported.append(os.path.join(backup_entries, feel))

    imported.sort()
    return imported

def import_feels(backups):
    """takes a list of filepaths and copies those to current main feels.

    this does not check for collisions.
    """

    pass


#############
#############
#############

def test():
    load()

    metaTest = meta()

    for x in metaTest:
      print(x)
