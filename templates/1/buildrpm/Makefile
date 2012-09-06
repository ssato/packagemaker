PACKAGE = #{name}
EXTRA_DIST = README pmaker-config.json
<?py if conflicts.files : ?>
EXTRA_DIST += apply-overrides revert-overrides trigger-overrides
<?py #endif ?>

# e.g. (cd ..; tar -cvf - foo-0.0.3 | xz -v9 > foo-0.0.3.tar.xz \
#         #           && mv foo-0.0.3.tar.xz foo-0.0.3/)

__name = #{name}-#{pversion}
__tar = tar -cvf
__tgz = $(__name).tar.#{compressor.ext}


dist: $(__tgz)
$(__tgz):
	cd .. && $(__tar) - $(__name) | #{compressor.cmd} -v9 > $(__tgz) && mv $(__tgz) $(__name)/


<?py if format == "rpm": ?>
EXTRA_DIST += #{name}.spec rpm.mk

abs_srcdir  ?= .
include $(abs_srcdir)/rpm.mk
<?py #endif ?>

MKDIR_P ?= mkdir -p
SED ?= sed


# vim:sw=4 ts=4 noet:
