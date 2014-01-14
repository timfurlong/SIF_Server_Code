'''
@author:    Tim Furlong
@summary:   This module is an interface to the rsync linux/unix command.
            rsync is used in this project to synchronize the incoming images to the server
            with the processing computer.

            We additionally use rsync as a means of syncing our codebase from our local
            machines to the server. When using these functions, be careful! You may delete
            data on the server computers. However, this should only happen with the
            --default flag set in the command.
'''
from subprocess import call, PIPE # To create command line calls
import os
from sys import argv
import logging

# Files common to both server and processing computers
common = ['CapstoneDatabase.db',
          'DBManager.py',
          'EXIF.py',
          'config.py',
          'rsync.py',
          'README.txt',
          'outputFiles']


# baseCmd = "rsync -r -t -p -v -z --progress --delete"
baseCmd = "rsync -r -C -t -p -a -z -v --progress"
cet_research_root = 'sif@cet-research.colorado.edu:~/SIF_Processing'

class rsync:
   def __init__(self, debug=False):
      self.debug  = debug # Set debug mode
      if self.debug:
         logLevel = logging.DEBUG
      else:
         logLevel = logging.INFO
      # Set logging level
      logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)

   def syncServerCode(self):
      '''Sync the server codebase (sockets) to cet-sif. Also sync common files.'''

      source = os.path.abspath( 'sockets' )
      dest   = 'sif@cet-sif.colorado.edu:~/SIF_Server/'

      cmd = baseCmd
      cmd = '%s --delete' % cmd
      cmd = cmd.split(' ')
      cmd.append( source )
      cmd.append( dest )

      print '----------------------------'
      print '>> %s\n' % ' '.join( cmd )
      call( cmd )

      self.syncCommonToSIF()

   def syncProcessingCode(self):
      '''Sync the processing codebase (Matlab) to cet-research. Also sync common files.'''
      source = os.path.abspath( 'Matlab' )
      dest   = cet_research_root

      cmd = baseCmd
      cmd = '%s --delete' % cmd
      cmd = cmd.split(' ')
      cmd.append( source )
      cmd.append( dest )

      print '----------------------------'
      print '>> %s\n' % ' '.join( cmd )
      call( cmd )

      source = os.path.abspath( 'Forecast' )

      cmd = baseCmd
      cmd = '%s --delete' % cmd
      cmd = cmd.split(' ')
      cmd.append( source )
      cmd.append( dest )

      print '----------------------------'
      print '>> %s\n' % ' '.join( cmd )
      call( cmd )

      self.syncCommonToResearch()

   def syncCommonToSIF(self):
      '''Sync all common files to the server ( cet-sif )'''
      dest = 'sif@cet-sif.colorado.edu:~/SIF_Server/'
      for c in common:
         source = os.path.abspath(c)
         cmd = baseCmd
         cmd = '%s --delete' % cmd
         cmd = cmd.split(' ')
         cmd.append( source )
         cmd.append( dest )

         print '----------------------------'
         print '>> %s\n' % ' '.join( cmd )
         call( cmd )

   def syncCommonToResearch(self):
      '''Sync all common files to the processing computer (cet-research)'''
      dest = '%s/' % cet_research_root
      for c in common:
         source = os.path.abspath(c)
         cmd = baseCmd
         cmd = '%s --delete' % cmd
         cmd = cmd.split(' ')
         cmd.append( source )
         cmd.append( dest )


         print '----------------------------'
         print '>> %s\n' % ' '.join( cmd )
         call( cmd )

   def sendPhotoToCETResearch(self, groupDir, verbose=False ):
      '''Send a new photo in <groupDir> to cet-research. This actually performs a
      sync of the entire contents of <groupDir>, so it can be used to send multiple.
      We currently only send one at a time though.'''

      if verbose:
         customOut = None
      else:
         customOut = PIPE
      dest = '%s/outputFiles/Unprocessed/%s/' % (cet_research_root, os.path.basename( groupDir ) )

      cmd = baseCmd
      cmd = cmd.split(' ')
      cmd.append( '%s/' % groupDir )
      cmd.append( dest )

      if verbose:
         print '----------------------------'
         print '>> %s\n' % ' '.join( cmd )
      call( cmd, stdout=customOut )

      dest = cet_research_root

      cmd = baseCmd
      cmd = cmd.split(' ')
      cmd.append( 'CapstoneDatabase.db' )
      cmd.append( dest )

      if verbose:
         print '----------------------------'
         print '>> %s\n' % ' '.join( cmd )
      call( cmd, stdout=customOut )

      print '%s synced to cet-research' % os.path.basename( groupDir )

   def syncPowerWithCETResearch( self, verbose=False ):
      '''Sync power data with processing computer. Under the hood, we '
      are rsyncing the database file.'''
      if verbose:
         customOut = None
      else:
         customOut = PIPE

      dest = cet_research_root

      cmd = baseCmd
      cmd = cmd.split(' ')
      cmd.append( 'CapstoneDatabase.db' )
      cmd.append( dest )

      if verbose:
         print '----------------------------'
         print '>> %s\n' % ' '.join( cmd )
      call( cmd, stdout=customOut )

      print 'Power data synced with cet-research'

if __name__ == '__main__':
   '''Call this file on the command line with one of <possibleArgs> as an argument
   to run one of the rsync methods outlined below'''

   possibleArgs = ['cet-research', 'cet-sif', 'commonSIF', 'commonResearch']
   if len(argv) < 2:
      print 'Requires one of these arguments to run: %s' % possibleArgs
      exit(1)
   if argv[1] not in possibleArgs:
      print 'Requires one of these arguments to run: %s' % possibleArgs
      exit(1)
   rsync = rsync()
   if argv[1] == 'cet-research':
      rsync.syncProcessingCode()
   elif argv[1] == 'cet-sif':
      rsync.syncServerCode()
   elif argv[1] == 'commonSIF':
      rsync.syncCommonToSIF()
   elif argv[1] == 'commonResearch':
      rsync.syncCommonToResearch()