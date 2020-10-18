# Announcements

**10/18/2020**  We are finalizing the first version of our installation and usage guide for new folks.  The guide brings together everything below, along with some of the tips and step-by-steps we've provided in the issues.  If you're new to Plex, PMS, and its agents, the guide is perfect for you.

**10/11/2020**  Looks like October is turning out to be IAFD month.  Not in a good way.  LOL.  IAFD is having to rebuild their RAID array...never a good thing....so their site has been down for quite some time.  Impacts to our agents:  The IAFD agent will not work, nor will pulling performer's headshots for all of the other agents.  The other agents will match, pull metadata and poster, just not an actor's headshot.  Last time IAFD struggled, they moved from HTTP to HTTPS to get back online causing impacts to all of our Agents.  Fingers crossed for their return to service quickly without further impact to us.

https://twitter.com/iafdcom

**10/07/2020:** All agents have been updated due to the change IAFD made on their site two days ago.

**10/06/2020:** Yesterday, IAFD announced that they had site hardware challenges and in order to restore service they had to enable HTTPS.  This had two impacts to our agents, one catastrophic:
1.  The IAFD agent now does not work.  The code needs to be tweaked to support https.  As a work around, if you're not afraid of editing code, a work around can be found here:  https://github.com/CodyBerenson/PGMA-Modernized/issues/52#issuecomment-704012596

2.  All of our agents make calls to IAFD to retrieve Actor Thumbnail photos.  So, until every agent is updated to support https: for IAFD, thumbnail photos may not be returned.  

We'll make and test the updates as soon as we can.  This, of course, is the risk we run when indexing sites make updates (i.e. Fagalicious two months ago and now IAFD).

9/17/2020:  Our two new agents, GayRado and BestExclusivePorn have been fully tested and are now included in our repository of Agents!  A couple specifics:

**BestExclusivePorn:**  BestExclusivePorn.com contains both blogged scenes and full films.  Although the site doesn't include metadata for the names of the performers, the agent will look for performers in the title and use as metadata, when there's a match.  See instructions below for further details.

**GayRado:**  GayRado.com is a site with scrapeable metadata for full films.  A note of caution:  Similar to some other sites (RADVideo, HomoActive), the site has a terrible search.  Many titles are browsable but not searchable.  Therefore the agent will not be able to scrape metadata from a title that cannot be searched.

8/15/2020:  Jason has coded two new Agents:  GayRado and BestExclusivePorn.  The latter includes blogged scenes...perhaps an additional stopgap until Fagalicious can be remediated.  Both of the Agents are being tested and will be released soon, to add to your arsenal of Gay Porn Agents.  :)

07/26/2020:  Sometimes the news is not so good.  Fagalicious has updated their site and broken the Agent :(  The fix is a high degree of complexity, so it may be a while before Fagalicious is up and running. There are times when certain scenes are blogged only on Fagalicious and not on WayBig or QueerClick.   You should check out IAFD.com to see if the scene is there.  If it is, consider grabbing the cover poster art from Fagalicious (clip it if you're a perfectionisht) and using the IAFD Agent for the metadata.  Further clarity about this workaround can be found below in the IAFD tips.  And, as always if you need help, open an issue.  

07/14/2020:  AEBN News!  We have removed the legacy AEBNii from the repository of agents as we described below on 6/01.  Further, we have renamed the AEBN agent to AEBNiii, for those of you who wish to use both our AEBN agent and MrPlow254's AEBN agent.  You now have the best of both AEBN worlds!

07/11/2020:  We are relasing a new Agent!  PornTeam. This agent indexes the site pornteam.com.  We try to give you many options to index your content, and PornTeam is an additional option.  One note:  the site doesn't allow all of their content to be searched.  They have plenty of titles that are browsable, but not searchable (unsure if it is by design or mistake).  If a title is not able to be searched, it will be unable to be matched by the agent...even if the title, its metadata, and posterart are on the site (not unlike RAD and homoactive).  

06/13/2020:  Phase 2 of optional Language Translation now available!  All PGMA-Modernized Indexes now include the ability to translate film/scene summaries from/to alternative languages.  See below for a more detailed explanation.

06/12/2020:  Phase 1 of optional Language Translation now available!  For WayBig, Fagalicious, QueerClick, and IAFD Agents, we now offer optional language translation!   Perhaps you'd prefer not have the movie/scene summary in its native French?  Or, perhaps you'd prefer to get all movie/scene summaries translated to your native German, Korean, or Chinese?  You now have that option for your favorite scenes, and soon you'll soon have these options for all Agents, Agent by Agent. See below for a more detailed explanation.  

06/12/2020:  Local Media Assets now enabled!  See the explanation below for how to take advantage of Local Media Assets below.

06/12/2020:  FAQ Added!  See below.

06/03/2020:  Coming soon!  Each Agent is being updated to offer optional language translation!  

06/01/2020:  The new AEBN Agent is available!  It utilizes the modernized view of AEBN, and offers more metadata functionality (e.g., Exact release dates).  For now, we will support both the new AEBN agent and the legacy AEBNii agent.  However, it is our intent to retire the legacy AEBNii agent.  You won't be required to stop using AEBNii, it will just be removed from the repository and likely no longer supported (e.g., if AEBN makes an update to their site which breaks AEBNii).  

06/06/2020:  The GEVI Agent now allows you to use either the Studio or Distributor name (sometimes they are different) in the **(Studio)** portion of the (Studio) - Title (YYYY).ext naming convention.

05/11/2020 and 05/18/2020:  GayWorld and GayMovie agents were added to the already robust set of Films agents.  While both have limitations in the metadata available, both offer a decent portfolio of movies to match from, and both have superior poster artwork.  

# Plex Metadata Agents for Gay Adult Video
**Please read all this document before usage.  If you need help, please read below**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/preview.gif)
### How to install
1. Clone this repository to your Plex server and copy all of the .bundle folders and their contents to your plugin folder. [Can't find the folder?](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder)
2. Restart your PMS and Login to the web interface and open settings.
3. In Settings > Server > Agents select "Gay Adult" and/or "Gay Adult Films" and/or "Gay Adult Scenes" and check any/all agents you wish to use.
4. Gay Adult contains all of the agents (perhaps for those who commingle Films and Scenes in the same plex library)
5. Gay Adult Films contains specifically the Film agents (e.g., AEBN, GEVI, GayDVDEmpire).  Use in libaries which will mostly or only contain full-length films (see image below)
6. Gay Adult Scenes contains agents for blog sites (WayBig, Fagalicious, QueerClick).  Use in libaries which will mostly or only contain scenes (see image below)
7. In Settings > Server > Agents order the agents by your personal preference (e.g., if most of your movies are found in AEBN, consider putting AEBN first); check Local Media Assets (Movies) if you include your own poster artwork (see below).
8. Create a new library or change the agent of an existing library to the "Gay Adult" or "Gay Adult Scenes" or "Gay Adult Films" agent, then refresh all metadata.

### Please Read to correctly label your files ###
**Usage for the Agents:**

**Feature Films:**

(Studio) - Title (Year).ext

Find your film on one of the Index sites (e.g., AEBN.com or gayeroticvideoindex.com).  Name your file **using the specific title from the Index site**
e.g.  

(Titan Media) - Copperhead Canyon (2008).mp4

(Raging Stallion Studios) - Manscent (2019).mp4

(Men) - Camp Chaos (2019).mp4

The matching agent will return the movie poster and relevant metadata,actor thumbnails (matched from IAFD.com) 
![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/film.jpg)

**Scenes from blogs:**

(Studio) - Title (Year).ext

Find your scene on one of the Index sites (e.g., WayBig.com, QueerClick.com).  Name your file **using the specific title from the Index site**

e.g., 

(Men Series) - Bellamy Bradley, Alex Fortin, William Seed and Morgan Blake in 'Battle Buddies, Part 4' (2017).mp4

(Active Duty) - Phoenix River and Ryan Jordan (2018).mp4

(Sean Cody) - Jess Tops Deacon (Bareback) (2018).mp4

The matching agent will return a scene poster and relevant metadata,actor thumbnails (matched from IAFD.com) 
![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/scene.jpg)



### Gay Erotic Video Index (GEVI) Tips and Considerations:

GEVI has a TREMENDOUS amount of indexed content, but has some quirks that are easy to navigate, if you follow a couple rules, beginning with the filing naming convention (Studio) - Title (Year).ext.  

1.  In GEVI as in the other Agents, if on windows, one cannot use a colon (:) in a filename.  If the site uses a colon either in the Studio or Title replace with space dash space, i.e. " - ".

2.  When manually searching for a movie, GEVI's results page will display the Company (i.e. Distributor), not the Studio.  The Agent *now* allows you to use either.  Select the movie and click into the movie page.  However, make note of the Title from the Results list.  In this case, the filename should be **(BoyCrush) - Big Uncut Fuckfest, Kyler Moss's (2013).mp4**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/results.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/movie1.jpg)

3.  There are times when the movie page may have multiple line titles (previous and next image).  Use the Title from the Results list.  In this case, the filename should be **(Jake Cruise Media) - Cruise Collection 68 Mike Roberts (2008).mp4**

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/movie2.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/results1.jpg)

4.  There are times when the movie page may have one or more AKA titles.  **Use the Title from the Title on the movie page...not the results list as in the previous examples**.  This last example is a good one.  Two movie titles.  Three company names.  The correct filename is **(Pietro Filmes) - Mãos à Obra (2001).mp4** (but remember, you can now use Studio or Distributor)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/results2.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/movie3.jpg)


5. Once you get used to the quirks/workings of the Gay Erotic Video Index site itself, the GEVI is an incredible Plex Agent.  


### Internet Adult Film Database (IAFD) Tips and Considerations:
IAFD is a robust database of adult films and scenes (straight, bi, gay, etc.).  Sometimes, when a particular film can't be found on any of the other indexing sites, or a particular scene can't be found on any of the other blog sites, it will be on IAFD.  We consider it a next-to-last resort (last resort being manually tagging metadata and posters).  However, unlike the other indexes, IAFD contains no posters.  Everyone has their own individual tastes.  To some, the autogenerated poster from Plex may be just fine, as long as the metadata is pulled from IAFD.  For others, metadata isn't enough and a quality poster is needed.  For those whose taste falls into the latter, you have the option of finding a poster that you like for the content, and manually uploading it using Plex's built in functionality (or using Local Media Assets (Movies) (see below).  For example, often on Google you can find studio stills for a particular scene.  If you like one, copy the source URL and upload it manually.  Plex utilizes a 1 x 1.5 ratio for posters (e.g., 600 px width x 900 px height) .  If your image doesn't fit those ratios, Plex will auto crop.  For the connoisseur, you may want to manually adjust in Paint 3d, Photoshop, etc.

For example, the blogs contain very little indexed BlakeMason scene content, whereas IAFD had most, perhaps nearly all, of it (at last for the recent several years).  The IAFD Agent is a good option.

We recommend that you include it last in the order of priority, unless it is your particular go-to agent. 

### Local Media Assets (Movies) Considerations:
This is a useful tool to use, especially in combination with the IAFD Agent.  Suppose there is a film or a scene that can only be found on IAFD.  For example, many Pride Studios and Next Door Studios scenes can't be found on the blogs, but are indexed on IAFD.  Further, those two sites offers high quality photos (not still captures) for that scene, including a 1 x 1.5 ratio image.  If you create a subfolder (e.g., John and James), and put both the IAFD appropriately named scene file *and* the artwork image titled poster.jpg, Plex will grab the metadata for the scene from IAFD and use the poster.jpg image as the poster artwork if Local Media Assets (Movies) is checked in Plex's Agent Settings.   

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/poster3.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/poster2.jpg)

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/poster1.jpg)

Another type of local media assets are the tags that may be embedded within a file's properties.  If you'd prefer to use the resulting metadata from one of the blogs vs. what may be encoded in your file's properties, make sure that Local Media Agents is ranked lowest in the ordering of agents. 

### BestExclusivePorn Tips and Considerations

Unlike other blog sites, this site does not include metadata for performers names.  A workaround, specifically for scenes, has been built into the agent.  The agent will look for sets of two words both beginning with Upper Case, assume they're an actor's name, and look for a match in IAFD.  

For example, (NextDoorRaw) - **D**on’t **S**top **D**acotah **R**ed fucks **Z**ak **B**ishop bareback (2020).mp4....the agent will see if it can find matches for "Don't Stop", "Dacotah Red" and "Zak Bishop" as it parses thru congruent sets of two capitalized words.  Not finding a match for "Don't Stop", the agent will properly build metadata and actor information and headshot for the remaining two matches (Dacotah Red and Zak Bishop).  

However, if, for example the title was (NextDoorRaw) - **P**lease **D**on’t **S**top **D**acotah **R**ed fucks **Z**ak **B**ishop bareback (2020).mp4, in order to properly return preformaer metadata/headshots you would manually have to change the case on "**S**top"...otherwise, the agent will look for the following actors:  Please Don't, Stop Dacotah, and Zak Bishop (therefore only finding one actual performer).  By changing the case of "**S**top" to "**s**top", the agent will look for the following actors:  Please Don't, Dacotah Red, and Zak Bishop, and return matched metadata/headshots for Dacotah and Zak.  

### Language Translation

All PGMA-Modernized Agents now provide optional language translation functionality.  Perhaps you're an English speaker and you'd prefer the Summary metadata for your libraries to be in English and not the native French from the index (e.g., https://www.gayeroticvideoindex.com/V/6/49506.html).  Conversely, you'd prefer to have Film and Scene summaries translated to your native German.  Perhaps you wish to duplicate and share one of your libraries with a friend who's native language is different than yours.  

When you create a new library or update an existing library, choose the language that you prefer the library's summaries to be translated to (if translation is necessary).  

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/language01.png)

When the agent matches the file, if the library language choice (in this Example, Dutch) is NOT the same as the website's default language (English for example, if using the AEBN agent), the agent will translate the summary to Dutch.  

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/language02.png)
 
You may optionally force an agent to check the source language before attempting to translate.  In the GEVI example above, by checking this setting the GEVI agent will translate the native French summary to your library's language, even though GEVI's default language is English.  

![](https://raw.githubusercontent.com/CodyBerenson/PGMA-Modernized/master/images/language01.jpg)

### Rationalizing Movies in a series, .com, etc.

If a title from an index site includes "Vol" or "Volume" or "Part", it is optional to include in the filename.  E.g.,  the film  "Raw! Vol. 5: Pounded" on Gay-world.org.  Valid filenames which will match include:

(CockyBoys) - Raw! 5 - Pounded (2019).mp4

or

(CockyBoys) - Raw! Vol. 5 - Pounded (2020).mp4 

Further, including 1 when the first part of a series is optional.  e.g., (Studio) - title 1 (2020) can be written as 
(Studio) - title (2020)

Re: .com, .org, .net, .co.xx internet names like men.com, including the .xxx is optional.  So instead of (men.com) - film title (2020) You can have (men) - film title (2020)

### Some final tips:  

1.  Consider using a couple Agents.  Can't find the film you're looking for on AEBN?  Try GEVI. Like the description or poster image better on HomoActive?  Use it.  Remember, that the same film may be on multiple sites, with each site using its specific version of the studio name or title.  Match your filename to the specific site you're wanting to match to. 

2.  The Agent will attempt to crop the scene poster for display in plex, using either an inline cropping service, or if unavailable a visual basic script (for Windows PMS installations).  If both fail, the agent will return the (often oversized) poster as-is from the blog site.  

3.  If you come across a site that indexes films or scenes and has plex style movie covers, it may be a good candidate for a new Agent.  Open an issue and make a request.  **Note: ** we will not create studio specific Agents...studios don't offer plex style movie covers and often update the framework of their site which breaks Agents.

4.  If you have any challenges or struggles, open a new issue.  Please describe your challenge as thoroughly as possible, including which agent you were targeting, the filename and include the log, if you can. **Note:** please, no screenshots that contain graphic content. 


### FAQ, Troubleshooting, and What to Do if you Require Assistance:

Q:  I'm new.  I've installed PMS.  I've downloaded all of the Agents and put into the Plex Plugins Directory.  I can't get it to work...I just can't get Plex to Match.  Help!

A:  Start small.  Before renaming every file in your system, start with one and work with it until you can get Plex to match it.  Trust us, you'll learn valuable insights from what didn't work that could cause a massive amount of rework if you've already renamed all your files.  If you still can't get it to work, we are happy to help!  Please follow the below steps:  

1.  Start small.

   a.  Create a new folder with the file you want to match against.  Find a match for this file on an index site, such as AEBN.com, gayeroticvideoindex.com, etc.  Name this file in the proper format (Studio) - Title (YYYY) ensuring this matches the studio, title, and date from the website.  

   b. Go into your PMS settings and choose only the film or scene agent whose website you just found the match to (i.e., AEBN, GEVI or WayBig.)  Unselect all others.  

   c. Stop your PMS.

   d. Go to  PMS Plugin Logs folder and delete all the deletable log files.  Not sure where they're located, click here:  https://support.plex.tv/articles/201106148-channel-log-files/
(e.g., in windows they are typically found in C:\Users\<Your User Name>
\AppData\Local\Plex Media Server\Logs\PMS Plugin Logs)

   e.  Restart your PMS.

2.  Create a new Plex library:  in the "add folders" step, point to the folder you just created; in the "advanced" step, choose the appropriate Agent i.e GayAdultFilms or GayAdultScenes that you had configured in 1b.  Click "Add Library" to complete the wizard.  Plex will create and scan the new library and attempt to match the file using the agent that you selected. Hopefully your match will be successful.  

3. If the match was unsucessful, please open an issue and include:

   a.  The specific operating system/device you have PMS installed on.

   b.  The logs--attach all the newly created logs from the \Logs\PMS Plugin Logs directories (see 1d). 

   c.  The specific url of the film or scene title on the Agent's index site.
   
   d.  Any information you deem pertinent, error messages you may have received, and any questions you may have

   e.  Please do not include adult-content images.

Q:  When choosing the agent in the library setup window, when it asks for scanner, which scanner option should I choose? Plex Movie Scanner, Plex Video Files, or Plex Video Files Scanner. I'm not sure which one works/works best with this.

A:  Choose Plex Movie Scanner. Then after choosing the plex movie scanner you have three options depending on your library's content:

    For video scenes - use gay adult scenes agent
    For full movies - use gay adult films
    For a mixture - use gay adult


Q:  When setting up the agents for Gay Adult, Gay Adult Scenes and Gay Adult Films the description mentions it utilizes different sources. Are those sources always used or do you need to also manually check the sources you want those agents to use?

A:  For any given set of agents, you choose which sources and the priority that it uses. Let's say that 90% of your content matches from AEBN; certainly choose AEBN and rank it first. 


Q:  I can't get any Scenes to Match on GEVI.  Please help.

A:  The GEVI Agent only scrapes films, not scenes.   Sorry.  


Q:  I can't get the WayBig Agent to match videos.  Help!

A:  The WayBig Agent won't scrape videos from WayBig.com, only Blog entries. If WayBig doesn't have the scene you're seeking, try Fagalicious or QueerClick.  Not on any of the three?  Try IAFD and upload your own poster.


Q:  I've figured out the setup and have successfully matched films and/or scenes.  BUT, I've tried everything, and I can't get a particular film/scene to match.  What now?

A:  Open a new Issue.  Please describe the challenge, include the URL for the film/scene, and the corresponding Agent's log file (i.e. if the film is on AEBN, please include the com.plexapp.agents.AEBN.log.) Unsure how to find the log?  This blog entry describes the log location for each PMS platform:  https://support.plex.tv/articles/200250417-plex-media-server-log-files/ The log will be in the PMS Plugin Logs subfolder.   **Please, do not upload graphic images**  Once a new issue is opened, we troubleshoot.  Most root causes turn out to be an incorectly named filename.  However, even though we have robustly tested the agents, we still find anomalies (e.g., special characters) that a particular index may infrequently use which necessitates an update to the logic in the Agent.  If the update is technically feasible, we'll likely make the fix and release the updated Agent.  Regardless of the root cause, you'll be able to track the progress of your issue (and look at any others you may find interesting).  


Q:  I've got a great idea for new functionality...or, there's an indexing site that I use all the time that you haven't provided an agent for.  What should I do?

A:  Open a new Issue.  We love to be challenged with creating new agents or making the current set of agents more robust.  However, we 1) won't create studio specific agents (e.g., SeanCody.com) or 2) likely won't create agents for sites that don't offer consistent quality posterart (IAFD being an obvious exception).  Our goal is to never, or nearly never, have to manually index content.  If you know a site, let us know.  We'll gratefully and happily see if it is feasibly scrapeable for Plex metadata.  


Q:  Does the code for the Agents ever change/get updated?

A:  Yes!  We are always developing new agents.  For existing agents, new functionality may be added (e.g., language translation support), or site updates to an index may break the Agent's ability to search.  It is a good practice to periodically check back and install the latest set of code.  Remember to stop and restart your Plex Media Server (PMS) in order for the new/updated Agents to take effect.  


Q:  Any best practices for backing up your Plex libraries and settings? I backup all my video files but wondering if there's another step I should do to make sure my metadata and album artwork is backed up in case of a drive failure. What do you guys do?

A:  There's a topic on the Plex Forum specifically about backing up (and restoring) the PMS libraries and settings: https://support.plex.tv/articles/201539237-backing-up-plex-media-server-data/

Since you're putting so much effort into building awesome libraries, you don't want to take any chances with losing them!


Q:  Why would I want to create separate libraries for movies and scenes?  Why would I want to comingle movies and scenes in one library?

A:  There are pros and cons to each approach. You may want to consider questions such as How many files do you have?  How well-organized is your content?  

Separate libraries:
1.  Pro:  A TimTales library is just that.  You don't have to further filter the library if all you want at that moment is your TimTales content.
2.  Con:  if you click on the actor it only returns matches for that particular library...you'll need to type in the name in the general search engine which will return all libraries;

Combined libaries:
1.  Pro:  One-stop shop.  All your indexed content in one location.
2.  Con:  a downfall of comingling, is that the larger the library grows, the longer Plex takes to scan. 


## Disclaimer


This project stores no images or metadata. All metadata is downloaded directly from publicly-available sources
