"""
This is RT source plugin for deoplete. It completes RequestTracker numbers from
a cache file.

# Install:

1. Copy the file to $HOME/.vim/bundle/deoplete.nvim/rplugin/python3/deoplete/sources/
2. pip install regex (https://pypi.python.org/pypi/regex supports cool fuzzy matching)
"""
from .base import Base

def log(msg):
    with open('/tmp/deoplete-jira.log', 'a') as file_:
        file_.write('%s\n' % msg)

from jira_rt_completion_server.jira_completer import JiraCompleter


class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim)

        self._completer = JiraCompleter('~/.cache/jira/jira.candidates.tsv')

        self.debug_enabled = True
        self.name = 'jira'
        #self.kind = 'keyword'
        self.mark = '[JIRA]'
        #self.min_pattern_length = 2

        # Use these options if you want to filter candidates yourself
        self.is_volatile = True
        self.matchers = [] # ['matcher_cpsm']
        self.sorters = []

        # Use these options if you want to implement custom matcher
        #self.matchers = ['matcher_fuzzy', 'matcher_full_fuzzy']
        #self.sorters = ['sorter_rank']
        #self.converters = []

        self.max_menu_width = 150
        self.max_abbr_width = 150
        self.input_pattern = self._completer.input_pattern #r'JI:?\w*$' #self._source.input_pattern

    def get_complete_position(self, context):
        return self._completer.get_complete_position(context)

    def gather_candidates(self, context):
        return self._completer.gather_candidates(context)

    def on_post_filter(self, context):
        return self._completer.on_post_filter(context)
