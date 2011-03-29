#!/usr/bin/python

from distutils.core import setup, Extension
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.build_ext import build_ext
from distutils.dir_util import remove_tree
from distutils import log
import os, os.path
import glob
import platform
import time

try:
    import py2exe
except ImportError:
    py2exe = None

# now, setup the keyword arguments for setup
# (because we don't know until runtime if py2exe is available)
setup_kwargs = {}
setup_kwargs['ext_modules'] = []
setup_kwargs['cmdclass'] = {}

#
# metadata
#

setup_kwargs['name'] = 'minecraft-overviewer'
setup_kwargs['version'] = '0.0.0' # TODO useful version

#
# py2exe options
#

if py2exe is not None:
    setup_kwargs['console'] = ['overviewer.py']
    setup_kwargs['data_files'] = [('', ['COPYING.txt', 'README.rst'])]
    setup_kwargs['zipfile'] = None
    if platform.system() == 'Windows' and '64bit' in platform.architecture():
        b = 3
    else:
        b = 1
    setup_kwargs['options'] = {}
    setup_kwargs['options']['py2exe'] = {'bundle_files' : b, 'excludes': 'Tkinter'}

#
# script, package, and data
#

setup_kwargs['packages'] = ['overviewer_core']
setup_kwargs['scripts'] = ['overviewer.py']
setup_kwargs['package_data'] = {'overviewer_core':
                                    ['data/config.js',
                                     'data/textures/*',
                                     'data/web_assets/*']}


#
# c_overviewer extension
#

# Third-party modules - we depend on numpy for everything
import numpy
# Obtain the numpy include directory.  This logic works across numpy versions.
try:
    numpy_include = numpy.get_include()
except AttributeError:
    numpy_include = numpy.get_numpy_include()


c_overviewer_files = ['main.c', 'composite.c', 'iterate.c', 'endian.c']
c_overviewer_files += ['rendermodes.c', 'rendermode-normal.c', 'rendermode-lighting.c', 'rendermode-night.c', 'rendermode-spawn.c']
c_overviewer_includes = ['overviewer.h', 'rendermodes.h']

c_overviewer_files = map(lambda s: 'overviewer_core/src/'+s, c_overviewer_files)
c_overviewer_includes = map(lambda s: 'overviewer_core/src/'+s, c_overviewer_includes)

setup_kwargs['ext_modules'].append(Extension('overviewer_core.c_overviewer', c_overviewer_files, include_dirs=['.', numpy_include], depends=c_overviewer_includes, extra_link_args=[]))

# custom clean command to remove in-place extension
class CustomClean(clean):
    def run(self):
        # do the normal cleanup
        clean.run(self)
        
        # try to remove '_composite.{so,pyd,...}' extension,
        # regardless of the current system's extension name convention
        build_ext = self.get_finalized_command('build_ext')
        pretty_fname = build_ext.get_ext_filename('overviewer_core.c_overviewer')
        fname = pretty_fname
        if os.path.exists(fname):
            try:
                if not self.dry_run:
                    os.remove(fname)
                log.info("removing '%s'", pretty_fname)
            except OSError:
                log.warn("'%s' could not be cleaned -- permission denied",
                         pretty_fname)
        else:
            log.debug("'%s' does not exist -- can't clean it",
                      pretty_fname)

class CustomBuild(build_ext):
    def build_extensions(self):
        c = self.compiler.compiler_type
        if c == "msvc":
            # customize the build options for this compilier
            for e in self.extensions:
                e.extra_link_args.append("/MANIFEST")

        # build in place, and in the build/ tree
        self.inplace = False
        build_ext.build_extensions(self)
        self.inplace = True
        build_ext.build_extensions(self)
        

if py2exe  is not None:
# define a subclass of py2exe to build our version file on the fly
    class CustomPy2exe(py2exe.build_exe.py2exe):
        def run(self):
            try:
                import util
                f = open("overviewer_version.py", "w")
                f.write("VERSION=%r\n" % util.findGitVersion())
                f.write("BUILD_DATE=%r\n" % time.asctime())
                f.write("BUILD_PLATFORM=%r\n" % platform.processor())
                f.write("BUILD_OS=%r\n" % platform.platform())
                f.close()
                setup_kwargs['data_files'].append(('.', ['overviewer_version.py']))
            except:
                print "WARNING: failed to build overview_version file"
            py2exe.build_exe.py2exe.run(self)
    setup_kwargs['cmdclass']['py2exe'] = CustomPy2exe

setup_kwargs['cmdclass']['clean'] = CustomClean
setup_kwargs['cmdclass']['build_ext'] = CustomBuild
###

setup(**setup_kwargs)


print "\nBuild Complete"
