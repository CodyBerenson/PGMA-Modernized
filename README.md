<h1>plex-gay-metadata-agent</h1>
<h1>Overview</h1>
A Plex agent for fetching gay adult video metadata. https://forums.plex.tv/discussion/32922/adult-agents-for-gay-titles

<h1>Versioning</h1>
Calendar Versioning is used for this software. YYYY.0M.0D.micro Zero-padded month and day. Note that if there are multiple updates within the same day micro versions are used, these are patches.

Example 2019.01.05.0 - meaning January 5th, 2019 with 0 patches for the software for that day.

<h1>How to install</h1>
1. Copy the Cockporn.bundle and any required site specific agents into the Plex Server plug-ins directory<br />
	<b>Mac:</b> ~/Library/Application Support/Plex Media Server/Plug-ins/<br />
	<b>QNAP:</b> /root/Library/Plex\ Media\ Server/Plug-ins/<br />
	<b>Windows:</b> %LOCALAPPDATA%\Plex Media Server\Plug-ins\ <br />
	<b>Raspberry Pi:</b> /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins<br />
2. Login to the web interface and open settings.<br />
3. In Settings > Server > Agents select "Gay Adult" and check all required agents.<br />
4. In Settings > Server > Agents move AEBN to second to last and Local Media Assets (Movies) to last.<br />
6. Create a new library or change the agent of an existing library to the "Gay Adult" agent, then refresh all metadata.

<h1>Wiki</h1>
More documentation can be found in the <a href="https://github.com/iklier/plex-gay-metadata-agent/wiki">wiki</a>.<br />
https://github.com/iklier/plex-gay-metadata-agent/wiki

Use https://regex101.com/ for setting regular expressions for file names and folders.

NONE OF THE FILENAMES FOR THE ADGENTS BELOW ARE CASE SENSITIVE.

<h1>AEBN.bundle</h1>
	NAMING CONVENTION:
		Enclosing directory: Any
		Video Naming: Text of the title as displayed on AEBN website. You can even have scenes for movies.

		If multiple titles from different studios follow exact format below must have ().
			(Studio name) - title.extention
		Else you can just use.
			tite.extention

		If it is a scene include the word scene in the filename.
			title scene 1
	KNOWN ISSUES
	- Autoupdate may cause issues as it may cause a full metadata refresh when a new file is added.

<h1>Freshmen.bundle</h1>
	NAMING CONVENTION:
		Enclosing directory: Can be defined in settings
		Video Naming: <scene number>.mp4
	
	KNOWN ISSUES:
	- Description fetching fails on certain scenes.
		

<h1>GayPornCollector.bundle</h1>
	NAMING CONVENTION:
		The title must be in the folder of the studio the title is for.
		e.g. Location Path/Studio name/title.extention

<h1>HelixStudios.bundle</h1>
	NAMING CONVENTION:
		Enclosing directory: Can be defined in settings<br>
		Video Naming: Text title as displayed on Helix Studios website.<br>
		DVD Naming: HXM123.extension where 123 is the DVD's ID<br>
		Scene Naming: If the Video Naming above gives no matches, name your scenes like 1234.extension where 1234 is the scene's ID
		

	KNOWN ISSUES
	- Limited ability to match titles with special characters in the name.
	- Unable to get metadata for bonus material from other sites.
	- Autoupdate may cause issues as it may cause a full metadata refresh when a new file is added.

<h1>RawFuckClub.bundle</h1>
	NAMING CONVENTION:
		Enclosing directory: Can be defined in settings, but "Raw Fuck Club" is recommended
		Video Naming:
		- `{title}`
		The scene name exactly as it appears on rawfuckclub.com are required for the best matching results.

	KNOWN ISSUES:
	- None at this time

	By default, this matcher only runs on items in a directory named "Raw Fuck Club". This is configurable in the agent settings.

<h1>SeanCody.bundle</h1>
	NAMING CONVENTION:
		Enclosing directory: Can be defined in settings
		Video Naming:
		- `sc{number} - {title}`, or
		- `SeanCody - sc{number} - {title}`, or
		- `Sean Cody - sc{number} - {title}`
		Spaces around the dashes are optional, as is the sc before the number. This is configurable in the agent settings. At least the clip number and name are required as the free site URLs are constructed using this information.

	KNOWN ISSUES
	- Limited ability to match titles with special characters in the name.
	- Unable to get metadata for bonus material from other sites.
	- Autoupdate may cause issues as it may cause a full metadata refresh when a new file is added.

	By default, this matcher only runs on items in a directory named "Sean Cody". This is configurable in the agent settings.

<h1>Staxus.bundle</h1>
	NAMING CONVENTION:
		Enclosing directory: Can be defined in settings
		Video Naming: Partial title or text of the title as displayed on Staxus website.

	KNOWN ISSUES
	- Unable to get metadata for bonus material from other sites.
	- Autoupdate may cause issues as it may cause a full metadata refresh when a new file is added.

<h1>NOTES</h1>
All metadata is downloaded by the end users personal Plex Media Server instance and no metadata is embedded in the agent bundle itself.
