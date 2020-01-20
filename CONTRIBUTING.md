# Contributing

So, you want to help the project out. That's great but there is a certain way to make sure that your changes are accepted by the maintainers.

## Prerequisites

You will need a Git client, I recommend [Github Desktop](https://desktop.github.com), and you will need a text editor. I strongly recommend [Visual Studio Code](https://code.visualstudio.com), as it supports syntax highlighting and it helps troubleshoot Git problems.

## Overview

Let's start by defining a few terms specific to Git.


> **Git** is a version control system (VCS.) This allows anyone to make changes to and view all previous changes of a project. This makes for easy troubleshooting.
### 

> A **Repository** is a Git project. This whole project is one repository, even though there are many folders.

> **Forking** a repository is when you *make an identical copy* of a repository. **THIS INCLUDES THE MASTER BRANCH**. However, this does not sync your changes with the *upstream repository* (aka this repo.) You can set this up in Github Desktop by following this guide.

> **Cloning** a repository is when you make a local copy of either your or someone elses repository. If you intend to submit changes to this repository, you must **fork**, clone **the fork**, and sync with the upstream

## Getting Started

Fork this repository by logging into your GitHub account. Then, click the fork button.
![](2020-01-20-12-57-28.png)

Wait, and you will be brought to your own copy of this repository. Open Github Desktop and sign-in if required.

![](2020-01-20-13-00-27.png)

You will be brought to the main page of Github Desktop. Click your fork in the list of your repositories. Click 'clone'

## Syncing Your Fork
This next section describes how to keep your fork's master branch synced with the master branch of the 'upstream repository.' This eliminates incompatibilities and makes merging pull requests 100x easier.

![](2020-01-20-13-04-30.png)

First, be sure that the current branch is set to *master*,**not upstream/master or dev, etc.** Next, press the fetch origin button. Then click the *current branch* button.

![](2020-01-20-13-07-40.png)

Select the *choose a branch to merge into master* button at the bottom. Select *upstream/master* and select **Merge** if Git detects that your fork is out of date.  

You will need to do this every time there is a new commit to the *upstream* master branch

Do not create branches in your own fork unless you know what you are doing. It is complicated, just don't do it.

## Making Changes

If you have VS Code as your editor, simpily push the **Open in Visual Studio Code** button.

- code
- drink coffee
- code more
- test code

**You do not have to do these steps for every small change, please only make commits if the code works, or else you are wasting your own time**

When you are ready to push your changes, save your files and go back to Github Desktop.

![](2020-01-20-13-13-56.png)

The left hand sidebar will show that you have modifed the repository. Make sure the changes you want are selected, add a summary, and click **Commit to master**

![](2020-01-20-13-17-16.png)

You have just made changes to your *local repository*. To push these changes to your online GitHub Fork, press the **Push Origin** button.

You just edited a Git repostory! It's a horrible process, I know, but it makes tracking changes and bugs *so much easier*

## Pull Requests
**You do not have to create a pull request for every small change you make. Please only make pull requests if you have created a new agent, or have made large changes**

Now, to see your changes go live in this *upstream repository*, you can submit a **Pull Request**

Go to the [repository homepage](https://github.com/acvigue/pgma) and click Pull Requests.

![](2020-01-20-13-20-07.png)

Click **new pull request**

![](2020-01-20-13-21-01.png)

Click **compare across forks** This will allow you to select the changes you have committed to your forked copy.

![](2020-01-20-13-21-48.png)

Change **head repository** to your forked copy. Make sure the changes are what you expected, and click **create pull request**

**Please keep allow edits by maintainers on, this will allow the project maintainers to test your code before pushing it to the main branch**

Give your pull request a descriptive name.

**Click create pull request again and wait for the maintainer to merge your pull request**