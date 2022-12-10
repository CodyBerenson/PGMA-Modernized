# AEBN.bundle

Plex metadata agent for fetching metadata from AEBN and IAFD
20200521 - 	Actor thumbnails source from IAFD - as AEBN thumbnails don't always show up correctly in plex
			Filenames must be named according to this format: (Studio) - Title (Year).ext
			If the title in AEBN has a colon its title place replace with the sequence " - "
			Agent attempts to match according to the filename, and does not approximate or suggest matches
			if filename pattern is not met, the agent will abort matching.
			background art is set to the back cover of the dvd.
20221204 - 	Renamed to AEBN