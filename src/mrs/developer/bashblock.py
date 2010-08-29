import re
import manuel
import textwrap
import subprocess

CODEBLOCK_START = re.compile(
    r'(^\.\.\s*(invisible-)?code-block::?\s*bash\b(?:\s*\:\w+\:)*)',
    re.MULTILINE)
CODEBLOCK_END = re.compile(r'(\n\Z|\n(?=\S))')


class BashBlock(object):

    def __init__(self, source):
        self._source = source
        self.source = []

        for line in source.split('\n'):
            if not line:
                continue
            self.source.append(line)


def find_code_blocks(document):
    for region in document.find_regions(CODEBLOCK_START, CODEBLOCK_END):
        start_end = CODEBLOCK_START.search(region.source).end()
        source = textwrap.dedent(region.source[start_end:])
        document.claim_region(region)
        region.parsed = BashBlock(source)


def execute_code_block(region, document, globs):
    if not isinstance(region.parsed, BashBlock):
        return

    result = 'lalalala'
    import pdb; pdb.set_trace()
    region.evaluated = result


class Manuel(manuel.Manuel):
    def __init__(self):
        manuel.Manuel.__init__(self, [find_code_blocks], [execute_code_block])
