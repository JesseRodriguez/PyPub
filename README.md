# PyPub
Extra simple publication/reference manager with a text interface. I wrote it up because I wanted something strong enough to build out a large publication library with my own categorization structure, but I didn't want to work with some big publication manager that didn't suit my needs. For instance, when I read publications, I annotate and draw on them digitally, and I want to see those annotations when I go back to read them. PyPub offers a simple way to do this. It will not be very helpful if you don't use BibTex.

_____

## Quick Tutorial

1. First, use the environment.yaml file to make sure you have all the dependencies and 'install' PyPub. This will use conda to create a new environment.
~~~
    (base)$ git clone https://github.com/JesseRodriguez/PyPub
    (base)$ cd PyPub
    (base)$ conda env create -f environment.yaml
    (base)$ conda activate pypub
~~~

2. Next, fill in the library directory (the directory in which you'd like to store your database and article .pdfs) and the pub sort directory (essentially a 'paper pile' where you toss .pdfs and corresponding .bib files when you're ready to add them to the database) in your `config.yaml` file.
~~~
    LibDir: /path/to/library/directory
    PubSortDir: /path/to/pub/sort/directory
~~~

3. `PubMngr.py` functions as the main publication manager application; run it with python and the text prompts will guide you through its use. Before adding a publication, drop its associated .pdf into your `PubSortDir`. If you have a .bib entry for it, either add a .bib file to `PubSortDir` with the same file name or let the script help you create one.
~~~
    (pypub)$ python PubMngr.py
~~~

4. If you've added a bunch of .pdfs with no associated .bib files to `PubSortDir`, run `bibMkr.py` to create them.
~~~
    (pypub)$ python bibMkr.py
~~~

_____

## A MacOS Recommendation

I think it's nice to have icons on my desktop that fire up a terminal window and run `PubMng.py` and `bibMkr.py`. If you think so too, use Automator to create an application with a 'run shell script' action. Then, paste the following into the ensuing window:
~~~
    osascript -e 'tell application "Terminal"
        do script "cd /Users/jesse/Documents/Literature && source activate pypub && python PubMngr.py"
        set bounds of front window to {0, 0, 980, 500}
    end tell'
~~~

This will make an app that runs `PubMngr.py` and open it in a terminal window of a certain size. Save the result in the applications folder and drag a shortcut onto your desktop. I even made some logos that are included in this repo if you're interested.

_____

### I wish you luck on your next literature review!
_____
