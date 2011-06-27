#raw
abs_builddir    ?= $(shell pwd)

rpmdir = $(abs_builddir)/rpm
rpmdirs = $(addprefix $(rpmdir)/,RPMS BUILD BUILDROOT)

rpmbuild = rpmbuild \
--quiet \
--define "_topdir $(rpmdir)" \
--define "_srcrpmdir $(abs_builddir)" \
--define "_sourcedir $(abs_builddir)" \
--define "_buildroot $(rpmdir)/BUILDROOT" \
$(NULL)

$(rpmdirs):
\t$(AM_V_at)$(MKDIR_P) $@

rpm srpm: $(PACKAGE).spec dist $(rpmdirs)

rpm:
\t$(AM_V_GEN)$(rpmbuild) -bb $<
\t$(AM_V_at)mv $(rpmdir)/RPMS/*/*.rpm $(abs_builddir)

srpm:
\t$(AM_V_GEN)$(rpmbuild) -bs $<

.PHONY: rpm srpm
#end raw
