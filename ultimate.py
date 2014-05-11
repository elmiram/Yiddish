# -*- coding = utf-8 -*-

# Term Paper Project: Automatic Disambiguation in the Yiddish National Corpus <web-corpora.net/YNC/search/>
# 2013-2014
# Project Part: Disambiguation Algorithms and Techniques
# Author: Elmira Mustakimova <egmustakimova_2@edu.hse.ru>
#         2nd year student at HSE NRU Dept. of Linguistics Moscow
# Academic Advisor: Timofey Arkhangelskiy


"""
These are some codes for morphological ambiguity resolution in the Corpus of Yiddish.

I still haven't written any nice description here.
"""

__author__ = 'elmira'

import os
import re
import time
import codecs
from lxml import etree
from collections import defaultdict


#************************************#
# Disambiguation - Bigrams           #
#************************************#

class GoodBigramsTrainer:
    """
    Disambiguating texts with bigrams.
    GoodBigramsTrainer searches corpus with homonimy and collects statistical information about non-ambiguous bigrams.
    Then it is possible to use this information to cope with the resting homonimy.
    """

    goodBigrs = []

    def __init__(self, path, extension=".xhtml", printing=False):
        """
        Starts the search.

        path: unicode string containing the path to the directory where the corpus files are stored
        extension: unicode string containing the ending of the filename, e.g. '.xhtml' or 'cheese.txt',
                   this helps to identify files that need to be searched
        printing: True or False,
                  False by default,
                  if the value is True, all bigrams are printed to file *good_bigrams.txt*
        """
        self.changes = 0
        print 'Collecting good bigrams...'
        for root, dirs, files in os.walk(path):
            for fName in files:
                if fName.endswith(extension):
                    self.search_file(os.path.join(root, fName))
        print 'Good bigrams collected. Total: %s bigrams.\r\n' %(len(self.goodBigrs))
        if printing:
            f = codecs.open(u"good_bigrams.txt", "a", "utf-8")
            f.write('\r\n'.join(self.goodBigrs))
            f.close()

    def search_file(self, fName):
        """
        Performs the search of good bigrams in a given file fName.
        Writes the result to the array goodBigrs.
        """
        try:
            root = etree.parse(fName).getroot()
            gram = []
            for se in root[1]:
                for w in range(len(se) - 1):
                    nextWord = [ana for ana in se[w + 1] if "lex" in ana.attrib]  # not counting empty tags
                    curWord = [ana for ana in se[w] if "lex" in ana.attrib]
                    nextPoS = set([x.attrib["gr"].split(u',')[0] for x in nextWord])
                    curPoS = set([x.attrib["gr"].split(u',')[0] for x in curWord])
                    if (curPoS == {"V", "ADV"} or curPoS == {"PREP", "PRON"} or curPoS == {"V", "PRON"}) and len(curWord) == 2:  # treating special cases right
                        curResult = True
                    else:
                        curResult = False
                    if (nextPoS == {"V", "ADV"} or nextPoS == {"PREP", "PRON"} or nextPoS == {"V", "PRON"}) and len(nextWord) == 2:
                        nextResult = True
                    else:
                        nextResult = False
                    if len(nextWord) == 1 or nextResult:
                        if len(curWord) == 1 or curResult:
                            gram.append((nextWord[-1].tail, nextWord[-1].attrib[u'gr'],
                                         curWord[-1].tail, curWord[-1].attrib[u'gr']))
            for i in gram:
                bigramString = i[0] + ' ' + i[1] + ' ' + i[2] + ' ' + i[3]
                self.goodBigrs.append(bigramString)

        except:
            print "Class - GoodBigrams; function - search_file(filename); fail at %s" % fName

    def count_freq(self, printing=False):
        """
        Opens array with bigrams and counts frequency for each bigram.
        Returns a dictionary { bigram:frequency }.

        printing: True or False,
                  False by default,
                  if the value is True, all bigrams with frequencies are printed to file
                  *good_bigrams_frequency_morpho.txt*
        """
        print 'Counting frequencies...\r\n'
        d = defaultdict(int)
        for line in self.goodBigrs:
            line = line.split()
            k = line[3] + ' ' + line[1]
            # if k not in d:
            #     print k
            d[k] += 1
        if printing:
            f2 = codecs.open(u"good_bigrams_frequency_morpho.txt", "w", "utf-8")
            # writes "ana1 ana2" freq
            for key in reversed(sorted(d.keys(), key=lambda k: d[k])):
                f2.write(key + ' ' + str(d[key]) + u'\r\n')
            f2.close()
        return d

    def get_rules(self, freqs):
        """
        Opens dictionary with frequencies and rearranges it into a dictionary of rules.

        Returns dictionary:
        dictionary = {anaOfWord1:[(anaOfWord2,freq),(anaOfWord3,freq),...],
                      anaOfWord1:[(anaOfWord2,freq),(anaOfWord3,freq),...],
                      anaOfWord1:[(anaOfWord2,freq),(anaOfWord3,freq),...],}
        """
        d = defaultdict(list)
        for key in freqs.iterkeys():
            items = key.split()
            items = (items[0], items[1], freqs[key])  # ana1 ana2 freq
            d[items[0]].append((items[1], int(items[2])))
        return d

    def check_for_special_cases(self, new_x):
        stay = ""
        decide = ""
        wordClasses = [x.attrib["gr"].split(u',')[0] for x in new_x]
        try_set = set(wordClasses)
        if len(try_set) == 2:
            if try_set == {"V", "ADV"}:
                stay = "ADV"
            elif try_set == {"PREP", "PRON"}:
                 stay = "PREP"
            elif try_set == {"V", "PRON"}:
                stay = "PRON"
            else:
                return None
            ambiguous = [x for x in new_x if stay not in x.attrib["gr"]]
            sure = [x for x in new_x if stay in x.attrib["gr"]]
            if len(ambiguous) == 1:
                decide = "continue"
            return stay, decide, ambiguous, sure
        else:
            return None

    def get_corpora(self, fname, check):

        root = etree.parse(fname).getroot()  # get a text from the corpus

        changes = 0

        for se in root[1]:
            for w in range(len(se)):
                var = 0
                max_f = 0
                curWordAnas = [ana for ana in se[w]]  # array contains all anas of current word
                if len(curWordAnas) > 1:  # if the word has multiple anas
                    cur_w = curWordAnas[-1].tail  # current word
                    answer = self.check_for_special_cases(curWordAnas)
                    for i in xrange(len(se[w])):  # ==for ana in word:
                        se[w].remove(se[w][0])  # deleted all ana from the tree
                    if answer is not None:
                        if answer[1] == "continue":
                            continue
                        curWordAnas = answer[2]  # only ambiguous anas
                        for i in answer[3]:
                            se[w].append(i)
                            var += 1
                    # At this point, we added all ana containing PREP in PRON\PREP complexes
                    # or all ana containing AVD in verbs with prefixes like aroysgeyn.
                    # hence - need to disambiguate the resting part
                    try:
                        prevAnaList = [ana for ana in se[w - 1] if "lex" in ana.attrib]
                        if len(prevAnaList) == 1:  # if the previous word has one ana
                            for ana in se[w - 1]:
                                prevWordAna = ana.attrib[u'gr'] # ana1
                                # got ana of the previous word
                            try:
                                d = {}
                                for possibleNextAna in check[prevWordAna]:
                                    # look for all possible anas after the previous one
                                    for analysis in curWordAnas:
                                        if possibleNextAna[0] == analysis.attrib[u'gr']:
                                            # search in the dictionary, find anas suggested by morphological parser
                                            d[possibleNextAna[0]] = (possibleNextAna[1], analysis)  # write to the dictionary
                                for x in d.keys():  # searching the most frequent ana
                                    if d[x][0] > max_f:
                                        max_f = d[x][0]
                                for x in d.keys():
                                    if d[x][0] == max_f:
                                        d[x][1].tail = None
                                        se[w].append(d[x][1])
                                        #write best ana
                            except KeyError:
                                # print "No key in dictionary"
                                pass
                    except KeyError:
                        # print "No previous word"
                        pass
                    if len(se[w]) == var:
                        for i in curWordAnas:
                            se[w].append(i)
                    else:
                        se[w][-1].tail = cur_w
                        changes += 1
        self.changes += changes
        print "Made %s changes. Total: %s changes." %(changes, self.changes)

        return etree.tostring(root, pretty_print=True, encoding=unicode)

    def start_apply(self, path, freq, extension=".xhtml"):
        check = self.get_rules(freq)  # dictionary
        for root, dirs, files in os.walk(path):
            for fname in files:
                if fname.endswith(extension):
                    print "Applying bigrams to %s" % os.path.join(root, fname)
                    new_text = self.get_corpora(os.path.join(root, fname), check)
                    f2 = codecs.open(os.path.join(root, fname), 'w', 'utf-8')
                    header = '<?xml version="1.0" encoding="utf-8"?>\r\n'
                    f2.write(header)
                    f2.write(new_text)
                    f2.close()


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


#************************************#
# Disambiguation - Viterbi           #
#************************************#

class HMM:

    def __init__(self, path, extension='.xhtml', printing=False, ambig=True):

        """
        Creates a Hidden Markov Model.
        Starts the search.

        path: unicode string containing the path to the directory where the corpus files are stored
        extension: unicode string containing the ending of the filename, e.g. '.xhtml' or 'cheese.txt',
                   this helps to identify files that need to be searched
        printing: True or False,
                  False by default,
                  if the value is True, all bigrams are printed to file *good_bigrams.txt*
        ambig: True or False,
               True by default, searches only non ambiguous unigrams and bigrams
               if the value is False, assumes that the corpus is manually disambiguated and each word has correct tag
        """
        self.states = defaultdict(int)
        self.observations = defaultdict(int)
        self.emissionProbabilities = defaultdict(dict)
        self.transitionProbabilities = defaultdict(dict)
        self.startProbabilities = defaultdict(int)
        self.starts = 0

        print 'Collecting statistics...'
        if ambig:
            count = 0
            for root, dirs, files in os.walk(path):
                for fName in files:
                    if fName.endswith(extension):
                        count += 1
                        self.search_file_ambig(os.path.join(root, fName))
                        if count % 300 == 0:
                            print "Processed %s files." % count
        elif ambig is False:
            count = 0
            for root, dirs, files in os.walk(path):
                for fName in files:
                    if fName.endswith(extension):
                        count += 1
                        self.search_file_not_ambig(os.path.join(root, fName))
                        if count % 100 == 0:
                            print "Processed %s files." % count
        # print 'Good bigrams collected. Total: %s bigrams.\r\n' % (len(self.goodBigrs))
        print 'Collected %s tags' % len(self.states)
        print 'Collected %s words' % len(self.observations)
        print 'Collecting emission and transition probabilities...'
        self.collect_emission()
        self.collect_transition()
        self.collect_start()
        if printing:
            self.printing()

    def search_file_ambig(self, fName):
        """
        Performs the search of good bigrams in a given file fName.
        Writes the result to the array goodBigrs.
        """
        # try:
        root = etree.parse(fName).getroot()
        for se in root[1]:
            for w in range(len(se) - 1):

                curWord = [ana for ana in se[w] if "lex" in ana.attrib]
                curWord1 = [ana for ana in se[w]]
                curW = curWord1[-1].tail
                self.observations[curW] += 1
                curResult = False
                if curWord != []:
                    curPoS = set([x.attrib["gr"].split(u',')[0] for x in curWord])
                    if (curPoS == {"V", "ADV"} or curPoS == {"PREP", "PRON"} or curPoS == {"V", "PRON"}) and len(
                            curWord) == 2:  # treating special cases right
                        curResult = True

                    if len(curWord) == 1 or curResult:

                        try:
                            curT = curWord[-1].attrib["gr"]
                            if curT != '':
                                self.states[curT] += 1
                                try:
                                    self.emissionProbabilities[curT][curW] += 1
                                except KeyError:
                                    self.emissionProbabilities[curT][curW] = 1
                        except KeyError:
                            pass

                nextWord = [ana for ana in se[w + 1] if
                            "lex" in ana.attrib]  # not counting empty tags
                nextWord1 = [ana for ana in se[w + 1]]
                nextW = nextWord1[-1].tail
                if w == len(se) - 1:
                    self.observations[nextW] += 1
                nextResult = False
                if nextWord != []:
                    nextPoS = set([x.attrib["gr"].split(u',')[0] for x in nextWord])
                    if (nextPoS == {"V", "ADV"} or nextPoS == {"PREP", "PRON"} or nextPoS == {"V", "PRON"}) and len(
                            nextWord) == 2:
                        nextResult = True
                    if len(nextWord) == 1 or nextResult:
                        nextT = nextWord[-1].attrib["gr"]

                        if w == len(se) - 1:
                            if nextT != '':
                                self.states[nextT] += 1

                try:
                    if (len(nextWord) == 1 or nextResult) and nextT != '' and curT != '':
                        if len(curWord) == 1 or curResult:
                            try:
                                self.transitionProbabilities[curT][nextT] += 1
                            except KeyError:
                                self.transitionProbabilities[curT][nextT] = 1
                except UnboundLocalError:
                    pass

        # except:
        #     print "Class - HMM; function - search_file_ambig(filename); fail at %s" % fName

    def search_file_not_ambig(self, fName):
        """
                Performs the search of good bigrams in a given file fName.
                Writes the result to the array goodBigrs.
                """
        # try:
        root = etree.parse(fName).getroot()
        for se in root[1]:
            for w in range(len(se) - 1):
                curWord = [ana for ana in se[w] if "lex" in ana.attrib]
                if curWord != []:
                    curW = curWord[-1].tail
                    self.observations[curW] += 1
                    try:
                        curT = curWord[-1].attrib["gr"]
                        if curT != '':
                            self.states[curT] += 1
                            try:
                                self.emissionProbabilities[curT][curW] += 1
                            except KeyError:
                                self.emissionProbabilities[curT][curW] = 1
                    except:
                        pass

                nextWord = [ana for ana in se[w + 1] if
                            "lex" in ana.attrib]  # not counting empty tags
                if nextWord != []:
                    nextW = nextWord[-1].tail
                    nextT = nextWord[-1].attrib["gr"]
                    if w == len(se) - 1:
                        self.observations[nextW] += 1
                        if nextT != '':
                            self.states[nextT] += 1

                if nextWord != [] and curWord != [] and nextT != '' and curT != '':

                    try:
                        self.transitionProbabilities[curT][nextT] += 1
                    except KeyError:
                        self.transitionProbabilities[curT][nextT] = 1

                            # except:
                            #     print "Class - HMM; function - search_file_ambig(filename); fail at %s" % fName

    def collect_emission(self):
        '''
        Turns the values in the dictionary into probabilities.
        Simply divides each value by the frequency of the corresponding tag.
        '''
        print "Collect emission probabilities B..."
        count = 0
        for state in self.states:
            if state not in self.emissionProbabilities:
                self.emissionProbabilities[state] = {}
            for i in self.emissionProbabilities[state]:
                self.emissionProbabilities[state][i] += 1
                self.emissionProbabilities[state][i] /= (self.states[state] + len(self.observations.keys()))

    def collect_transition(self):
        '''
        Turns the values in the dictionary into probabilities.
        Simply divides each value by the frequency of the corresponding tag.
        '''
        print "Collect transition probabilities A..."
        for state in self.states:
            if state not in self.transitionProbabilities:
                self.transitionProbabilities[state] = {}
            for i in self.transitionProbabilities[state]:
                self.transitionProbabilities[state][i] += 1
                self.transitionProbabilities[state][i] /= (self.states[state] + len(self.states.keys()))

    def collect_start(self):
        '''
        Turns the values in the dictionary into probabilities.
        Simply divides each value by the frequency of the corresponding tag.
        '''
        print "Collect start probabilities Q..."
        if self.startProbabilities == {}:
            for tag in self.states:
                self.startProbabilities[tag] = 1/len(self.states)
        else:
            for tag in self.startProbabilities:
                self.startProbabilities[tag] /= self.starts

    def printing(self):
        print "Printing data to file..."
        f = codecs.open(u"printing_states.txt", "w", "utf-8")
        for key in self.states:
            f.write(key + '\r\n')
        f.close()
        f = codecs.open(u"printing_starts.txt", "w", "utf-8")
        for key in self.startProbabilities:
            f.write(key + '  ' + str(self.startProbabilities[key]) + '\r\n')
        f.close()
        f = codecs.open(u"printing_observations.txt", "w", "utf-8")
        out = '\r\n'.join(self.observations.keys())
        f.write(out)
        f.close()
        f = codecs.open(u"printing_emission.txt", "w", "utf-8")
        for k in self.emissionProbabilities:
            f.write(k + '\r\n')
            for w in reversed(
                    sorted(self.emissionProbabilities[k].keys(), key=lambda c: self.emissionProbabilities[k][c])):
                f.write('ooo>  ' + str(self.emissionProbabilities[k][w]) + '    ' + w + '\r\n')
        f.close()
        f = codecs.open(u"printing_transition.txt", "w", "utf-8")
        for k in self.transitionProbabilities:
            f.write(k + '\r\n')
            for w in reversed(
                    sorted(self.transitionProbabilities[k].keys(), key=lambda c: self.transitionProbabilities[k][c])):
                f.write('    ' + str(self.transitionProbabilities[k][w]) + '    ' + w + '\r\n')
        f.close()

class ViterbiTrainer:

    def __init__(self, hmm, path, extension='.xhtml'):
        print "Run Viterbi Algorithm."
        self.states = hmm.states.keys()
        self.states2 = hmm.states
        self.trans_p = hmm.transitionProbabilities
        self.emit_p = hmm.emissionProbabilities
        self.start_p = hmm.startProbabilities
        self.observ = hmm.observations.keys()
        self.changes = 0
        count = 0
        for root, dirs, files in os.walk(path):
            for fName in files:
                if fName.endswith(extension):
                    count += 1
                    self.find_sents(os.path.join(root, fName))
                    print "Applied ViterbiTrainer to %s, %s files." % (os.path.join(root, fName), count)

    def find_sents(self, f):
        changes = 0
        root = etree.parse(f).getroot()
        f2 = codecs.open(u'res2.txt', 'a', 'utf-8')
        for se in root[1]:
            sentWords = []
            sent = []
            for w in range(len(se)):
                curWord = [ana for ana in se[w]]
                curW = curWord[-1].tail
                sentWords.append([(ana.attrib['gr'], ana) for ana in se[w]
                                   if 'gr' in ana.attrib and ana.attrib['gr'] != ''])
                sent.append(curW)
            tags = self.viterbi(sent)  # found most probable sequence of tags
            k = zip(sent, tags)
            sentWords = self.delete_bad_tags(k, sentWords)
            for c in xrange(len(sent)):
                if c in sentWords:
                    if sentWords[c] != []:
                        for i in xrange(len(se[c])):  # ==for ana in word:
                            se[c].remove(se[c][0])  # deleted all ana from the tree
                        # print len(sentWords[c])
                        for e in sentWords[c]:
                            se[c].append(e)
                        se[c][-1].tail = sent[c]
                        changes += 1
            for (a, b) in k:
                f2.write(a + ' : ' + b + '\r\n')
            f2.write(u'***********************************************************\r\n')
        out = etree.tostring(root, pretty_print=True, encoding=unicode)
        f2.close()
        fOut = codecs.open(f, 'w', 'utf-8')
        fOut.write(out)
        fOut.close()
        self.changes += changes
        print "Made %s changes. Total: %s changes." % (changes, self.changes)

    def delete_bad_tags(self, k, sentWords):
        for a in range(len(k)):
            obs, tag = k[a]
            if sentWords[a] != []:
                for gr, ana in sentWords[a]:
                    if gr != tag:
                        gr = 'bad'
        d = {}
        for e in range(len(sentWords)):
            if sentWords[e] != []:
                for p in range(len(sentWords[e])):
                    if sentWords[e][p][0] != 'bad':
                        sentWords[e][p][1].tail = None
                        if e in d:
                            d[e].append(sentWords[e][p][1])
                        else:
                            d[e] = [sentWords[e][p][1]]
        return d

    def viterbi(self, obs):
        V = [{}]
        path = {}

        d = {}
        for y in self.states:
            if obs[0] not in self.emit_p[y]:
                self.emit_p[y][obs[0]] = 1 / (self.states2[y] + len(self.observ))
            d[y] = (self.start_p[y] * self.emit_p[y][obs[0]])
        V = [d]
        path = {y:[y] for y in self.states}

        for t in range(1, len(obs)):
            V.append({})
            newpath = {}

            for y in self.states:
                ar = []
                for y0 in self.states:
                    if obs[t] not in self.emit_p[y]:
                        self.emit_p[y][obs[t]] = 1 / (self.states2[y] + len(self.observ))
                    if y not in self.trans_p[y0]:
                        self.trans_p[y0][y] = 1 / (self.states2[y] + len(self.states))
                    ar.append((V[t - 1][y0] * self.trans_p[y0][y] * self.emit_p[y][obs[t]], y0))
                (prob, state) = max(ar)
                V[t][y] = prob
                newpath[y] = path[state] + [y]
            path = newpath
        n = 0
        if len(obs) != 1:
            n = t

        (prob, state) = max((V[n][y], y) for y in self.states)
        return path[state]