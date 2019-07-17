# SeanCody.bundle

## Description

Plex metadata agent for fetching metadata for Sean Cody scenes.

This uses metadata and posters that are available from the site tour (free), so
the number of posters available is limited compared to the number of pictures
available in the paid side of the site.

By default, this matcher expects files to be named like:
* `sc{number} - {title}`, or
* `SeanCody - sc{number} - {title}`, or
* `Sean Cody - sc{number} - {title}`

Spaces around the dashes are optional, as is the sc before the number. This is
configurable in the agent settings. At least the clip number and name are
required as the free site URLs are constructed using this information.

By default, this matcher only runs on items in a directory named "Sean Cody".
This is configurable in the agent settings.

## Installation

Copy CockPorn.bundle and SeanCody.bundle to the Plex plugins path. See
[How do I find the Plug-Ins folder?][1] for more information.

## Known Issues

- Limited ability to match titles with special characters in the name.
- Unable to get metadata for bonus material from other sites.
- Autoupdate may cause issues as it may cause a full metadata refresh when a
new file is added.

[1]: https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-
