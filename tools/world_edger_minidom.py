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
from xml.dom.minidom import getDOMImplementation

EDGE_COLLISION = 20
OUTER_LIMITX = 25
OUTER_LIMITY = 20
CLIENT_MAPS = 'maps'
MAP_RE = re.compile(r'^\d{3}-\d{3}-\d{1}(\.tmx)?$')
GROUND_RE = re.compile('ground', re.I)
FRINGE_RE = re.compile('fringe', re.I)
OVER_RE = re.compile('over', re.I)
LAYER_ORDER = set(['Over','Fringe','Ground'])
LAYER_START = 1
LAYER_MAX = 5

class parseMap:

    def __init__(self, map):
        self.layername = ""
        self.data = ""
        self.layercopy = {}
        self.layeredges = {'BaseLayers': {}}
        self.mapdata = xml.dom.minidom.parse(map)
        self.handleMap()

    def handleMap(self):
        maptags = self.mapdata.documentElement
        self.mapwidth = int(maptags.attributes['width'].value)
        self.mapheight = int(maptags.attributes['height'].value)
        self.handleMapProperties()
        self.handleTileSets()
        self.handleLayers()
        self.handleObjects()
        return

    def handleMapProperties(self):
        self.layeredges['mapProperties'] = self.mapdata.getElementsByTagName("property")
        return

    def handleTileSets(self):
        self.layeredges['Tilesets'] = self.mapdata.getElementsByTagName("tileset")
        return

    def handleLayers(self):
        layers = self.mapdata.getElementsByTagName("layer")
        for layer in layers:
            self.layername = layer.attributes['name'].value
            self.layerData = layer.getElementsByTagName("data")
            self.handleLayerData()
            self.layercopy[self.layername] = self.data
        return

    def handleLayerData(self):
        self.data = self.layerData[0].firstChild.nodeValue
        self.findTilesToCopy()
        return

    def handleObjects(self):
        self.layeredges['objects'] = self.mapdata.getElementsByTagName("objectgroup")
        return

    def findTilesToCopy(self):
        self.layeredges['BaseLayers'][self.layername] = {'north': {}, 'south': {}, 'west': {}, 'east': {}}
        reader = csv.reader(self.data.strip().split('\n'), delimiter=',')
        for row in reader:
            self.layeredges['BaseLayers'][self.layername]['west'][reader.line_num] = row[EDGE_COLLISION:(EDGE_COLLISION*2)]
            self.layeredges['BaseLayers'][self.layername]['east'][reader.line_num] = row[(self.mapwidth - (EDGE_COLLISION*2)):(self.mapwidth - EDGE_COLLISION)]
            if(reader.line_num in range(EDGE_COLLISION,((EDGE_COLLISION*2) + 1))):
                self.layeredges['BaseLayers'][self.layername]['south'][reader.line_num] = row
            if(reader.line_num in range((self.mapheight - (EDGE_COLLISION*2)),(self.mapheight - (EDGE_COLLISION - 1)))):
                self.layeredges['BaseLayers'][self.layername]['north'][reader.line_num] = row

class copyMap:

    def __init__(self, map, layeredges = {}, direction = False):
        self.tilesets = {}
        self.layername = ""
        self.data = ""
        self.layercopy = {}
        self.layeredges = layeredges
        self.layeredges['LayerCopy'] = {}
        self.direction = direction
        self.mapdata = xml.dom.minidom.parse(map)
        self.tmxout = getDOMImplementation().createDocument(None, 'map', None)
        self.handleMap()

    def handleMap(self):
        self.maptags = self.mapdata.documentElement
        self.mapwidth = int(self.maptags.attributes['width'].value)
        self.mapheight = int(self.maptags.attributes['height'].value)
        self.tmxout.documentElement.setAttribute(u'width', str(self.mapwidth))
        self.tmxout.documentElement.setAttribute(u'height', str(self.mapheight))
        self.handleMapProperties()
        self.handleTileSets()
        self.handleLayers()
        self.handleObjects()
        return

    def handleMapProperties(self):
        mapProperties = self.mapdata.getElementsByTagName("property")
        newMapProps = self.tmxout.createElement("properties")
        for mapProp in mapProperties:
            newProp = self.tmxout.createElement("property")
            newProp.setAttribute(u'name', str(mapProp.attributes['name'].value))
            newProp.setAttribute(u'value', str(mapProp.attributes['value'].value))
            newMapProps.appendChild(newProp)
        self.tmxout.documentElement.appendChild(newMapProps)
        return

    def handleTileSets(self):
        self.xmlTileSets = self.mapdata.getElementsByTagName("tileset")
        tileGids = []
        for tileSet in self.xmlTileSets:
            newTileSet = self.tmxout.createElement('tileset')
            newTileSet.attributes['firstgid'] = tileSet.attributes['firstgid'].value
            newTileSet.attributes['source'] = tileSet.attributes['source'].value
            self.tmxout.documentElement.appendChild(newTileSet)
            tileGids.append(tileSet.attributes['firstgid'].value)
        # Append Each Tileset
        for tileSet in self.layeredges['Tilesets']:
            newTileSet = self.tmxout.createElement('tileset')
            if not tileSet.attributes['firstgid'].value in tileGids:
                newTileSet.attributes['firstgid'] = tileSet.attributes['firstgid'].value
                newTileSet.attributes['source'] = tileSet.attributes['source'].value
                self.tmxout.documentElement.appendChild(newTileSet)
        return

    def handleLayers(self):
        layers = self.mapdata.getElementsByTagName("layer")
        for layer in layers:
            self.layeredges['LayerCopy'][layer.attributes['name'].value] = layer
        self.handleLayerData()
        return

    def handleLayerData(self):
        print (self.layeredges['BaseLayers'].keys())
        print (self.layeredges['LayerCopy'].keys())
        #print (self.tmxout.toxml())
        sys.exit(2)
        layerstart = LAYER_START
        for layer in LAYER_ORDER:
            while layerstart <= LAYER_MAX:
                self.layername = layer + str(layerstart)
                if(self.layername in self.layeredges.keys()):
                    singlelayer = self.layeredges[self.layername]
                    if ('LayerCopy' in singlelayer.keys()):
                        print (singlelayer.keys())
                        self.layerData = (singlelayer['LayerCopy'])
                        self.data = self.layerData.firstChild.nodeValue
                        self.mapCopyTiles()
                    else:
                        print ("Create Layer")
                        print (self.layername)
                layerstart = layerstart + 1
        return

    def handleObjects(self):
        objects = self.mapdata.getElementsByTagName("objectgroup")
        # Create element objectgroup, For element in element attach node
        return

    def mapCopyTiles(self):
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
        self.layerData.firstChild.nodeValue = "\n" + copiedrows
        return

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

            # Get/Open/Parse Adjacent Maps
            adjacentmaps = {'south': "%s-%03d-%s.tmx" % (mapx, mapynorth, level), 'north': "%s-%03d-%s.tmx" % (mapx, mapysouth, level), 'west': "%03d-%s-%s.tmx" % (mapxwest, mapy, level), 'east': "%03d-%s-%s.tmx" % (mapxeast, mapy, level)}
            for mapdirection in adjacentmaps:
                mapname = posixpath.join(tmx_dir, adjacentmaps[mapdirection])
                MapData = copyMap(mapname, mainMapData.layeredges, mapdirection)
                print ("base map: %s.tmx" % (base))
                print ("%s map: %s" % (mapdirection, adjacentmaps[mapdirection]))
                #newxml = MapData.tmxout.toxml('utf-8').replace('?>','?>\n')
                #map_file = open(mapname, "w")
                #map_file.write(newxml)
                #map_file.close()

if __name__ == '__main__':
    main(sys.argv)
