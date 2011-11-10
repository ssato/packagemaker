AC_INIT([#{name}],[#{version}])
AM_INIT_AUTOMAKE([#{compressor.am_opt} foreign subdir-objects tar-pax])

dnl http://www.flameeyes.eu/autotools-mythbuster/automake/silent.html
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])

dnl TODO: fix autoconf macros used.
AC_PROG_LN_S
m4_ifdef([AC_PROG_MKDIR_P],[AC_PROG_MKDIR_P],[AC_SUBST([MKDIR_P],[mkdir -p])])
m4_ifdef([AC_PROG_SED],[AC_PROG_SED],[AC_SUBST([SED],[sed])])

dnl TODO: Is it better to generate #{name}.spec from #{name}.spec.in ?
AC_CONFIG_FILES([
Makefile
])

AC_OUTPUT
