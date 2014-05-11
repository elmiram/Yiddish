# -*- coding = utf-8 -*-

from __future__ import division
__author__ = 'elmira'


import os
import codecs
from lxml import etree
from collections import defaultdict

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

                        if 'gr' in curWord[-1].attrib and curWord[-1].attrib["gr"] != '':
                            if curWord[-1].attrib["gr"].startswith("V") or curWord[-1].attrib["gr"].startswith("PRON"):
                                curWord[-1].attrib["gr"] = curWord[-1].attrib["gr"].replace(',hebrew', '')
                                curT = ':'.join(curWord[-1].attrib["gr"].split(u',')[:2])
                            else:
                                curT = curWord[-1].attrib["gr"].split(u',')[0].strip('?')
                            self.states[curT] += 1
                            try:
                                self.emissionProbabilities[curT][curW] += 1
                            except KeyError:
                                self.emissionProbabilities[curT][curW] = 1
                        # except KeyError:
                        #     pass

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
                        if 'gr' in nextWord[-1].attrib and nextWord[-1].attrib["gr"] != '':
                            if nextWord[-1].attrib["gr"].startswith("V") or nextWord[-1].attrib["gr"].startswith("PRON"):
                                nextWord[-1].attrib["gr"] = nextWord[-1].attrib["gr"].replace(',hebrew', '')
                                nextT = ':'.join(nextWord[-1].attrib["gr"].split(u',')[:2])
                            else:
                                nextT = nextWord[-1].attrib["gr"].split(u',')[0].strip('?')

                        if w == len(se) - 1:
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
                        if 'gr' in curWord[-1].attrib and curWord[-1].attrib["gr"] != '':
                            if curWord[-1].attrib["gr"].startswith("V") or curWord[-1].attrib["gr"].startswith("PRON"):
                                curWord[-1].attrib["gr"] = curWord[-1].attrib["gr"].replace(',hebrew', '')
                                curT = ':'.join(curWord[-1].attrib["gr"].split(u',')[:2])
                            else:
                                curT = curWord[-1].attrib["gr"].split(u',')[0].strip('?')
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
                    if 'gr' in nextWord[-1].attrib and nextWord[-1].attrib["gr"] != '':
                        if nextWord[-1].attrib["gr"].startswith("V") or nextWord[-1].attrib["gr"].startswith("PRON"):
                            nextWord[-1].attrib["gr"] = nextWord[-1].attrib["gr"].replace(',hebrew', '')
                            nextT = ':'.join(nextWord[-1].attrib["gr"].split(u',')[:2])
                        else:
                            nextT = nextWord[-1].attrib["gr"].split(u',')[0].strip('?')
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

    def make_pos_tags(selfself, arr):
        for x in range(len(arr)):
            for e in range(len(arr[x])):
                if arr[x][e][0].startswith("V") or arr[x][e][0].startswith("PRON"):
                    newGR = ':'.join(arr[x][e][0].split(u',')[:2])
                    arr[x][e] = (newGR, arr[x][e][1])
                else:
                    newGR =arr[x][e][0].split(u',')[0].strip('?')
                    arr[x][e] = (newGR, arr[x][e][1])
        return arr

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
            sentWords = self.make_pos_tags(sentWords)
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

        # Initialize base cases (t == 0)
        d = {}
        for y in self.states:
            if obs[0] not in self.emit_p[y]:
                self.emit_p[y][obs[0]] = 1 / (self.states2[y] + len(self.observ))
            d[y] = (self.start_p[y] * self.emit_p[y][obs[0]])
        V = [d]
        path = {y:[y] for y in self.states}

        # Run Viterbi for t > 0
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
            # Don't need to remember the old paths
            path = newpath
        n = 0           # if only one element is observed max is sought in the initialization values
        if len(obs) != 1:
            n = t
        # self.print_dptable(V)

        (prob, state) = max((V[n][y], y) for y in self.states)
        return path[state]

    def print_dptable(self, V):
        s = " " * 20 + " ".join(("%7d" % i) for i in range(len(V))) + "\n"
        for y in V[0]:
            if len(y) < 20:
                c = y + ' ' * (20 - len(y))
                s += "%.20s: " % c
            else:
                s += "%.20s: " % y
            s += " ".join("%.7s" % ("%f" % v[y]) for v in V)
            s += "\n"
        print(s)

## POS!!
m = HMM('C:\\Users\\asus\\PycharmProjects\\yiddish\\yiddish_parsed_cases', printing=True, ambig=True)

p = 'C:\\Users\\asus\\PycharmProjects\\yiddish\\yiddish_parsed_cases_run_viterbi'
v = ViterbiTrainer(m, p)