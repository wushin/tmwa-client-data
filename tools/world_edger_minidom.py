#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##    Copyeast © 2012 Wushin <pasekei@gmail.com>
##
##    This file is part of The Mana World
##
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
##

## Notes: World Map connects on the edges

from __future__ import print_function

import os
import re
import sys
import csv
import posixpath
import xml.dom.minidom

EDGE_COLLISION = 20
OUTER_LIMITX = 25
OUTER_LIMITY = 20
CLIENT_MAPS = 'maps'
MAP_RE = re.compile(r'^\d{3}-\d{3}-\d{1}(\.tmx)?$')

class parseMap:

    def __init__(self, map, copydata = False, layeredges = {}, direction = False):
        self.tilesets = {'0': 'null'}
        self.layername = ""
        self.data = ""
        self.layercopy = {}
        self.layeredges = layeredges
        self.copydata = copydata
        self.direction = direction
        mapdata = xml.dom.minidom.parse(map)
        self.tmxout = mapdata
        self.handleMap(mapdata)

    def handleMap(self, mapdata):
        maptags = mapdata.getElementsByTagName("map")
        self.mapwidth = int(maptags[0].attributes['width'].value)
        self.mapheight = int(maptags[0].attributes['height'].value)
        mapProperties = mapdata.getElementsByTagName("property")
        self.handleMapProperties(mapProperties)
        tileSets = mapdata.getElementsByTagName("tileset")
        self.handleTileSets(tileSets)
        layers = mapdata.getElementsByTagName("layer")
        self.handleLayers(layers)
        objects = mapdata.getElementsByTagName("objectgroup")
        self.handleObjects(objects)
        return

    def handleMapProperties(self, mapProperties):
        return

    def handleTileSets(self, tileSets):
        for tileSet in tileSets:
            self.tilesets[tileSet.attributes['firstgid'].value] = tileSet.attributes['source'].value
        return

    def handleLayers(self, layers):
        for layer in layers:
            self.layername = layer.attributes['name'].value
            self.layerData = layer.getElementsByTagName("data")
            self.handleLayerData()
            self.layercopy[self.layername] = self.data
        return

    def handleLayerData(self):
        self.data = self.layerData[0].firstChild.nodeValue
        if(self.layername == 'Collision'):
            return
        if(self.copydata):
            self.mapCopyTiles()
        else:
            self.findTilesToCopy()
        return

    def handleObjects(self, objects):
        return

    def mapCopyTiles(self):
        # Check if Layer Needs Edit
        if (not (self.layername in self.layeredges.keys())):
            #print ("Nothing to copy on this layer")
            return
        # Edit Tilesets
        if (len(set(self.layeredges[self.layername]['Tilesets'].iteritems())-set(self.tilesets.iteritems()))):
            for tileset in (self.layeredges[self.layername]['Tilesets']):
                # Should add logic to check if tileset is within range of another.
                if not tileset in self.tilesets.keys():
                    self.tilesets[tileset] = self.layeredges[self.layername]['Tilesets'][tileset]
        # Edit Layer Data
        reader = csv.reader(self.data.strip().split('\n'), delimiter=',')
        copiedrows = ""
        for row in reader:
            if(reader.line_num in range(1,(EDGE_COLLISION + 1)) and self.direction == 'north'):
                copiedrows += (','.join(self.layeredges[self.layername]['north'][(reader.line_num + (self.mapheight - (EDGE_COLLISION*2)))][:-1])) + ","
            elif(reader.line_num in range((self.mapheight - (EDGE_COLLISION - 1)),(self.mapheight + 1)) and self.direction == 'south'):
                if(reader.line_num == self.mapheight):
                    copiedrows += (','.join(self.layeredges[self.layername]['south'][(reader.line_num - (self.mapheight - (EDGE_COLLISION*2)))][:-1]))
                else:
                    copiedrows += (','.join(self.layeredges[self.layername]['south'][(reader.line_num - (self.mapheight - (EDGE_COLLISION*2)))][:-1])) + ","
            elif(self.direction == 'west'):
                westrow = self.layeredges[self.layername]['west'][reader.line_num]
                if(reader.line_num == self.mapheight):
                    copiedrows += (','.join(row[:(self.mapwidth - EDGE_COLLISION)] + westrow))
                else:
                    copiedrows += (','.join(row[:(self.mapwidth - EDGE_COLLISION)] + westrow)) + ","
            elif(self.direction == 'east'):
                eastrow = self.layeredges[self.layername]['east'][reader.line_num]
                copiedrows += (','.join(eastrow + row[EDGE_COLLISION:]))
            else:
                copiedrows += (','.join(row))
            copiedrows += "\n"
        self.layerData[0].firstChild.nodeValue = "\n" + copiedrows
        return

    def findTilesToCopy(self):
        self.layeredges[self.layername] = {'north': {}, 'south': {}, 'west': {}, 'east': {}, 'Tilesets': self.tilesets}
        reader = csv.reader(self.data.strip().split('\n'), delimiter=',')
        for row in reader:
            self.layeredges[self.layername]['west'][reader.line_num] = row[EDGE_COLLISION:(EDGE_COLLISION*2)]
            self.layeredges[self.layername]['east'][reader.line_num] = row[(self.mapwidth - (EDGE_COLLISION*2)):(self.mapwidth - EDGE_COLLISION)]
            if(reader.line_num in range(EDGE_COLLISION,((EDGE_COLLISION*2) + 1))):
                self.layeredges[self.layername]['south'][reader.line_num] = row
            if(reader.line_num in range((self.mapheight - (EDGE_COLLISION*2)),(self.mapheight - (EDGE_COLLISION - 1)))):
                self.layeredges[self.layername]['north'][reader.line_num] = row

def main(argv):
    _, client_data = argv
    tmx_dir = posixpath.join(client_data, CLIENT_MAPS)

    for arg in os.listdir(tmx_dir):
        base, ext = posixpath.splitext(arg)

        if ext == '.tmx' and MAP_RE.match(base):
            tmx = posixpath.join(tmx_dir, arg)
            # Create Tileset Mapping
            mainMapData = parseMap(tmx)
            (mapx,mapy,level) = (base.split('-'))
            # World Map loops onto itself
            mapxwest = int(mapx) - 1
            mapxeast = int(mapx) + 1
            if (int(mapx) == 1):
                mapxwest = OUTER_LIMITX
            elif (int(mapx) == OUTER_LIMITX):
                mapxeast = 1

            mapynorth = int(mapy) - 1
            mapysouth = int(mapy) + 1
            if (int(mapy) == 1):
                mapynorth = OUTER_LIMITY
            if (int(mapy) == OUTER_LIMITY):
                mapysouth = 1

            print ("base map: %s.tmx" % (base))
            # Get/Open/Parse Adjacent Maps
            adjacentmaps = {'south': "%s-%03d-%s.tmx" % (mapx, mapynorth, level), 'north': "%s-%03d-%s.tmx" % (mapx, mapysouth, level), 'west': "%03d-%s-%s.tmx" % (mapxwest, mapy, level), 'east': "%03d-%s-%s.tmx" % (mapxeast, mapy, level)}
            for mapdirection in adjacentmaps:
                print ("%s map: %s" % (mapdirection, adjacentmaps[mapdirection]))
                mapname = posixpath.join(tmx_dir, adjacentmaps[mapdirection])
                MapData = parseMap(mapname, True, mainMapData.layeredges, mapdirection)
                newxml = MapData.tmxout.toxml('utf-8').replace('?>','?>\n')
                map_file = open(mapname, "w")
                map_file.write(newxml)
                map_file.close()

if __name__ == '__main__':
    main(sys.argv)
