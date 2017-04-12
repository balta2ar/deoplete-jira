
from os.path import expanduser, expandvars
import regex as re

#CANDIDATES_FILENAME = '/tmp/rt.candidates.txt'
#CANDIDATES_FILENAME = expandvars(expanduser('~/.cache/rt/rt.candidates.txt'))
CANDIDATES_FILENAME = expandvars(expanduser('~/.cache/rt/jira.candidates.txt'))
JIRA_PATTERN = r'UOP-?\w*$'
RX_RT = re.compile(JIRA_PATTERN, re.IGNORECASE)


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


class MyJiraMatcher(object):
    def __init__(self, prefixes):
        self._prefixes = prefixes

    def get_complete_str(self, context):
        # Cut off and remember RT prefix
        complete_str = context['complete_str']
        for prefix in self._prefixes:
            if complete_str.startswith(prefix):
                return prefix, complete_str[len(prefix):]
        else:
            return None, None

    def get_complete_position(self, context):
        match = RX_RT.search(context['input'])
        pos = match.start() if match else -1
        return pos

    def load_raw_candidates(self, filename, complete_str):
        # Read candidates, cut off http part and fuzzy match by long description
        candidates_from_file = self.read_candidates(filename)
        #candidates_from_file = self.modify_candidates(candidates_from_file)
        candidates_without_http = candidates_from_file
        # for candidate in candidates_from_file:
        #     pos = candidate.find(' http')
        #     candidates_without_http.append(candidate[:pos] if pos != -1 else candidate)

        if complete_str is not None and len(complete_str):
            filtered_candidates = self.filter_raw_candidates(complete_str, candidates_without_http)
        else:
            filtered_candidates = sorted(candidates_without_http, reverse=True)
            #filtered_candidates = candidates_without_http
        return filtered_candidates

    def read_candidates(self, filename):
        with open(filename) as file_object:
            lines = file_object.readlines()
            candidates = [str(line.strip()) for line in lines]
            return candidates

    def modify_candidates(self, raw_candidates):
        result = []
        for candidate in raw_candidates:
            parts = candidate.split()
            line = parts[0:1] + parts[2:]
            result.append(' '.join(line))
        return result

    def prepare_deoplete_candidates(self, prefix, raw_candidates):
        result = []
        for x in raw_candidates:
            # short = prefix + x[:6]
            # long_ = prefix + x
            short = x[:x.find(' ')] #prefix + x[:6]
            long_ = x #prefix + x
            item = {'word': short, 'abbr': long_}
            result.append(item)
        return result

    def make_regex(self, pattern):
        pattern = str(pattern) if not isinstance(pattern, str) else pattern
        regex = re.compile('(?:%s){i}' % pattern, re.IGNORECASE | re.BESTMATCH)
        return regex

    def check_match(self, regex, text):
        # pattern = str(pattern) if not isinstance(pattern, str) else pattern
        # regex = re.compile('(?:%s){i}' % pattern, re.IGNORECASE | re.BESTMATCH)
        r = regex.search(str(text))
        return (True, r) if r else (False, r)

    def filter_raw_candidates(self, pattern, raw_candidates):
        pattern = str(pattern) if not isinstance(pattern, str) else pattern
        regex = self.make_regex(pattern)
        suggestions = []
        for item in raw_candidates:
            match, r = self.check_match(regex, item)
            if match:
                suggestions.append((len(r.group()), r.start(), item))
        return [z for _, _, z in sorted(suggestions)]

    def filter_deoplete_candidates(self, pattern, deoplete_candidates):
        pattern = str(pattern) if not isinstance(pattern, str) else pattern
        regex = self.make_regex(pattern)
        suggestions = []
        for item in deoplete_candidates:
            match, r = self.check_match(regex, item['abbr'])
            if match:
                #suggestions.append((len(r.group()), r.start(), item['abbr']))
                suggestions.append(item)
        return suggestions
        #return [z for _, _, z in sorted(suggestions)]

if __name__ == '__main__':
    mymatcher = MyMatcher(prefixes=['RT:', 'RT'])
    context = {'complete_str': 'RT:teststand',
               'input': 'RT:teststand'}
    pos = mymatcher.get_complete_position(context)
    print('POS', pos)

    prefix, complete_str = mymatcher.get_complete_str(context)
    print('prefix', prefix, 'complete_str', complete_str)

    filtered_candidates = mymatcher.load_raw_candidates(
        CANDIDATES_FILENAME, complete_str)
    print('filtered_candidates', filtered_candidates[:3])

