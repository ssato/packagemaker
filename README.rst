About
=======

PackageMaker is a kind of archiver like tar and zip but generates packages
instead of just an archive file.

Packaging process is fully automated and you can package files, dirs and
symlinks by just passing paths list and package information to PackageMaker.

It helps building packages of existing files on your system by automating
almost all of the steps needed for packaing: arrange source tree, create
makefiles and rpm specs or debian packaging files, etc.

Basic Usage
=============

See the output of `pmaker --help` (or run 'PYTHONPATH=. python tools/pmaker -h'
in this dir) or pmaker(8) or examples/\*.log.

How it works
==============

When packaging files, dirs and symlinks which user gave in the path list,
PackageMaker will try gathering the information of these targets  and then:

#. arrange src tree contains these files, dirs and symlinks with these
   relative path kept, and build files (Makefile.am, configure.ac, etc.)
   to install these.

#. generate packaging metadata like RPM SPEC, debian/rules, etc.
#. build package such as rpm, src.rpm, deb, etc.

.. note::
   The permissions of the files might be lost during packaging process. If you
   want to ensure these are saved or force set permissions as you wanted,
   specify these explicitly in Makefile.am or rpm spec, etc.

"Package-based system construction" - the concept behind packagemaker
=======================================================================

Usually, systems are constructed through the following steps:

#. kitting: setup hardware
#. install os
#. configure os
#. install middleware and apps
#. configure middleware and apps

It is possible to automate some of steps 2..4, above but it takes much time and
hard sometime because most steps consist of procedual steps with side effects.

With help of onfiguration management technology such like puppet, chef and
ansible or deployment tools like cappistrano, it may be possible to automate
such build steps, but, important point is that procedual steps is not required
in actual, that is, any procedual and effectful steps make some files, dirs and
symlinks in the last. In other words, what we have to take care to construct
systems is just what files, dirs and symlinks are needed and where these are.

It should be easy to manage and helps making these processes less procedual and
more functional a lot if all we have to consider is what files we have to take
care and where these should be. For example, if all of the changes
(file/dir/symlink additions and modifications) after the step 2 could be
packaged into some RPMs, we can re-play these steps with a kickstart file with
basic os installatio and package list which these additional RPMs are added.

PackageMaker is one of the important pieces to actualize and establish "package
based system construction" [#]_ methodology because it should enable reducing
the cost of packaging files, dirs and sysmlinks (captureing what objects making
that system), and may enables 're-playing' the system construction process.

.. [#] Although container based system construction and deployment technologies like docker becomes familiar these days, you have to write 'yum install ...' in docker files still. That is, docker can hide some of the steps but the essential problems do not go away by docker.

Comparison with configuration management system
-------------------------------------------------

Some configuration management systems such like puppet, chef and ansible also
can accomplish the same goal packagemaker focusing but these add some more
extra software layers to os-native software management systems. Puppet may
conflict with and overrides package management system for example.

Say, if you're using puppet to just deploy files I think you should package
these files and let package management system process them.

Packages built with packagemaker do not need any runtime system or libraries
and should be able to work well with os-native package management systems in
standalone mode.

Architecture
==============

Simply put, PackageMaker can be divided into four components:

a. Models
b. Collectors
c. Backends
d. Utility modules

a. Models
-----------

Classes in pmaker.models.FileObjects module implement the basic model of target
objects: files, dirs and symlinks.  Because a lot of instance of these objects
need to be created as user requested, operations (copy, move, etc.) for these
models are implemented in functions in another module,
pmaker.models.FileObjectOperations.

Model classes are instantiated from dedicated factory functions in
pmaker.models.FileObjectFactory and never instantiated directly.

The code of models are placed in pmaker/models directory.

b. Collectors
---------------

This component process user input (files list) and to create a collection of
FIleObject instances to package later.

The code of collectors are placed in pmaker/collectors directory.

c. Backends (Drivers)
-----------------------

The modules under pmaker/backend is the core componenet to manage and drive
packaging process.

All backend classes inherit pmaker.backend.base.Base class and may override
methods {setup, preconfigure, configure, sbuild, build} to implement each
actual build steps.

d. Utility modules
-------------------

Most of python code in module's top directory (pmaker/\*.py) are utility
modules.

How to build
==============

Build w/ mock
----------------

Although it takes some time to make a rpm, it should be better and I recommend
this way:

#. python setup.py srpm
#. mock -r <target_build_dist> dist/SRPMS/packagemaker-*.src.rpm

Build w/o mock
----------------

It's easier than the above but only possible to make a rpm for build host. Just
run::

  python setup.py rpm

How to test
=============

* Unit tests: `python setup.py test`
* Unit tests + System tests: `python setup.py test --full`

If you want to test specific python code:

#. source code: ./runtest.sh <path_to_python_source>
#. a class in source code: ./runtest.sh <path_to_python_source>:<class_name>
#. a method of a class in source code:./runtest.sh <path_to_python_source>:<class_name>.<method_name>

SEE ALSO: nosetests(1)

Here are some examples:

::

  $ ./runtest.sh pmaker/tests/rpmutils.py
  FIXME: Implement tests for this function ... ok
  test_info_by_path (pmaker.tests.rpmutils.TestFunctions) ... ok
  test_rpm_attr (pmaker.tests.rpmutils.TestFunctions) ... ok
  test_rpm_search_provides_by_path (pmaker.tests.rpmutils.TestFunctions) ... ok
  test_rpmh2nvrae (pmaker.tests.rpmutils.TestFunctions) ... ok
  test_rpmh2nvrae__no_rpmdb (pmaker.tests.rpmutils.TestFunctions) ... ok
  FIXME: Implement tests for this function ... ok
  FIXME: Implement tests for this function ... ok

  ----------------------------------------------------------------------
  Ran 8 tests in 0.517s

  OK
  $ ./runtest.sh pmaker/models/tests/FileInfo.py:TestFileInfo
  test__init__ (pmaker.models.tests.FileInfo.TestFileInfo) ... ok

  ----------------------------------------------------------------------
  Ran 1 test in 0.019s

  OK
  $ ./runtest.sh tests/07_multi_files_filelist_json.py:Test_00_multi_files_filelist_json.test_01_system_files__tgz
  test_01_system_files__tgz (tests.07_multi_files_filelist_json.Test_00_multi_files_filelist_json) ... configure.ac:2: installing `./install-sh'
  configure.ac:2: installing `./missing'
  ok

  ----------------------------------------------------------------------
  Ran 1 test in 21.479s

  OK
  $

HACKING
==========

This is my usual way for enhancements:

#. create a branch: git branch foo
#. modify or add code to archive objective enhancements in that branch: git checkout foo; vim ...
#. add (unit) tests for enhancements to verify the correctness of changes
#. commit and run full test (unit + system tests)

if all looks ok, merge the branch to main.

And here is my usual way for bug fixes:

#. Write tests for the bug
#. Modify / add code for the fix
#. Run the tests and confirm if the fix was right

TODO
=======

* resolve package name collisions due to overriding packages; there is
  'man-pages-overrides' package exist. How about using '-overlay' suffix
  instead of '-overrides' ?
* correct wrong English expressions
* define schema for input (JSON, YAML?, XML?, ...)

  * perhaps, the contents of files will be gotten from external site pointed by
    URL reference in JSON data

* more complete tests
* eliminate the strong dependency to rpm and make it runnable on debian based
  systems (w/o rpm-python)
* find causes of warnings during deb build and fix them all
* plugin system: posponed
* keep permissions of targets in tar archives

Finished TODO items
---------------------

* refactor its architecture: Done

  * make collector (generator) and packagemaker classes loosely-coupled: Done
  * separate packaging strategy (PackageMaker._scheme) and packaging format
    (PackageMaker._format): Done

* sort out command line options: Done
* Run w/o python-cheetah: Done (now it uses pytenjin instead)

References
============

In random order:

* http://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-creating-rpms.html
* http://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html
* http://cdbs-doc.duckcorp.org
* https://wiki.duckcorp.org/DebianPackagingTutorial/CDBS
* http://kitenet.net/~joey/talks/debhelper/debhelper-slides.pdf
* http://wiki.debian.org/IntroDebianPackaging
* http://www.debian.org/doc/maint-guide/ch-dother.ja.html

Alternatives
==============

Basic idea and implementation design of PackageMaker was arised from offhand
talk with my very talented co-worker, Masatake Yamato (yamato at redhat.com).

Around the same time I started working on PackageMaker, Magnus-san developed
buildrpm and I was very impressed with it. Implementation was completely
different but PackageMaker and buildrpm do the same thing basically.

I believe PackageMaker is useful and helps you but if you want features
PackageMaker lacks or will not have or you don't like it, take a look at
buildrpm:

* buildrpm: http://magnusg.fedorapeople.org/buildrpm/

And I recently found fpm which looks powerful and feature rich meta packaging
tool written in ruby:

* https://github.com/jordansissel/fpm

License
=========

* Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
* Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
* Copyright (C) 2011 - 2013 Red Hat, Inc.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.

Exceptions
------------

Files under pmaker/imported/ were imported from external projects and the above
license is not applied. 

Author
=======

Satoru SATOH <ssato at redhat.com>

.. vim:sw=2:ts=2:et:
