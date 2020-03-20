# elliptical-box-maker

Inkscape plug-in that generates drawings for an elliptical box which can be made using a laser cutter.
##Overview

This [Inkscape](https://inkscape.org/) plugin is intended to help you create laser cuttable designs.
To give you an idea about what it can do. Here are some examples that were made using this plugin.
![Boxes](/images/boxes.jpeg)
![Simple box](/images/foobarbox.jpeg)

With a little bit of effort it is also possible to make something a bit more original. For example:
![A dinosaur](/images/dinosaur.jpeg)
![Sea life](/images/fish%20n%20shark.jpeg)


## Installation
It's probably a good idea to use the [latest release](https://github.com/BvdP/elliptical-box-maker/releases) in stead of downloading the latest commit. 
The latest commit is probably work in progress and may not be a very good user experience.

You need to download the source code and copy `ell_box.py` and `ell_box.inx` to your Inkscape extensions directory (see below). You also need another extension https://github.com/BvdP/Inkscape_helper . Put the two files in a folder called "Inkscape_helper" (note the capital I) and put the folder into the extensions directory where you put the ell_box.pi and ell_box.inx files.

The other files are part of this documentation that you are reading, there is no need to copy those.
If you then start Inkscape the plugin should show up in the Extensions menu under Laser Tools --> Elliptical Box Maker.

In the following paragraphs "local install" means installing in your own inkscape folders. You don't need special rights to do this but other users cannot use the plugin (unless they install it themselves).
"System wide install" means that every user on the system can use the plugins but you need admin rights to install them.

### On Windows:
* Local install: put both files in `C:\Users\USERNAME\AppData\Roaming\inkscape\extensions` (where USERNAME is your username, i.e. the name you use when you log in)
* System wide install: put the files in `C:\Program Files\Inkscape\share\extensions`

### On Linux or Mac:
* Local install: put both files in `~/.config/inkscape/extensions`
* System wide install: put them in `/usr/share/inkscape/extensions`

# Usage

For now check the [tutorial](http://www.instructables.com/id/Generating-elliptical-boxes-using-a-laser-cutter-a/) on Instructables.
