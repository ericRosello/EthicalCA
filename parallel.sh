#!/bin/sh

CURRENTDATE=`date +"%m_%d__%H_%M_%S"`

for i in {1..5}
do
   python main_menu.py $i $CURRENTDATE 5 &
done