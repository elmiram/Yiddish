# -*- coding = utf-8 -*-

# Term Paper Project: Automatic Disambiguation in the Yiddish National Corpus <web-corpora.net/YNC/search/>
# 2013-2014
# Project Part: Brill's Transformation-Driven Disambiguation
# Author: Elmira Mustakimova <egmustakimova_2@edu.hse.ru>
#         2nd year student at HSE NRU Dept. of Linguistics Moscow
# Academic Advisor: Timofey Arkhangelskiy

"""
Run BrillTrainer:

Step 0.
Create an instance of the class.

>>> m = BrillTrainer()

Step 1.
Define the directory with corpus files, the extension of corpus files is by default '.xhtml'.
To change the extension, pass extension=".your-extension".
You may pass printing=True as one of the arguments of this function to print the created corpus to file.
The bigger the files in the directory are, the more transformations are generated.

>>> m.make_POS_file(u'C:\\corpus', printing=True)

Step 2.
Starts collecting transformations.
printRules=True - for writing list of rules to file.
printCorp=True - for writing the transformed corpus to file.
maximum - to limit the maximum number of transformations.

>>> m.run_brill(printRules=True, maximum=300)

Step 3.
Applies learned transformations to the files in the given directory that have the given extension.
If the parameter "rules" is specified with path to list of transformations,
the function opens the file and applies the rules extracted from it
(which allows to skip steps 1 and 2 if a list of transformations is available).

>>> m.start_apply(u'C:\\corpus')

>>> m.start_apply(u'C:\\corpus', rules=u'C:\\list-of-transformations.txt')
"""

from __future__ import division
__author__ = 'elmira'

import os
import re
import time
import codecs
from lxml import etree
from collections import defaultdict

#************************************#
# Disambiguation - Brill             #
#************************************#


class Transformation:
        """
        This is created merely for storing information.
        """

        def __init__(self):
            self.score = 0
            self.rule = u''
            self.meta = ''


class BrillTrainer:
    """
    Part of Speech Disambiguation with Transformation-Based Learning.
    Has four templates checking 1 word or tag before or after the current word.
    Initializes with a directory with corpus files for generating transformations and ending of the files.
    """

    nums = 0
    orderedList = []
    frequencies = defaultdict(int)

    def __init__(self):
        print "BrillTrainer instance created."
        self.corpus = []
        self.changes = 0

    def make_POS_file(self, path, extension=".xhtml", printing=False):
        """
        Takes a directory with corpus xhtml-files and makes one huge txt out of all texts.
        All words in the united document have POS-tags.

        path: unicode string containing the path to the directory where the corpus files are stored
        extension: unicode string containing the ending of the filename, e.g. '.xhtml' or 'cheese.txt',
                   this helps to identify files that need to be searched
        printing: True or False,
                  False by default,
                  if the value is True, the unified POS-tagged document is printed to file *corpus.txt*
        """
        self.nums = 0
        print 'BrillTrainer instance. Creating txt version of corpus with POS-tags...'
        for root, dirs, files in os.walk(path):
            for fname in files:
                if fname.endswith(extension):
                    self.transform_file(os.path.join(root, fname))
                    print '    ', fname, 'found %s words so far' % self.nums
        print 'Corpus created.\r\n'
        if printing:
            fOut = codecs.open('corpus.txt', 'a', 'utf-8-sig')
            fOut.write('\r\n'.join(self.corpus))
            fOut.close()

    def transform_file(self, fname):
        """
        Takes one file and adds its content to the unified document.
        """
        root = etree.parse(fname).getroot()  # get a text from the corpus
        for se in root[1]:
            sent = u''
            for w in xrange(len(se)):
                curWord = se[w][-1].tail
                if curWord is None:
                    curWord = ''
                new_x = [ana for ana in se[w]]
                for i in xrange(len(se[w])):  # ==for ana in word:
                    se[w].remove(se[w][0])  # deleted all ana from the tree
                for i in xrange(len(new_x)):
                    try:
                        new_x[i] = new_x[i].attrib['gr']
                        if new_x[i].startswith("PRON") or new_x[i].startswith("V"):
                            new_x[i] = ':'.join(new_x[i].split(',')[:2])
                        else:
                            new_x[i] = new_x[i].split(',')[0]
                        new_x[i] = re.sub(r"\?", "", new_x[i])
                    except:
                        new_x[i] = 'ND'
                new_x = list(set(new_x))
                tag = "_".join(sorted(new_x))
                tag = re.sub("PREP_PRON:A", "PREP+PRON:A", tag)
                tag = re.sub("ADV_V", "ADV+V", tag)
                tag = re.sub("PRON_V", "PRON+V", tag)
                curWord += '/' + tag + ' '
                sent += curWord
                self.nums += 1
            self.corpus.append(sent)

    def run_brill(self, printRules=False, printCorp=False, maximum=500):
        """
        Starts brill disambiguation algorithm.
        Returns ordered list of transformations.

        printRules: True or False, False by default,
                  if the value is True, the list of transformations is printed to file *list-of-transformations.txt*
        printCorp: True or False, False by default,
                    if the value is True, the transformed POS-tagged document is printed to file
                    *corpus-transformed.txt*
        """
        corpus = self.corpus
        print 'Collecting transformations... ', time.asctime()
        templates = [(-1, 'tag'), (+1, 'tag'), (-1, 'word'), (+1, 'word')]
        while True:
            self.frequencies = self.freq(corpus)
            bestTransform = self.get_best_transform(templates)
            if not (bestTransform.score > 0):
                break
            corpus = self.apply_transformation(bestTransform, corpus)
            self.orderedList.append(bestTransform.rule)
            if len(self.orderedList) >= maximum:
                break
            if len(self.orderedList) % 100 == 0:
                print 'Found %s transformations so far.' % len(self.orderedList)
        print 'Ready. Collected all transformations.', time.asctime()
        print 'Found %s transformations.\r\n' % len(self.orderedList)
        if printRules:
            transformOut = codecs.open(u'list-of-transformations.txt', 'w', 'utf-8-sig')
            transformOut.write('\r\n'.join(self.orderedList))
            transformOut.close()
        if printCorp:
            corpusOut = codecs.open(u'corpus-transformed.txt', 'w', 'utf-8-sig')
            corpusOut.write('\r\n'.join(corpus))
            corpusOut.close()
        return self.orderedList

    def get_best_transform(self, templates):
        """
        Iterates over all templates and returns the best transformation for the current state of the corpus.
        """
        # print 'function get_best_transform', time.asctime()
        best = Transformation()
        for template in templates:
            curTransform = self.get_best_instance(template)
            if curTransform.score > best.score:
                best = curTransform
        return best

    def open_fromTags(self):
        # print 'function open_fromTags', time.asctime()
        fromTags = []
        for k in self.frequencies[0].keys():
            if '_' in k:
                fromTags.append(k)
        return fromTags

    def generate_context(self, froms, template):
        # print 'function generate_context', time.asctime()
        contexts = []
        nums = template[0]  # -1 or +1
        types = template[1]  # word or tag
        if types == "word":
            if nums == 1:
                contexts = [(nums, types, w) for w in self.frequencies[1][froms].keys()]
            elif nums == -1:
                contexts = [(nums, types, w) for w in self.frequencies[3][froms].keys()]
        elif types == "tag":
            if nums == 1:
                contexts = [(nums, types, w) for w in self.frequencies[2][froms].keys()]
            elif nums == -1:
                contexts = [(nums, types, w) for w in self.frequencies[4][froms].keys()]
        return contexts

    def get_best_instance(self, template):
        # print 'function get_best_instance', time.asctime()
        best = Transformation()
        fromTags = self.open_fromTags()
        for fromTag in fromTags:  # fromTags = all types of POS-homonymy in our corpus, e.g. N_A_PRON
            toTags = fromTag.split('_')

            contexts = self.generate_context(fromTag, template)

            for toTag in toTags:  # toTags = parts of multiple tag, e.g. N, A, PRON for N_A_PRON
                for context in contexts:  # (nums, types, item)
                    arrZ = [(toTag, tag, context) for tag in toTags if tag != toTag]
                    bestZ = max(arrZ, key=self.estimate)
                    new_score = self.inContext(toTag, context) - self.estimate(bestZ)
                    if new_score > best.score:
                        # new_rule = u"Change " + fromTag + u" to " + toTag + u" if "
                        new_rule = fromTag + u"\t" + toTag + u"\t"
                        new_rule += str(bestZ[2][0]) + u'\t' + bestZ[2][1] + u'\t' + bestZ[2][2]
                        if new_rule not in self.orderedList:
                            best.rule = new_rule
                            best.score = new_score
                            best.meta = (fromTag, toTag, bestZ[2])
        return best

    def apply_transformation(self, bestTransform, corpus):
        # print 'function apply_transformation', time.asctime()
        nums, types, item = bestTransform.meta[2]
        fromTag = bestTransform.meta[0]
        toTag = bestTransform.meta[1]
        if types == 'word':
            types = 0  # word or tag
        elif types == 'tag':
            types = 1
        for se in xrange(len(corpus)):
            corpus[se] = corpus[se].split()
            for word in xrange(len(corpus[se])):
                w = corpus[se][word].split('/')
                if w[1] == fromTag:
                    if (nums == -1 and word != 0) or (nums == 1 and word != len(corpus[se]) - 1):
                        w_other = corpus[se][word + nums].split('/')
                        if w_other[types] == item:
                            corpus[se][word] = re.sub(fromTag, toTag, corpus[se][word])
            corpus[se] = ' '.join(corpus[se])
        return corpus

    def freq(self, corpus):
        # print 'function freq', time.asctime()
        d = defaultdict(int)
        word_next, word_prev, tag_next, tag_prev = defaultdict(dict), defaultdict(dict), defaultdict(
            dict), defaultdict(dict)
        for line in corpus:
            line = line.split()
            for word in xrange(len(line)):
                cur_w, cur_tag = line[word].split('/')
                d[cur_tag] += 1
                if d[cur_tag] == 1:
                    word_next[cur_tag], word_prev[cur_tag], tag_next[cur_tag], tag_prev[cur_tag] = defaultdict(
                        int), defaultdict(int), defaultdict(int), defaultdict(int)
            if word != len(line) - 1:
                w_next, t_next = line[word + 1].split('/')
                word_next[cur_tag][w_next] += 1
                tag_next[cur_tag][t_next] += 1
            if word != 0:
                w_prev, t_prev = line[word - 1].split('/')
                word_prev[cur_tag][w_prev] += 1
                tag_prev[cur_tag][t_prev] += 1
        return d, word_next, tag_next, word_prev, tag_prev

    def inContext(self, tag, context):
        #(tag, (num, types, item))
        nums = context[0]  # -1 or +1
        if context[1] == 'word':
            if nums == 1:
                d = self.frequencies[1]
            elif nums == -1:
                d = self.frequencies[3]
        elif context[1] == 'tag':
            if nums == 1:
                d = self.frequencies[2]
            elif nums == -1:
                d = self.frequencies[4]
        item = context[2]  # word or tag
        try:
            result = d[tag][item]
            # number of times a word unambiguously tagged with tag occurs in context in the corpus
        except:
            result = 0
        return result

    def estimate(self, tup):
        # print 'function estimate', time.asctime()
        toTag, tag, context = tup
        fY, fZ = self.frequencies[0][toTag], self.frequencies[0][tag]
        contextZC = self.inContext(tag, context)
        if fZ == 0:
            return 0
        else:
            return float(fY) / fZ * contextZC

    #APPLYING BRILL

    def start_apply(self, path, extension=".xhtml", rules=''):
        fileNum = 1
        if rules != '':
            rules = self.open_transformations(rules)
        else:
            rules = self.orderedList
        print 'Applying learned transformations to directory %s...' % path
        for root, dirs, files in os.walk(path):
            for fname in files:
                if fname.endswith(extension):
                    p = os.path.join(root, fname)
                    print 'Processing %s , %s...' % (p, fileNum),
                    self.apply_it(p, rules)
                    fileNum += 1
        print 'Total number of changes: %s' % self.changes

    def open_transformations(self, path):
        transFile = codecs.open(path, 'r', 'utf-8-sig')
        orderedList = []
        for line in transFile:
            line = line.strip()
            orderedList.append(line)
        return orderedList

    def transform_anas(self, new_x):
        arr = []
        for i in range(len(new_x)):
            try:
                a = new_x[i].attrib['gr']
                if a.startswith("PRON") or a.startswith("V"):
                    a = ':'.join(a.split(',')[:2])
                else:
                    a = a.split(',')[0]
                a = re.sub(r"\?", "", a)
            except:
                a = 'ND'
            arr.append(a)
        arr = list(set(arr))
        tag = "_".join(sorted(arr))
        tag = re.sub("PREP_PRON:A", "PREP+PRON:A", tag)
        tag = re.sub("ADV_V", "ADV+V", tag)
        tag = re.sub("PRON_V", "PRON+V", tag)
        # print tag
        return tag

    def get_toTag(self, gr):
        if gr.startswith("PRON"):
            gr = ':'.join(gr.split(',')[:2])
        else:
            gr = gr.split(',')[0]
        return gr

    def apply_it(self, path, rules):
        changes = 0
        root = etree.parse(path).getroot()  # get a text from the corpus
        for t in rules:
            fromTag, toTag, position, types, context = t.split('\t')
            position = int(position)
            for se in root[1]:
                for w in range(len(se)):
                    new_x = [ana for ana in se[w]]
                    cur_w = new_x[-1].tail  # current word
                    for i in xrange(len(se[w])):  # ==for ana in word:
                        se[w].remove(se[w][0])  # deleted all ana from the tree
                    if len(new_x) > 1:
                        a = new_x
                        tag = self.transform_anas(a)
                        if tag == fromTag:
                            try:
                                if types == 'tag':
                                    other = self.transform_anas([ana for ana in se[w + position] if w + position != -1])
                                elif types == 'word':
                                    other = [ana for ana in se[w + position] if w + position != -1][-1].tail
                                if other == context:
                                    new_x2 = [ana for ana in new_x if
                                              ana.attrib['gr'].startswith(toTag.replace(':', ','))]
                                    changes += 1
                                    for x in new_x2:
                                        x.tail = None
                                        se[w].append(x)
                            except IndexError:
                                pass
                            except AttributeError:
                                print [ana for ana in se[w]][-1].tail
                    if len(se[w]) == 0:
                        for i in new_x:
                            se[w].append(i)
                    else:
                        se[w][-1].tail = cur_w

        out = etree.tostring(root, pretty_print=True, encoding=unicode)
        fOut = codecs.open(path, 'w', 'utf-8-sig')
        fOut.write(out)
        fOut.close()
        self.changes += changes
        print "%s changes in file, %s changes in total" % (changes, self.changes)


m = BrillTrainer()

# m.make_POS_file(u'C:\\Users\\asus\\PycharmProjects\\yiddish\\yiddish_parsed_cases')

# m.run_brill(printRules=True, maximum=300)

m.start_apply(u'C:\\Users\\asus\\PycharmProjects\\yiddish\\yiddish_parsed_cases_run_brill\\acc',
              rules='C:\\Users\\asus\\PycharmProjects\\yiddish\\Ultimate\\list-of-transformations.txt')