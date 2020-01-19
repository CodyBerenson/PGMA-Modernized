# AEBNii.bundle

Plex metadata agent for fetching metadata from AEBN and IAFD
20190816 - 	Adapted from previous AEBN Agent
			Actor thumbnails source from IAFD - as AEBN don't always show up correctly in plex
			Filenames must be named according to this format: (Studio) - Title (Year).ext
			If the title in AEBN has a hyphen "-" in its title place an em dash in the corresponding position in the Movie Title.
			Agent attempts to match according to the filename, and does not approximate or suggest matches
			if filename pattern is not met, the agent will abort matching.
			background art is set to the back cover of the dvd.
