'''
__changelog__ -- contains the project changelog in object form.
'''

from bwversion import Version, WIPVersion, PlannedVersion, ChangeLog

CHANGELOG = ChangeLog(
    WIPVersion('0.4.0',
        'BWObject can be used as @decorator',
        ),
    Version('0.3.6',
        'Fixed missing BWContext problem',
        'Fixed bug where varkeys from installctx was not pushed into ctx',
        'Fixed semantics on __ctxproperty__',
        'Added better context installer support',
        'throw() now returns the thrown object',
        ),
    Version('0.3.5',
        'Fixed missing into() problem',
        ),
    Version('0.3.4',
        'Added better reference mechanics to context',
        'Added rebinding of contexts to context referecnes',
        'Added ability to set partial paths on contexts',
        'Removed classcachedmethod as no good use case emerged for it',
        ),
    Version('0.3.3',
        'Added greater support for code coverage',
        'Fixed numerous bugs via code coverage'
        ),
    Version('0.3.2',
        'Added contexts',
        ),
    Version('0.3.1',
        'Added the member attribute extensions',
        ),
    Version('0.3',
        'Added type conversion support for members',
        'Added default and built values for members',
        'Added required members',
        'Added TC global',
        ),
    Version('0.2.6',
        'Added throw() and catch() as simple functions',
        ),
    Version('0.2.5',
        'Added throwables',
        'Added changelog file',
        'Modified version to be more shell friendly',
        'Made __version__ more pydoc compatible',
        ),
    Version('0.1', 'Initial pre-release at PyOhio'),
)

__doc__ += '\n' + str(CHANGELOG)

if __name__ == '__main__':
    print CHANGELOG

