#!/bin/bash
## Copyright 2011 Ben Longbons
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 2 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

tilesize()
{
    let TILESIZE="$1"
}
continent()
{
    O=~/www/updates/"$1".png
    let T_W="$2"
    let T_H="$3"
    let P_W=T_W*TILESIZE
    let P_H=T_H*TILESIZE
    convert -size ${P_W}x${P_H} canvas:transparent "$O"
}
offset()
{
    let O_X+="$1"
    let O_Y+="$2"
}
map()
{
    local I T_X T_Y P_X P_Y
    I="graphics/minimaps/$1".png
    let T_X=O_X+"$2"
    let T_Y=O_Y+"$3"
    let P_X=T_X*TILESIZE
    let P_Y=T_Y*TILESIZE

    convert "$O" \( "$I" -repage ${P_W}x${P_H}+${P_X}+${P_Y} -background transparent -flatten \) \( -clone 0 -clone 1 -composite \) \( -clone 1 -clone 0 -composite \) -delete 0,1 -compose blend -set option:compose:args 50 -composite "$O"
}

for ARG
do
    source "$ARG"
done
