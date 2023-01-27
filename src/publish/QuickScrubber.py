
import sys
import getopt
import os
import shutil
import string
import py_compile
import time
import re
import platform

from direct.dist import FreezeTool

helpString ="""
Usage:
  python Scrubber [opts] command installDirectory persistDirectory

Options:

  -h   Display this help

  -f filelist
       Specify pathname of filelist file.

  -p platform
       Should be WIN32 or OSX.

Example:
python Scrubber scrub J:/ C:/toontown-persist/

Generates multifiles suitable for publishing
Creates a persist directory

Required:
  command
      The action to perform.  This is either 'scrub' to update the
      contents of the persistDirectory and build launcherFileDb,
      'wise' to build patches against InstallLauncher.exe and build
      launcherFileDb.ddb, or 'copy' to copy from the persistDirectory
      to the installDirectory, compressing as it goes.

  installDirectory
      The full path to a temporary directory to copy the
      ready-to-be-published files into.

  persistDirectory
      The full path to a directory that retains persistant state
      between publishes.
"""

#
# filelist syntax:
#
#   multifile <mfname>
#
#     Begins a new multifile.  All files named after this line and
#     until the next multifile line will be a part of this multifile.
#
#     <mfname>
#       The filename of the multifile, no directory.
#
#
#   file <filename> <dirname> <platforms>
#
#     Adds a single file to the current multifile.
#
#     <filename>
#       The name of the file to add.  This is the full path to the
#       file on the publishing machine at the time this script is run.
#
#     <dirname>
#       The directory in which to install the file, on the client.
#       This should be a relative pathname from the game directory.
#       The file is written to the multifile with its directory part
#       taken from this, and its basename taken from the source
#       filename, above.  Also, if the file is extracted, it will be
#       written into this directory on the client machine.
#
#       The directory name "toplevel" is treated as a special case;
#       this maps to the game directory itself, and is used for files
#       in the initial download.
#
#     <platforms>
#       A comma-delimited list of platforms for which this file should
#       be included with the distribution.  Presently, the only
#       options are WIN32 and/or OSX.
#
#
#   dir <localDirname> <dirname>
#
#     Adds an entire directory tree to the current multifile.  The
#     named directory is searched recursively and all files found are
#     added to the current multifile, as if they were listed one a
#     time with a file command.
#
#     <localDirname>
#       The name of the local directory to scan on the publishing
#       machine.
#
#     <dirname>
#       The name of the corresponding local directory on the client
#       machine; similar to <dirname> in the file command, above.
#
#
#   module modulename
#
#     Adds the named Python module to the exe or dll archive.  All files
#     named by module, until the next freeze_exe or freeze_dll command (below),
#     will be compiled and placed into the same archive.
#
#   exclude_module modulename
#
#     Excludes the named Python module from the archive.  This module
#     will not be included in the archive, but an import command may
#     still find it if a .py file exists on disk.
#
#   forbid_module modulename
#
#     Excludes the named Python module from the archive.  This module
#     will specifically never be imported by the resulting executable,
#     even if a .py file exists on disk.  (However, a module command
#     appearing in a later phase--e.g. Phase3.pyd--can override an
#     earlier forbid_module command.)
#
#   dc_module file.dc
#
#     Adds the modules imported by the indicated dc file to the
#     archive.  Normally this is not necessary if the file.dc is
#     explicitly included in the filelist; but this command may be
#     useful if the file.dc is imported in a later phase.
#
#   freeze_exe <exeFilename> <mainModule> <dirname>
#
#     <exeFilename>
#       The name of the executable file to generate.  Do not include
#       an extension name; on Windows, the default extension is .exe;
#       on OSX there is no extension.
#
#     <mainModule>
#       The name of the python module that will be invoked first (like
#       main()) when the resulting executable is started.
#
#     <dirname>
#       (Same as for the file command, above.)
#
#   freeze_dll <dllFilename> <dirname>
#
#
#     <dllFilename>
#       The name of the shared library file to generate.  Do not include
#       an extension name; on Windows, the default extension is .pyd;
#       on OSX the extension is .so.
#
#     <dirname>
#       (Same as for the file command, above.)

filelistPath = '$TF/src/publish/QuickFilelist'
installDirectory = None
persistDirectory = None

#
# This is the list of filename extensions for files that will be be
# stored in a compressed form within the multifiles.  These files will
# remain compressed within their multifiles and will thus be stored
# compressed on the client's machine, and transparently decompressed
# on-the-fly at runtime when they are accessed out of the multifile.
#
# There's no real advantage for doing this in terms of improving
# download time, since we already compress the whole multifile for
# download.  Load-time performance doesn't seem to be much affected
# one way or the other (on the one hand, now we have pay extra CPU to
# decompress the file at load time; on the other hand, since the
# actual file stored on disk is smaller, there is less I/O overhead).
#
# The real reason we do this is to provide a tiny bit more
# obfuscation: since these are text files, their contents would be
# immediately apparent if the user did a 'strings' command on the
# multifile.  Compressing them incidentally makes them binary and
# therefore difficult to read.  Of course, this is mere obfuscation,
# not real security.
#

compressExtensions = ['ptf', 'dna', 'txt', 'dc', 'wav']
compressFiles = []

try:
    opts, pargs = getopt.getopt(sys.argv[1:], 'hRf:p:m:')
except Exception as e:
    # User passed in a bad option, print the error and the help, then exit
    print(e)
    print(helpString)
    sys.exit(1)

internalPlatform = platform.system()
if internalPlatform == 'Windows':
    platform = 'WIN32'
elif internalPlatform == 'Linux':
    platform = 'LINUX'
elif internalPlatform == 'Darwin':
    platform = 'OSX'

for opt in opts:
    flag, value = opt
    if (flag == '-h'):
        print(helpString)
        sys.exit(1)
    elif (flag == '-f'):
        filelistPath = value
    elif (flag == '-p'):
        platform = value
    else:
        print('illegal option: ' + flag)
        sys.exit(1)

if (not (len(pargs) == 3)):
    print('Must specify a command, an installDirectory, and a persistDirectory')
    sys.exit(1)
else:
    command = pargs[0]
    installDirectory = pargs[1]
    persistDirectory = pargs[2]

print("Platform:", platform)

from direct.directnotify.DirectNotifyGlobal import *
from panda3d.core import *
from panda3d.direct import *

# Now that we have PandaModules, make Filename objects for our
# parameters.
filelistPath = Filename.expandFrom(filelistPath)
installDirectory = Filename.fromOsSpecific(installDirectory)
persistDirectory = Filename.fromOsSpecific(persistDirectory)

class Scrubber:
    def __init__(self):

        # create a DirectNotify category for the Launcher
        self.notify = directNotify.newCategory("Scrubber")

        self.persistDir = persistDirectory

        # The multifiles and patches live in a subdirectory called content
        self.installDir = installDirectory
        #self.contentDir = Filename(self.installDir, Filename('content/'))
        #self.contentDir.makeDir()

        if command == 'scrub':
            self.doScrubCommand()

        elif command == 'copy':
            self.doCopyCommand()

        else:
            print("Invalid command: %s" % (command))
            sys.exit(1)

    def flushIO(self):
        sys.stdout.flush()      # MAKE python flush I/O for more interactive response

    def doCopyCommand(self):
        # Get all the multifiles in the persist dir.
        import glob
        mfPattern = self.persistDir / '*.mf'
        mfiles = glob.glob(mfPattern.toOsSpecific(), recursive=False)

        for mfile in mfiles:
            # Copy the mfile to the install dir.
            # If it's the toplevel multifile, extract it into the install dir,
            # rather than copying.
            mFilename = Filename.fromOsSpecific(mfile)
            if mFilename.getBasenameWoExtension() == 'toplevel':
                self.notify.info("Extracting toplevel into install dir")
                os.chdir(self.installDir.toOsSpecific())
                m = Multifile()
                m.openRead(mFilename)
                count = m.getNumSubfiles()
                for i in range(count):
                    subfileName = Filename(m.getSubfileName(i))
                    m.extractSubfile(i, subfileName)
                m.close()
            else:
                self.copyFile(mFilename, self.installDir / mFilename.getBasename())

    def doScrubCommand(self):

        # The launcher phase writes out the launcherFileDb
        # The launcher phase is special because the ActiveX does the hash checks
        # To do the hash checks it reads in a special file called launcherFileDb
        self.launcherPhase = 1

        # The filelist is a developer maintained text file listing all the files
        # to publish, in each phase.
        self.notify.info('init: Reading filelist: ' + filelistPath.cStr())
        self.filelist = open(filelistPath.toOsSpecific())
        self.lines = self.filelist.readlines()
        self.filelist.close()

        # Initialize some placeholder variables
        self.currentMfname = None
        self.currentMfile = None
        self.lineNum = -1

        # This records the current list of modules we have added so
        # far.
        self.freezer = FreezeTool.Freezer()
        self.freezer.linkExtensionModules = True
        self.freezer.keepTemporaryFiles = False

        # The persist dir is the directory in which the results from
        # past publishes are stored so we can generate patches against
        # them.  If it is empty when we begin, we will generate a
        # brand new publish with no previous patches.
        self.persistDir.makeDir()

        # Within the persist dir, we make a temporary holding dir for
        # generating multifiles.
        self.mfTempDir = Filename(self.persistDir, Filename('mftemp/'))
        self.mfTempDir.makeDir()

        # We also need a temporary holding dir for squeezing py files.
        self.pyzTempDir = Filename(self.persistDir, Filename('pyz/'))
        self.pyzTempDir.makeDir()

        # Change to the persist directory so the temp files will be
        # created there
        os.chdir(self.persistDir.toOsSpecific())

        self.notify.info('init: persist dir: ' + self.persistDir.cStr())

        # Now start parsing the filelist lines
        self.lineList = self.getNextLine()
        while self.lineList:
            # If we get to a new multifile, we know we are done with the previous one
            # close it and make a new one
            if self.lineList[0] == 'multifile':
                if self.currentMfname:
                    self.closePreviousMfile()
                # Make a new file
                self.parseMfile()

            # Add a Python file to the executable
            elif self.lineList[0] == 'module':
                self.parseModule(self.lineList)

            elif self.lineList[0] == 'exclude_module':
                self.parseExcludeModule(self.lineList, forbid = False)

            elif self.lineList[0] == 'forbid_module':
                self.parseExcludeModule(self.lineList, forbid = True)

            elif self.lineList[0] == 'dc_module':
                self.parseDCModule(self.lineList)

            # Add a file to the current multifile
            elif self.lineList[0] == 'freeze_exe':
                self.freezeExe(self.lineList)

            # Add a file to the current multifile
            elif self.lineList[0] == 'freeze_dll':
                self.freezeDll(self.lineList)

            # Add a file to the current multifile
            elif self.lineList[0] == 'file':
                self.parseFile(self.lineList)

            # Grab the files in this directory
            elif self.lineList[0] == 'dir':
                self.parseDir()

            else:
                # error
                raise Exception('Unknown directive: ' + repr(self.lineList[0])
                                      + ' on line: ' + repr(self.lineNum+1))
            self.lineList = self.getNextLine()

        # All done, close the final multifile
        if self.currentMfname:
            self.closePreviousMfile()

        self.mfTempDir.rmdir()
        self.pyzTempDir.rmdir()

        self.notify.info('init: Scrubber finished')

    def getNextLine(self):
        """
        Read in the next line of the line list
        """
        self.lineNum = self.lineNum + 1
        while (self.lineNum < len(self.lines)):
            # Eat python style comments
            if (self.lines[self.lineNum][0] == '#'):
                self.lineNum = self.lineNum + 1
            else:
                # Return the line as an array split at whitespace, and
                # do not include the newline character (at index -1)
                line = self.lines[self.lineNum][:-1].split()
                if line:
                    return line
                # Skip the line, it was just a blank line
                else:
                    self.lineNum = self.lineNum + 1
        else:
            return None

    def parseMfile(self):
        """
        The current line is a multifile description.
        Read in the properties and add the multifile to the downloadDb
        """
        self.currentMfname = Filename(self.lineList[1])
        self.currentMfname.setBinary()

        if self.currentMfname == "toplevel":
            # Not actually a multifile, but files to be copied into the root
            # persist dir.
            self.notify.info("Opening toplevel mfile")
        else:
            sourceFilename = Filename(self.mfTempDir,
                                    Filename(self.currentMfname.getBasenameWoExtension()))
            self.currentMfile = Multifile()
            self.currentMfile.setRecordTimestamp(False)
            sourceFilename.unlink()
            if not self.currentMfile.openWrite(sourceFilename):
                self.notify.error("Unable to open multifile %s for writing." % (sourceFilename.cStr()))
            self.notify.info('parseMfile: creating multifile: ' + self.currentMfname.cStr())

    def compFile(self, filename):
        # Return the name of the compressed file
        return Filename(filename.cStr() + '.pz')

    def parseModule(self, lineList):
        moduleName = lineList[1]
        self.freezer.addModule(moduleName)

    def parseExcludeModule(self, lineList, forbid):
        moduleName = lineList[1]
        self.freezer.excludeModule(moduleName, forbid = forbid)

    def parseDCModule(self, lineList):
        sourceFilename = Filename.expandFrom(lineList[1])

        # First, read in the dc file
        dcFile = DCFile()
        if (not dcFile.read(sourceFilename)):
            self.notify.error("Unable to parse %s." % (sourceFilename.cStr()))

        # Then add all of the .py files imported by the dc file.
        self.addDCImports(dcFile)

    def addDCImports(self, dcFile):

        # This is the list of DC import suffixes that should be
        # available to the end-user.  We publish server code
        # so users can run their own servers.  Toontown only
        # published client code.
        clientSuffixes = ['OV', 'AI']

        for n in range(dcFile.getNumImportModules()):
            moduleName = dcFile.getImportModule(n)
            moduleSuffixes = []
            if '/' in moduleName:
                moduleName, suffixes = moduleName.split('/', 1)
                moduleSuffixes = suffixes.split('/')
            self.freezer.addModule(moduleName)

            for suffix in clientSuffixes:
                if suffix in moduleSuffixes:
                    self.freezer.addModule(moduleName + suffix)


            for i in range(dcFile.getNumImportSymbols(n)):
                symbolName = dcFile.getImportSymbol(n, i)
                symbolSuffixes = []
                if '/' in symbolName:
                    symbolName, suffixes = symbolName.split('/', 1)
                    symbolSuffixes = suffixes.split('/')

                # "from moduleName import symbolName".

                # Maybe this symbol is itself a module; if that's
                # the case, we need to add it to the list also.
                self.freezer.addModule('%s.%s' % (moduleName, symbolName),
                                       implicit = True)
                for suffix in clientSuffixes:
                    if suffix in symbolSuffixes:
                        self.freezer.addModule('%s.%s%s' % (moduleName, symbolName, suffix),
                                               implicit = True)


    def parseFile(self, lineList):
        if len(lineList) > 3 and lineList[3]:
            platforms = lineList[3].split(',')
            if platform not in platforms:
                return

        # The original file we want to install, at its full path
        sourceFilename = Filename.expandFrom(lineList[1])
        sourceFilename.makeCanonical()
        sourceFilename.setBinary()
        # self.notify.debug('parseFile: ' + sourceFilename.cStr())

        # It may be ok if the named file does not exist yet.  It might
        # be generated during the whole Scrubber process.  Phase3.pyo,
        # for instance, is one such file.

        # If the original file is a py file, make sure it is compiled first
        if (sourceFilename.getExtension() == 'pyo'):
            pyfile = Filename(sourceFilename)
            pyfile.setExtension('py')
            if pyfile.exists():
                py_compile.compile(pyfile.toOsSpecific(),
                                   sourceFilename.toOsSpecific(),
                                   sourceFilename.getBasename())

        # The relative path where we want to put this file
        dir = Filename.expandFrom(lineList[2])
        # The relative path plus the file name
        basename = Filename(sourceFilename.getBasename())
        if dir == '.':
            relInstallFilename = Filename(basename)
        else:
            relInstallFilename = Filename(dir, basename)
        relInstallFilename.standardize()
        relInstallFilename.setBinary()

        # If we are storing a dc file, strip out the comments and
        # parameter names first, to provide a bit less useful
        # information to inquisitive hackers.
        if (sourceFilename.getExtension() == 'dc'):
            # First, read in the dc file
            dcFile = DCFile()
            if (not dcFile.read(sourceFilename)):
                self.notify.error("Unable to parse %s." % (sourceFilename.cStr()))

            # And then write it back out to a different filename, in
            # brief.  Here we change the filename of the
            # sourceFilename to our generated file.  We do this after
            # we have already assigned relInstallFilename, above, from
            # the original sourceFilename.
            sourceFilename.setExtension('dcb')
            if (not dcFile.write(sourceFilename, 1)):
                self.notify.error("Unable to write %s." % (sourceFilename.cStr()))

            # Adding a dc file implicitly adds all of the .py files
            # imported by the dc file.
            self.addDCImports(dcFile)

        if self.currentMfile:
            # Should we compress this subfile?
            compressLevel = 0
            if relInstallFilename.getExtension() in compressExtensions or \
                relInstallFilename.getBasename() in compressFiles:
                compressLevel = 6

            # Add the actual file contents to the actual multifile
            if self.currentMfile.addSubfile(relInstallFilename.getFullpath(),
                    sourceFilename, compressLevel) == "":
                self.notify.info("warn: %s does not exist!" % (sourceFilename.cStr()))
        else:
            # No current multifile, so copy the file into the root persist dir.
            copyDest = Filename(Filename.fromOsSpecific(os.getcwd()), relInstallFilename)
            self.copyFile(sourceFilename, copyDest)

    def parseDirCallback(self, installDir, sourceDir, dirname, filenames):
        dirnameBase = os.path.split(dirname)[1]
        if dirnameBase == 'CVS':
            # Ignore CVS directories.
            return
        if dirnameBase == '.git':
            # Ignore git directories.
            return

        # Parse out the args
        for filename in filenames:
            fullname = Filename.fromOsSpecific(dirname + '/' + filename)
            relToSource = Filename(fullname)
            if not relToSource.makeRelativeTo(sourceDir, False):
                self.notify.error('could not make %s relative to %s' % (fullname, sourceDir))
            relInstallPath = Filename(Filename(installDir, relToSource).getDirname())
            if os.path.isfile(fullname.toOsSpecific()):
                self.parseFile(['file', fullname.toOsSpecific(), relInstallPath.toOsSpecific()])

    def parseDir(self):
        # Grab all the files in this dir
        sourceDir = Filename.expandFrom(self.lineList[1])
        dirName = sourceDir.toOsSpecific()
        installDir = self.lineList[2]
        if os.path.exists(dirName):
            for root, _, files in os.walk(dirName):
                self.parseDirCallback(installDir, sourceDir, root, files)
        else:
            self.notify.error("Directory does not exist: %s" % dirName)

    def freezeExe(self, lineList):
        basename = lineList[1]
        mainModule = lineList[2]

        self.freezer.addModule(mainModule, newName='__main__')
        self.freezer.done(addStartupModules=True)

        target = self.freezer.generateCode(basename, compileToExe=True)
        target = os.path.join(os.getcwd(), target)
        self.freezer = FreezeTool.Freezer(previous = self.freezer)
        self.freezer.linkExtensionModules = True
        self.freezer.keepTemporaryFiles = False

        # Now add the generated file just like any other file, except
        # we do not want to make a copy of it since it is already
        # sitting in the persist dir
        self.parseFile(['file', target, lineList[3]])

    def freezeDll(self, lineList):
        basename = lineList[1]

        self.freezer.done()

        target = self.freezer.generateCode(basename)
        target = os.path.join(os.getcwd(), target)
        self.freezer = FreezeTool.Freezer(previous = self.freezer)
        self.freezer.linkExtensionModules = True
        self.freezer.keepTemporaryFiles = False

        self.parseFile(['file', target, lineList[2]])

    def closePreviousMfile(self):
        if self.currentMfile:
            self.notify.info('closePreviousMfile: writing mfile: ' + self.currentMfname.toOsSpecific())

        self.flushIO()

        if self.currentMfile:
            # Write the mf to disk
            self.currentMfile.close()

            # Get the mf name out of the mf.pz name
            sourceFilename = Filename(self.mfTempDir,
                                      Filename(self.currentMfname.getBasenameWoExtension()))
            relInstallFilename = Filename(sourceFilename.getBasename())
            persistFilename = Filename(self.persistDir, relInstallFilename)

            persistFilename.setBinary()
            sourceFilename.setBinary()

            self.moveFile(sourceFilename, persistFilename)

    def bunzipToTemporary(self, filename):
        # Runs bunzip2 on the indicated file, writing the result to a
        # temporary filename, and returns the temporary filename.
        tempFilename = Filename.temporary('', 'Scrub_')
        command = 'bunzip2 <"%s" >"%s"' % (filename.toOsSpecific(), tempFilename.toOsSpecific())
        print(command)
        exitStatus = os.system(command)
        if exitStatus != 0:
            raise 'Command failed: %s' % (command)

        return tempFilename

    def copyFile(self, fromFilename, toFilename):
        if fromFilename != toFilename:
            osDir = Filename(toFilename.getDirname()).toOsSpecific()
            if not os.path.isdir(osDir):
                os.makedirs(osDir)
            self.notify.info('Copying %s to %s' % (fromFilename.cStr(), toFilename.cStr()))
            shutil.copy(fromFilename.toOsSpecific(), toFilename.toOsSpecific())
            #os.system('chmod 644 "%s"' % toFilename.toOsSpecific())

    def moveFile(self, fromFilename, toFilename):
        self.notify.info('Moving %s to %s' % (fromFilename.cStr(), toFilename.cStr()))
        toFilename.unlink()
        if not fromFilename.renameTo(toFilename):
            self.notify.error('Unable to move %s to %s.' % (fromFilename.cStr(), toFilename.cStr()))
        #os.system('chmod 644 "%s"' % toFilename.toOsSpecific())

    def compressFile(self, sourceFilename, destFilename, useBzip2 = 0):
        self.notify.info('Compressing from %s to %s' % (sourceFilename.cStr(), destFilename.cStr()))
        if useBzip2:
            command = 'bzip2 <"%s" >"%s"' % (sourceFilename.toOsSpecific(),
                                             destFilename.toOsSpecific())
        else:
            command = 'pzip -o "%s" "%s"' % (destFilename.toOsSpecific(),
                                             sourceFilename.toOsSpecific())
        print(command)
        exitStatus = os.system(command)
        if exitStatus != 0:
            raise 'Command failed: %s' % (command)
        #os.system('chmod 644 "%s"' % destFilename.toOsSpecific())

scrubber = Scrubber()
