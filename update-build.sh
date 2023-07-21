#!/bin/bash
oldnum=$(cut -d '=' -f2 build.txt)
newnumber=$(expr $oldnum + 1)
sed -i "s/$oldnum\$/$newnumber/g" ./build.txt
sed -i "s/\.build.*\"/.build.$newnumber\"/g" ./conf*.json