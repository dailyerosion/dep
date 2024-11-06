      subroutine strip(oldnam,newnam)
c
c     + + + PURPOSE + + +
c
c     SR STRIP strips all characters except the 8 character prefix to a
c     file name. Used for the creation of the initial condition name in
c     the initial condition file.
c
c     Called from CONTIN.
c     Author(s): Whittemore
c     Reference in User Guide:
c
c     Version: This module not yet recoded.
c     Date recoded:
c     Recoded by:
c
c     + + + KEYWORDS + + +
c
c     + + + PARAMETERS + + +
c
c     + + + ARGUMENT DECLARATIONS + + +
c
      character*51 oldnam
      character*8 newnam
c
c     + + + ARGUMENT DEFINITIONS + + +
c
c     newnam - name to be passed back to contin to be used as scenario
c              name in initial condition file.
c     oldnam - name read in from screen or shell file
c
c     + + + COMMON BLOCKS + + +
c
c     + + + LOCAL VARIABLES + + +
c
      integer spos, filpos, tpos
c
c     + + + LOCAL DEFINITIONS + + +
c
c     spos   - position counter
c     filpos - position in newnam for character from oldnam
c     tpos   - position counter
c
c     + + + SUBROUTINES CALLED + + +
c
c     + + + DATA INITIALIZATIONS + + +
c
c
      newnam = '        '
    
      filpos = 1
c
      do 10 spos = len(oldnam), 1, -1
c
        if (oldnam(spos:spos).eq.'.') then
          tpos = spos - 1
c
c       This is the base part of the name, find the beginning
c
          do while (oldnam(tpos:tpos).ne.'/'.and.oldnam(tpos:tpos).ne.
     1        '\')
            tpos = tpos  - 1
            if (tpos.lt.1) then
               exit
            end if
          end do

         tpos = tpos + 1
         do while (oldnam(tpos:tpos).ne.'.')
             newnam(filpos:filpos) = oldnam(tpos:tpos)
             filpos = filpos + 1;
             tpos = tpos + 1
             if (filpos.gt.8) then
                 return
             end if
         end do
         newnam(filpos:filpos) = ''
c
          return
c
       else if (oldnam(spos:spos).eq.'/'.or.oldnam(spos:spos).eq.'\')
     1      then
c         Filename has no extension
          
          tpos = spos + 1
          
c         
          do while (tpos.lt.len(oldnam))
                newnam(filpos:filpos) = oldnam(tpos:tpos)
                filpos = filpos + 1;
                tpos = tpos + 1
                if (filpos.gt.8) then
                 return
             end if
                
          end do
           newnam(filpos:filpos) = ''
c
          return
          end if
  10    continue
          
c
c     If we get here the name has no extension or path, just take first chars
      tpos = 1
      do while (tpos.lt.len(oldnam))
          newnam(filpos:filpos) = oldnam(tpos:tpos)
          filpos = filpos + 1
          tpos = tpos + 1
          if (filpos.gt.8) then
               return
          end if
      end do
      
      newnam(filpos:filpos) = '';
      return
      
      end
