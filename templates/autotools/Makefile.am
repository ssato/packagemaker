#import os.path
EXTRA_DIST = MANIFEST MANIFEST.overrides
#if $conflicted_fileinfos
EXTRA_DIST += apply-overrides revert-overrides
#end if
#if $format == "rpm"
EXTRA_DIST += ${name}.spec rpm.mk

abs_srcdir  ?= .
include \$(abs_srcdir)/rpm.mk
#end if

#for $dd in $distdata
pkgdata${dd.id}dir = $dd.dir
dist_pkgdata${dd.id}_DATA = \\
#for $f in $dd.files
src$f \\
#end for
\$(NULL)

#end for

#for $fi in $fileinfos
#if $fi.type() == "symlink"
#set $dir = os.path.dirname($fi.target)
#set $bn = os.path.basename($fi.target)
install-data-hook::
\t\$(AM_V_at)test -d \$(DESTDIR)$dir || \$(MKDIR_P) \$(DESTDIR)$dir
\t\$(AM_V_at)cd \$(DESTDIR)$dir && \$(LN_S) $fi.linkto $bn

#else
#if $fi.type() == "dir"
install-data-hook::
\t\$(AM_V_at)test -d \$(DESTDIR)$fi.target || \$(MKDIR_P) \$(DESTDIR)$fi.target

#end if
#end if
#end for

MKDIR_P ?= mkdir -p
SED ?= sed
