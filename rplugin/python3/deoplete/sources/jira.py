"""
This is JIRA source plugin for deoplete. It completes JIRA issue numbers from
a cache file.

# Install:

1. Copy the file to $HOME/.vim/bundle/deoplete.nvim/rplugin/python3/deoplete/sources/
2. pip install regex (https://pypi.python.org/pypi/regex supports cool fuzzy matching)

# Make sure cache is generated in crontab by this command:

$HOME/bin/jira -u <user> ls -p UOP | sed -e 's/://' -e 's/ \+/ /g' | sort -r -V > jira.candidates.txt
(uses https://github.com/Netflix-Skunkworks/go-jira)
"""
from .base import Base

#import re
import os
from os.path import expanduser, expandvars
import regex as re
from time import strftime, time
from pprint import pformat

from deoplete.util import load_external_module
current = __file__
load_external_module(current, 'sources/jira_matcher')
from jira_matcher import MyJiraMatcher, JIRA_PATTERN, CANDIDATES_FILENAME


def measure(func):

    def deco(*args, **kwargs):
        a = time()
        result = func(*args, **kwargs)
        b = time()
        log('%s running time: %s' % (func.__name__, b - a))
        return result

    return deco


def log(msg):
    if os.environ.get('NVIM_PYTHON_LOG_LEVEL', None) != 'DEBUG':
        return
    timestamp = strftime("%Y-%m-%d %H:%M:%S")
    with open('/tmp/jira.completer.log', 'a+') as file_object:
        file_object.write('%s ' % timestamp + msg + '\n')


# Taken from: https://github.com/amjith/fuzzyfinder
def fuzzyfinder(text, collection):
    suggestions = []
    text = str(text) if not isinstance(text, str) else text
    #pat = '.*?'.join(map(re.escape, text))
    pat = '(?:%s){i}' % text
    regex = re.compile(pat, re.IGNORECASE | re.BESTMATCH)
    for item in collection:
        r = regex.search(item)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    return [z for _, _, z in sorted(suggestions)]


def read_candidates(filename):
    with open(filename) as file_object:
        lines = file_object.readlines()
        candidates = [str(line.strip()) for line in lines]
        return candidates


# class MyMatcher(object):
#     def __init__(self, prefixes):
#         self._prefixes = prefixes
#
#     def get_complete_str(self, context):
#         # Cut off and remember RT prefix
#         complete_str = context['complete_str']
#         for prefix in self._prefixes:
#             if complete_str.startswith(prefix):
#                 return prefix, complete_str[len(prefix):]
#         else:
#             return None, None
#
#     def get_complete_position(self, context):
#         match = RX_RT.search(context['input'])
#         pos = match.start() if match else -1
#         return pos
#
#     def load_raw_candidates(self, filename, complete_str):
#         # Read candidates, cut off http part and fuzzy match by long description
#         candidates_from_file = self.read_candidates(filename)
#         #candidates_from_file = self.modify_candidates(candidates_from_file)
#         candidates_without_http = candidates_from_file
#         # for candidate in candidates_from_file:
#         #     pos = candidate.find(' http')
#         #     candidates_without_http.append(candidate[:pos] if pos != -1 else candidate)
#
#         if complete_str is not None and len(complete_str):
#             filtered_candidates = self.filter_raw_candidates(complete_str, candidates_without_http)
#         else:
#             filtered_candidates = sorted(candidates_without_http, reverse=True)
#         return filtered_candidates
#
#     def read_candidates(self, filename):
#         with open(filename) as file_object:
#             lines = file_object.readlines()
#             candidates = [str(line.strip()) for line in lines]
#             return candidates
#
#     def modify_candidates(self, raw_candidates):
#         result = []
#         for candidate in raw_candidates:
#             parts = candidate.split()
#             line = parts[0:1] + parts[2:]
#             result.append(' '.join(line))
#         return result
#
#     def prepare_deoplete_candidates(self, prefix, raw_candidates):
#         result = []
#         for x in raw_candidates:
#             # short = prefix + x[:6]
#             # long_ = prefix + x
#             short = x[:x.find(' ')] #prefix + x[:6]
#             long_ = x #prefix + x
#             item = {'word': short, 'abbr': long_}
#             result.append(item)
#         return result
#
#     def check_match(self, pattern, text):
#         pattern = str(pattern) if not isinstance(pattern, str) else pattern
#         regex = re.compile('(?:%s){i}' % pattern, re.IGNORECASE | re.BESTMATCH)
#         r = regex.search(str(text))
#         return True if r else False
#
#     def filter_raw_candidates(self, pattern, raw_candidates):
#         pattern = str(pattern) if not isinstance(pattern, str) else pattern
#         suggestions = []
#         for item in raw_candidates:
#             if self.check_match(pattern, item):
#                 suggestions.append(item)
#         return sorted(suggestions)
#
#     def filter_deoplete_candidates(self, pattern, deoplete_candidates):
#         pattern = str(pattern) if not isinstance(pattern, str) else pattern
#         suggestions = []
#         for item in deoplete_candidates:
#             if self.check_match(pattern, item['abbr']):
#                 suggestions.append(item)
#         return suggestions


class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'jira'
        #self.kind = 'keyword'
        self.mark = '[JIRA]'
        self.min_pattern_length = 3
        self.matchers = []
        self.sorters = []
        self.max_menu_width = 120
        self.max_abbr_width = 120
        self.input_pattern = JIRA_PATTERN

        self.mymatcher = MyJiraMatcher(prefixes=['UOP-', 'UOP'])
        log('CONSTRUCTOR %s' % self.input_pattern)

    def get_complete_position(self, context):
        log('GET POS: ' + pformat(context))
        pos = self.mymatcher.get_complete_position(context)
        log('GET POS RESULT: ' + pformat(pos))
        return pos

    @measure
    def gather_candidates(self, context):
        log('GATHER: ' + pformat(context))
        prefix, complete_str = self.mymatcher.get_complete_str(context)
        log('COMPLETE STR: %s' % complete_str)
        if prefix is None:
            return []

        filtered_candidates = self.mymatcher.load_raw_candidates(
            CANDIDATES_FILENAME, complete_str)

        result = self.mymatcher.prepare_deoplete_candidates(
            prefix, filtered_candidates)
        log('GATHER CAND: ' + str(result))
        log('GATHER CAND COUNT: ' + str(len(result)))
        return result

    @measure
    def on_post_filter(self, context):
        log('POST FILTER: ' + pformat(context))
        prefix, complete_str = self.mymatcher.get_complete_str(context)
        log('POST FILTER PREFIX: ' + str(prefix) + ' COMPLETE_STR ' + str(complete_str))
        log('POST FILTER types: %s %s' % (type(prefix), type(complete_str)))
        candidates = context['candidates']
        result = candidates
        if complete_str is not None:
            result = self.mymatcher.filter_deoplete_candidates(
                complete_str, candidates)
        log('POST FILTER RESULT: ' + pformat(context))
        log('POST FILTER RESULT LEN: ' + str(len(context)))
        return result
