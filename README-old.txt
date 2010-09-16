Terminology
-----------

Relative paths are relative to the buildout directory, except noted otherwise.

*Local* refers to something in the buildout directory.

We use bdist/egg and sdist/src synonymously (at least as long as we are solely
working with eggs and buildout).


Custom copy of egg
==================

Normally eggs are either in ``eggs/`` directory or a buildout cache. Either
way, in order to make changes to an egg (e.g. to set a breakpoint), a copy of
the egg is made in ``eggs-customized/``. In case of a buildout cache this is
necessary not to interfere with other buildouts, otherwise it is convenient to
keep eggs with changes apart from eggs without.

The custom copy is initialized as a local git repository not connected to any
external repo, in order to keep track of changes and to create patches. Feel
free to implement support for alternatives to git, ideally by branching on
github.

    % ./bin/mrsd customize <eggname>
    --> mkdir -p eggs-customized
    --> 
    Created custi

    % ./bin/mrsd customize <eggname>

After creating a copy of the egg, you are dropped into the newly created egg
directory to customize the egg.

View changes made to already tracked files:

    % git diff
    % git d
    % git diff --color-words
    % git dw

Add a newly created file:

    % git add <file_name>

XXX

Switching back and forth
~~~~~~~~~~~~~~~~~~~~~~~~

You can switch back and forth between your customized egg and the stock egg.

    % ./bin/mrsd toggle <eggname>

    % ./bin/mrsd toggle <eggname>

    % ./bin/mrsd stock <eggname>

    % ./bin/mrsd stock <eggname>

    % ./bin/mrsd customize <eggname>
    WARNING

Discarding customized eggs
~~~~~~~~~~~~~~~~~~~~~~~~~~



XXX: Do we want to support the following 

    % ./bin/mrsd discard <eggname>


Generating patches
------------------

The customized eggs in ``eggs-customized/`` are not meant to be under revision
control as it would limit you the  is
In order to make changes persistent


Limitations
===========

mrs.developer was only tested on linux so far. Please report back
success/failure on other systems. 

Behind the Scenes
=================





Random Notes
============

- rerunning buildout is necessary, iff:
  - version of egg changed
  - requires (normal or test) are changed
  - autoinclude feature is changed

- In non-develop eggs its only possible to change code, the EGG_INFO dir stays
  untouched

- customization of eggs is solved by running a script after all recipes are
  finished and therefore all bin/ scripts are created.
