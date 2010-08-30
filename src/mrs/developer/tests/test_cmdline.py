import unittest
import manuel.codeblock
import manuel.doctest
import manuel.testing


### This should probably be moved to manuel
import re
import manuel
import textwrap
import subprocess

CODEBLOCK_START = re.compile(
    r'(^\.\.\s*(invisible-)?code-block::?\s*console\b(?:\s*\:\w+\:)*)',
    re.MULTILINE)
CODEBLOCK_END = re.compile(r'(\n\Z|\n(?=\S))')
COMMAND_MARKERS = ['#', '%', '$']


class ChunkBlock(object):

    def __init__(self, source):
        self.source, self.result = source, ''
        self.command, self.expected_result = self.parse()
        self.command = self.command[1:].strip()

    def run_command(self):
        p = subprocess.Popen(self.command.split(),
                             stderr=subprocess.STDOUT,
                             stdout=subprocess.PIPE)
        result, _ = p.communicate()
        p.wait()
        self.result = result.strip('\n')
        return self.expected_result == self.result

    def parse(self):
        source = self.source.strip('\n')
        if source[0] not in COMMAND_MARKERS:
            raise Exception('You should start a block with %, # or $.')

        # parse command out
        command = ''
        command_num = 1
        for i, line in enumerate(source.split('\n')):
            if line[0] not in COMMAND_MARKERS + ['>']:
                source = source[command_num:]
                break
            if len(command) and command[-1] == '\\':
                if line[0] == '>':
                    command = command[:-1]
                    line = line[1:].lstrip()
                    command_num += 3
                else:
                    raise Exception('You ment to continue this command? '
                                    '--> "%s"' % command)
            command += line
            command_num += len(line)
        return command, source

    def error_msg(self):
        return 'Error at command: \n    %% %s\n\nEXPECTED:\n%s\n\nGOT:\n%s' % (
                    self.command, self.expected_result, self.result)


class ConsoleBlock(object):

    def __init__(self, source):
        self.source, self.chunks = source, []
        tmp_source, first = [], True
        for line in source.split('\n')[1:]:
            if len(line) and line[0] in COMMAND_MARKERS:
                if first:
                    first = False
                else:
                    self.chunks.append(ChunkBlock('\n'.join(tmp_source)))
                    tmp_source = []
            tmp_source.append(line)
        self.chunks.append(ChunkBlock('\n'.join(tmp_source)))


def parse(document):
    for region in document.find_regions(CODEBLOCK_START, CODEBLOCK_END):
        start_end = CODEBLOCK_START.search(region.source).end()
        source = textwrap.dedent(region.source[start_end:])

        document.claim_region(region)
        region.parsed = ConsoleBlock(source)

        assert region in document


def evaluate(region, document, globs):
    if not isinstance(region.parsed, ConsoleBlock):
        return
    result = False
    for chunk in region.parsed.chunks:
        if not isinstance(chunk, ChunkBlock):
            continue
        if not chunk.run_command():
            region.evaluated = chunk
            break


def format(document):
    for region in document:
        if not isinstance(region.evaluated, ChunkBlock):
            continue
        region.formatted = region.evaluated.error_msg()


class Manuel(manuel.Manuel):
    def __init__(self):
        manuel.Manuel.__init__(self, [parse], [evaluate], [format])


##########################


def test_suite():
    m = manuel.doctest.Manuel()
    m += manuel.codeblock.Manuel()
    m += Manuel()
    return manuel.testing.TestSuite(m,
            #'../README.txt'
            '../tests.txt',
            )

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())

