'''
__changelog__ -- contains the project changelog in object form.
'''

from bwversion import Version, ChangeLog

CHANGELOG = ChangeLog(
    Version('0.1', 'Initial pre-release at PyOhio'),
    Version('0.2.5',
        'Added throwables',
        'Added changelog file',
        'Modified version to be more shell friendly',
        'Made __version__ more pydoc compatible',
        ),
    Version('0.2.6',
        'Added throw() and catch() as simple functions',
        ),
    Version('0.3',
        'Added type conversion support for members',
        'Added default and built values for members',
        'Added required members',
        'Added TC global',
        ),
    Version('0.3.1',
        'Added the member attribute extensions',
        ),
    Version('0.3.2',
        'Added contexts',
        ),
    Version('0.3.3',
        'Added greater support for code coverage',
        'Fixed numerous bugs via code coverage'
        ),
    Version('0.3.4',
        ),
)

__doc__ += '\n' + str(CHANGELOG)

if __name__ == '__main__':
    print CHANGELOG

