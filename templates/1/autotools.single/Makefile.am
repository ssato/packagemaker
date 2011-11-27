EXTRA_DIST = MANIFEST MANIFEST.overrides
<?py if conflicts.files : ?>
EXTRA_DIST += apply-overrides revert-overrides
<?py #endif ?>
<?py if format == "rpm": ?>
EXTRA_DIST += #{name}.spec rpm.mk

abs_srcdir  ?= .
include $(abs_srcdir)/rpm.mk
<?py #endif ?>

<?py for dd in distdata: ?>
pkgdata#{dd.id}dir = #{dd.dir}
dist_pkgdata#{dd.id}_DATA = \
<?py    for f in dd.files: ?>
src#{f} \
<?py    #endfor ?>
$(NULL)

<?py #endfor ?>

<?py import os.path ?>
<?py for f in files: ?>
<?py    if f.type() == "symlink": ?>
<?py        sdir = os.path.dirname(f.install_path) ?>
<?py        bname = os.path.basename(f.install_path) ?>
install-data-hook::
	$(AM_V_at)test -d $(DESTDIR)#{sdir} || $(MKDIR_P) $(DESTDIR)#{sdir}
	$(AM_V_at)cd $(DESTDIR)#{sdir} && $(LN_S) #{f.linkto} #{bname}

<?py    elif f.type() == "dir": ?>
install-data-hook::
	$(AM_V_at)test -d $(DESTDIR)#{f.install_path} || $(MKDIR_P) $(DESTDIR)#{f.install_path}

<?py    #endif ?>
<?py #endfor ?>

MKDIR_P ?= mkdir -p
SED ?= sed

# vim:sw=4 ts=4 et:
