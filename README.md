# How to Install

[Click Here](/images/PlexGayMetadataAgents-InstallationandUsageGuide.pdf)
for our new Installation and Usage Guide.  
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

## Disclaimer


This project stores no images or metadata. All metadata is downloaded directly from publicly-available sources
