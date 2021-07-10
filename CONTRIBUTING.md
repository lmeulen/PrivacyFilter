# Contributing
Thanks for your interest in the project! 

If you find a bug or want to propose a new feature open an issue. If you have written some code that should be merged open a pull request describing your changes 
and why it should be merged. If you have a question or want to discuss something, feel free to contact any of the contributors.

## Git branching model

The branching model is based on the branching model described in the post [A successful Git branching model](http://nvie.com/posts/a-successful-git-branching-model/). 

### The main branches

The central repository holds three types of branches:

* master 
* development
* feature branches

#### The master branch 
We consider _origin/master_ to be the main branch where the source code of HEAD always reflects a production-ready state.

* safe to merge into the development
* contains only reviewed code

#### The development branch
The development branch serves as a working branch where new features can be collected and tested before they are merged into the master.

* contains finished changes 
* successfull unit tests


#### Merging strategy and feature branches
Feature branches are used to develop and integrate new code and integrate into the development branch. 

Feature branches should be used for a single change and should ideally correspond to a single issue.
~~Once the code on the branch is ready for review, a pull request into development should be opened.~~

**Feature branches**

* correspond to a single issue
* merged into development upon succesfull unit tests
* ~~merged into developmentthrough a pull request~~

**Pull request**

If needed, a pull request can be created.
In order for the pull request to be merged, the following conditions must be met:

* unittests passed
* ~~a positive review is required~~
* follows the PEP8 style guide 
* has tests for the code

Tests are run automatically.
