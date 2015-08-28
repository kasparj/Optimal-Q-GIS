nastavit QGISHOME = /usr v premmenych v QGIS

Ktore subory editovat:

converter.py - sluzi na konverziu .xml suborov na .shp subory a .csv. Vola sa
funkcia ****(je oznacena, tusim ako posledna). Zaroven aj ulozi vsetky subory,
cize po zavolani funkcie **** je mozne QGIS ukoncit. Obsahuje aj dalsie
funkcie, ich popis je priamo v pri funkcii, tie sa nevolaju mimo ten skript.


open_all.py, database_dialog.py, show_all.py ... su subory, pre kazdu polozku v
menu - obsah je viac-menej rovnaky - potom na zaciatku database.py treba
importovat z toho

database.py - !! Dolezite - tu sa inicializuje cely plugin, tu sa reaguje na
signaly, tu sa volaju vsetky funckie... popis v subore

****.ui - editovat v Qt, inak nic ine

ikony - 

dalsie subory netreba editovat
