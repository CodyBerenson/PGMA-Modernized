# Plex Metadata Agents for Gay Adult Video
**Please read all this document before usage**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/preview.gif)
### How to install
1. Clone this repository to your Plex server and copy all of the .bundle folders and their contents to your plugin folder. [Can't find the folder?](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder)
2. Restart your PMS and Login to the web interface and open settings.
3. In Settings > Server > Agents select "Gay Adult" and/or "Gay Adult Films" and/or "Gay Adult Scenes" and check any/all agents you wish to use.
a.  Gay Adult is contains all of the agents (perhaps for those who commingle Films and Scenese in the same library)
b.  Gay Adult Films contains specifically the Film agents (e.g., AEBN, GEVI, GayDVDEmpire).  Use in libaries which will mostly or only contain full-length films (see image below)
c.  Gay Adult Scenes contains agents for blog sites (WayBig, Fagalicious, QueerClick).  Use in libaries which will mostly or only contain scenes (see image below)
4. In Settings > Server > Agents order the agents by your personal preference (e.g., if most of your movies are found in AEBN, consider putting AEBN first); uncheck Local Media Assets (Movies).
5. Create a new library or change the agent of an existing library to the "Gay Adult" or "Gay Adult Scenes" or "Gay Adult Films" agent, then refresh all metadata.

**View the README inside the studio folders to correctly label your files**

### Please Read
Usage for the Agents:

Feature Films:

(Studio) - Title (Year).ext

e.g.  

(Titan Media) - Copperhead Canyon (2008).mp4

(Raging Stallion Studios) - Manscent (2019).mp4

(Men) - Camp Chaos (2019).mp4

The matching agent will return the movie poster annd relevant metadata,actor thumbnails (matched from IAFD.com) 
![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/film.jpg)

Scens from blogs:

(Studio) - Title (Year).ext
e.g., 

(Men Series) - Bellamy Bradley, Alex Fortin, William Seed and Morgan Blake in 'Battle Buddies, Part 4' (2017).mp4

(Active Duty) - Phoenix River and Ryan Jordan (2018).mp4

(Sean Cody) - Jess Tops Deacon (Bareback) (2018).mp4

The matching agent will return a scene poster and relevant metadata,actor thumbnails (matched from IAFD.com) 
![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/scene.jpg)

Some tips:  
1.  Especially for WayBig, replace curly opening quotes with the standard single quote'.  Waybig will use a curly opening quote; if copying and pasting from the WayBig site, replace with a standard single quote.
2.  The Agent will attempt to crop the scene poster for display in plex, using either an inline cropping service, or if unavailable a visual basic script (for Windows PMS installations).  If both fail, the agent will return the (often oversized) poster as-is from the blog site.  

## Disclaimer


This project stores no images or metadata. All metadata is downloaded directly from publicly-available sources
