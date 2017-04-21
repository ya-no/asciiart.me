﻿#coding:utf-8

import sys
import math
import numpy as np
from PIL import Image
import PIL.Image
import operator

from AA_Dijkstra import Edge, Dijkstra

class Chr:
    def __init__(self, _chr, _chrIm_h, _chrIm_w):
        self.chr = _chr
        self.chrIm_h = _chrIm_h
        self.chrIm_w = _chrIm_w
        self.chrIm = np.zeros((self.chrIm_h, self.chrIm_w), dtype=np.uint8)

    @classmethod
    def frominstance(cls, instance):
        new_instance = cls(instance.chr, instance.chrIm_w, instance.chrIm_h)
        for y in range(instance.chrIm_h):
            for x in range(instance.chrIm_w):
                new_instance.chrIm[y, x] = instance.chrIm[y, x]
        return new_instance

class ChrTool:
    def __init__(self):
        self.offset = 3

        self.header1 = u'<!DOCTYPE html>\r\n<html>\r\n<head>\r\n<meta http-equiv="Content-Type" content="text/html">\r\n<meta charset="UTF-8">\r\n</head>\r\n<body>\r\n'
        self.header2 = u"<div style=\"font-family:'ＭＳ Ｐゴシック';font-size:16px;line-height:18px;\">\r\n<nobr>\r\n"
        self.footer1 = u"</nobr>\r\n</div>\r\n"
        self.footer2 = u"</body>\r\n</html>\r\n"

        # chrDict準備
        # Windowsのメモ帳で文字コードを utf-8 に変換したものを読み込んでいる
        self.chrDict = self.getChrListFrom18Line("chrDict_20170327_utf8.txt")

    def getChrListFrom18Line(self, filename):

        chrList = []
        f = open(filename)

        # １行目はDB内の登録文字数
        line = f.readline()  # 1行を文字列として読み込む(改行文字も含まれる)
        chr_num = int(line)

        for i in range(chr_num):

            # http://www.ctrlshift.net/blog/?id=20080927_convert_unicode_utf8_in_python
            # https://gist.github.com/devlights/4561968

            chr_tmp = f.readline() # 文字
            chr_tmp = chr_tmp.decode('utf-8') # utf-8をunicode にデコードして保持しておく
            chr_tmp = chr_tmp[0]
            chr = chr_tmp

            chrIm_w_str = f.readline() # 文字の幅
            chrIm_w = int(chrIm_w_str)

            # Chr
            chrTmp = Chr(chr, 18, chrIm_w)

            for j in range(18):
                line = f.readline()
                for k in range(chrTmp.chrIm_w):
                    if line[k] == '1':
                        chrTmp.chrIm[j, k] = 0
                    else:
                        chrTmp.chrIm[j, k] = 255

            chrList.append(chrTmp)

        f.close()
        return chrList

    def getAA(self, imgGray): #, comment):

        im_h = imgGray.shape[0]
        im_w = imgGray.shape[1]

        count = int( (float(im_h) ) / 18.0)

        routes = []

        for i in range(count):

            print('line : ' + str(i))

            # --- generate ascii art ---

            pow_val =  0.4 * math.log(1.5) / math.log(2.0) + 0.7 # 1.0

            y = i * 18

            flag = True
            if flag:

                labels = [] # list of int
                edges = [] # list of Edge

                for x in range(im_w - 20):

                    labels.append(x)

                    min_chrs = [None] * 14
                    min_vals = [1.0e29] * 14

                    j = 0
                    for chr_tmp in self.chrDict:

                        # ssd_val = 0.0
                        # for yy in range(2, chr_tmp.chrIm_h):
                        #     for xx in range(0, chr_tmp.chrIm_w):
                        #         ssd_tmp = imgGray[y+yy, x+xx] - chr_tmp.chrIm[yy, xx]
                        #         ssd_val += ssd_tmp * ssd_tmp
                        #     if (math.pow(ssd_val, pow_val) >= min_vals[chr_tmp.chrIm_w - 3]):
                        #         break

                        imgDiff = imgGray[y+2:y+18, x:x+chr_tmp.chrIm_w] - chr_tmp.chrIm[2:18,:]
                        ssd_val = np.sum(imgDiff * imgDiff)

                        ssd_val = float(math.pow(ssd_val, pow_val))

                        if ssd_val < min_vals[chr_tmp.chrIm_w - 3]:
                            min_vals[chr_tmp.chrIm_w - 3] = ssd_val
                            min_chrs[chr_tmp.chrIm_w - 3] = chr_tmp

                        if min_vals[chr_tmp.chrIm_w - 3] == 0.0 and j > 1:
                            break
                        j += 1

                    for k in range(14):
                        if min_chrs[k] != None:
                            assert min_vals[k] != 1.0e30, 'min_valsがおかしい！'
                            assert min_chrs[k].chrIm_w == (k + 3), 'min_chrsがおかしい！'
                            edges.append(Edge(x + min_chrs[k].chrIm_w, x, min_vals[k], min_chrs[k]))

                dijkstra = Dijkstra()
                route = dijkstra.doDijkstra(labels, edges)
                routes.append(route)

        # --- finalize ---

        strTmpContents = u''

        for k in range(len(routes)):

            chrs1 = []

            index = 0

            while True:

                if index + 1 >= len(routes[k]):
                    break

                label_parent = routes[k][index].sLabel
                label = routes[k][index].eLabel
                cost = routes[k][index].cost
                min_index2 = index

                # 同一ラベルを調べる
                while True:

                    index += 1

                    if index >= len(routes[k]):
                        break

                    # 同じ eLabel を持つルートを調べる
                    if routes[k][index].eLabel == label:
                        # 同一ラベルだったら cost を調べる
                        if routes[k][index].cost < cost:
                            cost = routes[k][index].cost
                            label_parent = routes[k][index].sLabel
                            min_index2 = index
                    else:
                        break

                if index >= len(routes[k]):
                    break

                chrs1.append(routes[k][min_index2].chr)

                while True:

                    if routes[k][index].eLabel == label_parent:
                        break

                    index += 1

                    if index >= len(routes[k]):
                        break

            # 行頭に必ず全角スペースを入れておく
            strTmpContents += u'　'

            for chr_tmp in chrs1:
                strTmpContents += chr_tmp.chr

            strTmpContents += u'<br>\r\n'

        # 半角スペースを２つ以上重ねても強制的に１つにまとめられる、の対策
        # 半角スペース２つを全角スペース１つに置換する（置換ごとに + 1 ドットずれる）
        strTmpContents = strTmpContents.replace(u'  ', u'　')

        # 太い線が２重線(l!)になってしまっているものを修正する
        strTmpContents = strTmpContents.replace(u'l!', u'|.')
        strTmpContents = strTmpContents.replace(u'j!', u'｝')

        strTmp2 = u''
        strTmp2 += self.header1
        strTmp2 += self.header2
        strTmp2 += strTmpContents
        # strTmp2 += commentTmp
        strTmp2 += self.footer1
        strTmp2 += self.footer2

        return strTmp2

