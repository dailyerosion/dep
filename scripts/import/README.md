
Brian Gelder provides me a 7zip file with individual flowpaths included.  There
is one file per HUC12.  Step 1 is to run this through flowpath_importer.py

Then flowpath2prj.py generates the PRJ files.

Then prj2wepp.py

 3 Mar 2016 - Processed new soil files from David James, discovered the
following old entries.

-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1402/102300031402_415.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_5.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_27.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_47.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_94.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_100.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_148.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_184.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_200.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_217.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_237.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1302/102300031302_243.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1411/102300031411_175.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1406/102300031406_8.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1406/102300031406_254.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1211/102300031211_221.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1301/102300031301_46.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1301/102300031301_69.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1301/102300031301_105.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1301/102300031301_213.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1403/102300031403_28.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1403/102300031403_189.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1403/102300031403_460.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1403/102300031403_567.sol
-rw-rw-r-- 1 akrherz akrherz 187 Apr 23  2015 ./10230003/1403/102300031403_579.sol