# Log for OOO Calendar

## 2021-10-09

Problem statement: I would like a way to view OOO time of Trussels at a glance, ideally in my existing calendar tools. I would like this to be trustable (so, kept up to date automatically from the source of truth, which is currently Paylocity).

I know that Paylocity has an automatic report of all OOO time that is in CSV format. Currently, I believe that in order to get it, I’ll need to SFTP the CSV report from them after they generate it based on conversations with Eady.

### Initial architecture notes

I want this running on a server somewhere. I don’t yet know if I want to use something very high level like a Lambda, but I don’t have to decide that now. Ultimately, this system needs to ingest the Paylocity CSV, extract the relevant fields from the CSV (Name of Trussel, start of OOO, and duration or end of OOO), and then transform those fields into calendar data somehow.

Since I have done a *lot* of calendar related engineering in a previous life, I get to cheat. I know that calendar APIs are very complicated and hard to debug AND they are specific to a given calendar system. I’d like to avoid that. I know that there is a standard called iCalendar (no relation to the Apple Calendar app) that is defined in RFC 5545, and I know that this standard is implemented in every popular calendar system, including the two I care the most about for my own purposes: Apple Calendar and Google Calendar. (This is the standard that .ics files follow). I also know that both of these systems support iCalendar feed URLs that return iCalendar events that get displayed in the calendar UI and that are refreshed automatically. OK, cool, this seems like it’ll do the trick.

I also know that since I’m doing a transform, the generated calendar is read-only; I don’t care about supporting people *creating* OOO from within the calendar. They’ll still have to go to Paylocity to make updates.

OK, so what am I looking at wanting so far:

Since this is going to run server-side, I’m going to pick from the following languages:

JavaScript/TypeScript, Python, Ruby, Go, Rust

I have two serialization formats I need to support: I need to read CSV, and I need to write iCalendar. I know that I need more than split(“,” csvfile) to parse CSVs, because I have passed the Truss engineering interview, so let’s see who’s got CSV libraries:

### CSV Libraries

JavaScript has… many. Arguably, too many; there’s a ton of them, and I’m not sure which ones are actually maintained. There’s also the unfortunate “What JavaScript environment is this designed for?” problem; you can’t always tell if something is supposed to be browser-only or node-only. However, for my purposes, let’s assume that we will be able to find one that will work.

Python has a csv library built in. I like using built-in libraries when possible; avoiding dependencies is a good way to not have to screw around with things later and the APIs are usually very stable. The Python CSV library has been there for a while, so it seems like a good option.

Ruby also has a CSV library built in that’s been there for a while. It could also be a good option.

Go has a CSV library built in, so it might do.

Rust doesn’t have a CSV module built-in, and it does have a crate that seems to fit the bill. However, it’s not a built-in, so maybe I don’t want to do this.

I don’t think I have performance concerns here: the sample report I’m using is 135k with ~900 rows. I’d expect to start caring about performance at the 1 MB mark at worst, so let’s not worry about that.

### iCalendar libraries

JavaScript has an ICS library: https://www.npmjs.com/package/ics

Python has a couple: icalendar and ics in PyPy, plus a handful of others on Github. Icalendar shows how to generate iCalendar data, so it’s probably good enough, and the library notes talk about Python 3.9 and 3.10 compatibility, so it seems like it’s being maintained.

Ruby has an icalendar gem that seems robust.

Go has one, but boy, it’s undocumented and hasn’t been touched in 2 years.

Rust has one that is documented and seems to be kept up to date.


Alright. At this point, I’m looking pretty hard at Python and Ruby, and I remember that eventually I’m going to have to SFTP files, so… who’s got a library that can do that?

### SFTP libraries

JavaScript has one: https://openbase.com/js/ssh2-sftp-client and it appears to be “pure” JavaScript, which is important; I don’t want to have to figure out how to make sure that OpenSSH is correctly installed inside of a Lambda later.

Python has a couple. I’ve heard of paramiko before and know it works.

Ruby has at least one SFTP gem.

Go has at least one.

Rust also has one.

OK, but this gets funky, because SECURITY CODE is always a pain in the ass, and “pure language” implementations means they are re-implementing the security sensitive systems. So now I have an annoying tradeoff to make.

I decide to *punt* the annoying tradeoff to later; it looks like I’ve got some other choices to make.

I figure Lambda is going to be most restrictive environment and while it does support custom runtimes, it also has Node.js 14.x, Python 3.9 support and Ruby 2.7 support now. I’m willing to accept this constraint, because I believe that Lambda is probably the end-state for this tool due to better maintenance properties (I really don’t want to spend time on this after it’s working), and cost properties.

Really looks like Python or Ruby are my best choices here. I suck equally at both, so there’s no personal inclination towards either. OK, what are some other factors that might come into play? They’ve both got good testing infra built in. Ruby has a stronger dependency story with Bundler, and I’ve heard that there’s a Python equivalent to Bundler now, although I’ve never used it so that would be something to figure out. Python has typing annotations as of 3.6 and mypy, which I think I can use to save myself some pain. Ruby has a static typing story, but it seems newer and really wants Ruby 3, which Lambda doesn’t support yet (and seems pretty new).

OK, this all leads me to select Python 3.9.x for my runtime.

Cool cool cool. Let’s get started.

``` bash
cd ~/src
mkdir truss-ooo-calendar
cd truss-ooo-calendar
git init
```

NOTE: I’m deliberately not putting anything on Github yet; I’m the only person working on this, and I can upload the repo to GitHub later. OK, cool, let’s get my environment going. I’ve already got `asdf` setup as per Truss engineering standards, so:

`asdf list all python`

Returns a ton of stuff, but I have the 3.9.7 available so I update .tool-versions and asdf install. This takes a while.

OK. Given that I have a csv of data, I think the next thing I need to do is see if I can parse it. So, my next goal is to have a small function that takes the CSV file, and does something with it.

To start, I make a main.py, and drop the usual boilerplate in, and make it print Hello world. It works! This is great, my environment is working.

Now I add a function PaylocityCSVToData that returns the string it’s passed, and call that from main.py.

OK, that’s good. But I’m getting tired of running ./main.py all the time, so I make a simple Makefile and add phony run and test targets. Both of them just run ./main.py for now.

OK, but now, before I start to get too fancy, let’s get tests going. I’m going to use the built in unittest and make a simple test_main.py that verifies that PaylocityCSVToData returns the same string you pass into it. I also modify the Makefile to use unittest’s auto-discover for make test, so now I don’t have to think about that anymore.

I verify that if the strings don’t match, the test fails.

Since I have something that “works”, I commit everything with the time honored commit message of “Initial commit.”

Now to get some CSV parsing happening. I have some test data, but I don’t want to accidentally commit it into my project, so I add “test_data.csv” to my .gitignore. Later when I have some synthetic data for testing, I’ll add it back, but for now I want to work with the genuine article.

OK, so now I want to modify my function to take a file object. I change my test to match.

Now I do a bunch of iteration to figure out what I need to pull out of this CSV file… it’s kind of messy, and doesn’t have headers. From looking at my own vacation, I figure out which columns I think care about: name, type, start date, end date, and status.

OK, now I start pulling this apart. Make a function that turns a single row into a dict, make tests for it. Make another function that fixed the Paylocity name data, make a test for that.

Tests all pass, although the PaylocityCSVToData function test is effectively useless; I’m using it as a visual test runner and spewing data to the console to see what’s happening. However, since I’m pulling more and more out of it, I am not worried about it right now.

Got Mypy setup (make test now runs unitests and mypy), and added 1 type annotation to my simplest function. That all works!

That’s enough for today. Next steps seem to be finish parsing the CSV data into date objects and parsing the type and status fields into enums. *Maybe* worth turning that dict into an actual object, too. Then we can look into using those event objects to generate iCalendar data.

## 2021-10-10

Added type annotations to my functions and methods so far. This revealed one bug that already existed! Type annotations for Python feel confusing; they’ve obviously been iterated on pretty heavily, and are different in Python 3.9 vs. older Python 3 versions.

Python 3.9 has a bunch of built-in types for basics like list, dict, int ,float, etc. Python 3.8 and earlier don’t have those; you’re supposed to use the typing module, and do `from typing import Dict`.   Dict in 3.8 is equivalent to dict in 3.9. However, it seems like even in 3.9 you still need to use the typing module sometimes; for example, I have a function that takes a file object as a parameter, and I seem to need to do from typing import TextIO in order to get the right type for it.

OK, to be fair, TextIO probably isn’t the right type; Sequence[str] probably is, but we’ll deal with that later.

At this point, I’ve got working type checking (and proved that it will break my build if it fails), and I’ve got some data extracted from the CSV. I’ve also made the CSV extractor deal with empty rows in the original dataset, so we can now use it without modifying it first.

OK, using that, I add LeaveType and LeaveStatus enums. It was easy to implement the from_str methods in each: I implemented the NotImplementedError case first, and then ran the tests until I covered all of the cases in the test data for each enum. I am starting to question the value of LeaveType; I was thinking it might be useful to know if someone’s on vacation vs. sick, but that’s not really important, and could be considered a privacy violation. I’ll leave it in for now, but if I end up not using it when I generate iCalendar data I’ll remove it.

I should convert this event dict into a LeaveEvent class next. Once that’s done, I can wire up the iCalendar library.

Before doing that, I decide to take a detour and set up pre-commit, prereqs, and black. Pre-commit is mostly to keep me honest about black. Prereqs is just to help when, in theory, I look at this in the future. Black I want to get setup now so I don’t have to think about formatting again, and it’s easier to do that sooner than later.

Now that’s done and my files are all formatted, I turn the dict into a LeaveEvent class. I’m doing this because, in general, I prefer to have small known shapes of data instead of using a generic dict to act as a struct. I believe I will be able to take advantage of type checking in the future as well. However, I have to pay a price for this that I don’t like: dict gets equality for free, and I have to write my own __eq__ method now. I’m sure there is a clever way to do this but I don’t know it, so I do a very brute force and error prone thing and check == for all of the properties by hand. It’s ugly, and it works.

I read over the documentation for the two iCalendar libraries: ics.py and icalendar.py. ics.py looks easier to use, but also less mature. A decision for tomorrow.

## 2021-10-11

OK, since I need a dependency, I now need to figure out how to manage them. It looks like Python has pipenv now, which appears to be more or less the same as Ruby’s Bundler. Let’s try it.

OK, it is more or less the same (Pipfile and Pipfile.lock, which seem to be what I expect). I’m fully expecting this to betray me later; the ecosystem obviously still thinks `pip` and `virtualenv` are the way to do things, which is… surprising, given how fragile those tools are and how Ruby and node have demonstrated a Much Better Way To Do This for the last decade or so. Still, no requirements.txt needed so far.

I get mypy and black installed via pipenv; they continue to work. I then install icalendar. No type shims, so I tell mypy to ignore that module for now.

Then I convert the start_date and end_date properties of LeaveEvent from str to datetime, and parse the dates from the CSV data. At this point, all of the structured data in the CSV is now parsed into “real” objects instead of strings (well, except for name, which is fine as a string).

Finally, I rename PaylocityCSVToData to PaylocityCSVToLeaveEvents, and have it return the events list.

## 2021-10-12

Get a simple Calendar object built. Have to look some stuff up in the RFC, but hey, that’s why there are RFCs. Start to build a VEVENT and then calamity strikes: I need to figure out how to make timezones work in Python. Historically, this hasn’t been built-in, and involved using a dependency (pytz). However, as of Python 3.9, zoneinfo is builtin and pytz is deprecated. Better late than never, I suppose.

After hacking around a bit, I learn some things. I learn that VEVENT components need to have DTSTAMP and UID properties. I learned that “all day” events are synthesized; you make them by setting DTSTART to just a date, and DTEND to the following day. I also did manage to generate an ICS file from the Paylocity data set that I have AND it loaded into Apple Calendar. Yay. Deleting the calendar data locked up Apple Calendar for almost a minute. Boo.

I used Apple Calendar to generate a couple of example events and stashed them in an examples directory for later.

OK. I now have a working CSV -> iCalendar transform and it appears to be correctly generate “all day” events.

I guess the next thing to figure out is how to SFTP the CSV data from Paylocity.

I learned that the data is available via SFTP on ftp.paylocity.com, with a filename like Time_Off_Requests_20211008.csv. All of the generated reports are there, so I’ll need some logic to collect the most recent one.

The credentials for this are in the 1Password Infra vault under “Paylocity SFTP for Time Off Request Reports”.

Cool. This is enough to get paramiko wired up.

pipenv install paramiko
pipenv install types-paramiko

That worked. Hacked together a little function that hardcoded everything and successfully listed files from the Paylocity server. Next steps: figure out how to deal with the secrets (password, in this case), and add some configuration so I can test against my own SFTP server.

Also, I’m starting to talk about this with MacRae and Eady, so I should get it up on GitHub, and move these notes into a markdown file in the project proper.
