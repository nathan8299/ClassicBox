#!/usr/bin/env python

"""
Reads resource forks.
"""

from classicbox.resource_fork import read_resource_fork
from classicbox.resource_fork import write_resource_fork
from StringIO import StringIO
import sys

# ------------------------------------------------------------------------------

def main(args):
    (command, resource_file_filepath, ) = args
    
    if command == 'info':
        with open(resource_file_filepath, 'rb') as input:
            # Read and print the contents of the resource map
            print_resource_fork(input)
    
    elif command == 'test_read_write_approx':
        test_read_write_approx(resource_file_filepath)
    
    elif command == 'test_read_write_exact':
        test_read_write_exact(resource_file_filepath)
    
    else:
        sys.exit('Unrecognized command: %s' % command)
        return


def test_read_write_approx(resource_file_filepath):
    """
    Tests that the specified fork written by write_resource_fork() is read
    by read_resource_fork() as exactly the same data structure.
    
    Does NOT test that an arbitrary fork read by read_resource_fork() will
    be output by write_resource_fork() as exactly the same byte stream.
    See test_read_write_exact() for that test.
    """
    
    with open(resource_file_filepath, 'rb') as input:
        original_resource_map = read_resource_fork(
            input,
            read_everything=True)
    
    # Must write to an intermediate "normalized" fork
    normalized_fork = StringIO()
    write_resource_fork(normalized_fork, original_resource_map)
    
    normalized_fork.seek(0)
    normalized_resource_map = read_resource_fork(
        normalized_fork,
        read_everything=True)
    
    output_fork = StringIO()
    write_resource_fork(output_fork, normalized_resource_map)
    
    expected_output = normalized_fork.getvalue()
    actual_output = output_fork.getvalue()
    
    matches = (actual_output == expected_output)
    print 'Matches? ' + ('yes' if matches else 'no')
    if not matches:
        print '    Expected: ' + repr(expected_output)
        print '    Actual:   ' + repr(actual_output)
        print


def test_read_write_exact(resource_file_filepath):
    """
    Tests that the specified fork read by read_resource_fork() is
    output by write_resource_fork() as exactly the same byte stream.
    
    NOTE: There exist valid resource fork inputs for which this test fails.
          This is because the resource fork format does not strictly
          define the precise ordering, arrangement, and spacing of 
          several elements in the resource fork.
          
          However, this implementation SHOULD correctly reconstruct any
          resource fork generated by ResEdit 2.1.3.
    """
    
    with open(resource_file_filepath, 'rb') as input:
        original_resource_map = read_resource_fork(
            input,
            read_everything=True)
    
    output_fork = StringIO()
    write_resource_fork(output_fork, original_resource_map)
    
    with open(resource_file_filepath, 'rb') as file:
        expected_output = file.read()
    actual_output = output_fork.getvalue()
    
    matches = (actual_output == expected_output)
    print 'Matches? ' + ('yes' if matches else 'no')
    if not matches:
        print '    Expected: ' + repr(expected_output)
        print '    Actual:   ' + repr(actual_output)
        print
        print ('#' * 32) + ' EXPECTED ' + ('#' * 32)
        print_resource_fork(StringIO(expected_output))
        
        print ('#' * 32) + ' ACTUAL ' + ('#' * 32)
        print_resource_fork(StringIO(actual_output))

# ------------------------------------------------------------------------------

def print_resource_fork(input_resource_fork_stream):
    # NOTE: Depends on an undocumented argument
    resource_map = read_resource_fork(
        input_resource_fork_stream,
        read_all_resource_names=True,
        _verbose=True)

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv[1:])
