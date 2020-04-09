# Plex Metadata Agents for Gay Adult Video
**Please read all this document before usage**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/preview.gif)
### How to install
1. Clone this repository to your Plex server and copy all of the .bundle folders and their contents to your plugin folder. [Can't find the folder?](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder)
2. Restart your PMS and Login to the web interface and open settings.
3. In Settings > Server > Agents select "Gay Adult" and/or "Gay Adult Films" and/or "Gay Adult Scenes" and check any/all agents you wish to use.
4. Gay Adult is contains all of the agents (perhaps for those who commingle Films and Scenes in the same plex library)
5. Gay Adult Films contains specifically the Film agents (e.g., AEBN, GEVI, GayDVDEmpire).  Use in libaries which will mostly or only contain full-length films (see image below)
6. Gay Adult Scenes contains agents for blog sites (WayBig, Fagalicious, QueerClick).  Use in libaries which will mostly or only contain scenes (see image below)
7. In Settings > Server > Agents order the agents by your personal preference (e.g., if most of your movies are found in AEBN, consider putting AEBN first); uncheck Local Media Assets (Movies).
8. Create a new library or change the agent of an existing library to the "Gay Adult" or "Gay Adult Scenes" or "Gay Adult Films" agent, then refresh all metadata.

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



### Gay Erotic Video Index (GEVI) Tips and Considerations:

GEVI has a TREMENDOUS amount of indexed content, but has some quirks that are easy to navigate, if you follow a couple rules, beginning with the filing naming convention (Studio) - Title (Year).ext.  

1.  In GEVI as in the other Agents, if on windows, one cannot use a colon (:) in a filename.  If the site uses a colon either in the Studio or Title, ignore it.

2.  When manually searching for a movie, GEVI's results page will display the Company (i.e. Distributor), not the Studio.  The Agent requires the Studio which is often different, so select the movie and click into the movie page.  However, make note of the Title from the Results list.  In this case, the filename should be **(BoyCrush) - Big Uncut Fuckfest, Kyler Moss's (2013).mp4**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/results.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/movie1.jpg)

3.  There are times when the movie page may have multiple line titles (previous and next image).  Use the Title from the Results list.  In this case, the filename should be **(Jake Cruise Media) - Cruise Collection 68 Mike Roberts (2008).mp4**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/movie2.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/results1.jpg)

4.  There are times when the movie page may have one or more AKA titles.  Use the Title from the Title on the movie page.  This last example is a good one.  Two movie titles.  Three company names.  The correct filename should be **(Pietro Filmes) - Mãos à Obra (2001).mp4**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/results2.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/movie3.jpg)


5.  Once you get used to the quirks of GEVI, it is an incredible Agent.  


### Some final tips:  

1.  The Agent will attempt to crop the scene poster for display in plex, using either an inline cropping service, or if unavailable a visual basic script (for Windows PMS installations).  If both fail, the agent will return the (often oversized) poster as-is from the blog site.  

2.  If you come across a site that indexes films or scenes and has plex style movie covers, it may be a good candidate for a new Agent.  Open an issue and make a request.  **Note: ** we will not create studio specific Agents...studios don't offer plex style movie covers and often update the framework of their site which breaks Agents.

3.  If you have any challenges or struggles, open a new issue.  Please describe your challenge as thoroughly as possible, including which agent you were targeting, the filename and include the log, if you can. **Note:** please, no screenshots that contain graphic content. 

## Disclaimer


This project stores no images or metadata. All metadata is downloaded directly from publicly-available sources
