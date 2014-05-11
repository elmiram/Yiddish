# -*- coding = utf-8 -*-

# Term Paper Project: Automatic Disambiguation in the Yiddish National Corpus <web-corpora.net/YNC/search/>
# 2013-2014
# Project Part: Disambiguation with a Bigram Language Model
# Author: Elmira Mustakimova <egmustakimova_2@edu.hse.ru>
#         2nd year student at HSE NRU Dept. of Linguistics Moscow
# Academic Adviser: Timofey Arkhangelskiy

"""
Disambiguating texts with bigrams.

Step 1.
Create an instance of a GoodBigramsTrainer class. The class is initialized with the path to the corpus directory, the extension of the files ('.xhtml' by default), and a boolean literal for printing (this prints all the bigrams into a file, if True, otherwise, skips printing):
m = GoodBigramsTrainer('C:\\corpus')

Step 2.
Create frequencies of bigrams:
freqs = m.count_freq()

Step 3.
Apply the model to disambiguation. This requires the path to the corpus directory, the extension of the files and the frequencies, that we counted earlier:
m.start_apply('C:\\corpus', '.xhtml', freqs)


"""
__author__ = 'elmira'

import os
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


m = GoodBigramsTrainer('C:\\Users\\asus\PycharmProjects\yiddish\\yiddish_parsed_cases', printing=False)
freqs = m.count_freq(printing=False)
m.start_apply('C:\\Users\\asus\PycharmProjects\yiddish\\yiddish_parsed_cases_run_bigr\\acc', freqs)