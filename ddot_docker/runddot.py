#!/usr/bin/env python


import sys
import argparse
import pandas as pd
import shlex
import subprocess
import logging
import io
import json
from ddot import Ontology


logger = logging.getLogger('runddot')


def _parse_arguments(desc, args):
    """Parses command line arguments"""
    help_formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_formatter)

    parser.add_argument('input', help='Input file in 3 column format'
                                      'expected by clixo')
    parser.add_argument('--ndexserver', default='test.ndexbio.org',
                        help='NDEx server to upload ontology to (default test.ndexbio.org')
    parser.add_argument('--ndexuser', default='ddot_anon',
                        help='NDEx username (default ddot_anon)')
    parser.add_argument('--ndexpass', default='ddot_anon',
                        help='NDEx password (default ddot_anon)')
    parser.add_argument('--ndexname', default='DDOTontology',
                        help='Name to give network on NDEx (default DDOTontology)')
    parser.add_argument('--ndexlayout', default='bubble-collect',
                        help='Layout of network on NDEx (default bubble-collect)')
    parser.add_argument('--ndexvisibility', default='PUBLIC',
                        help='Visibility of network on NDEx (default PUBLIC)')
    parser.add_argument('--config', help='a text file to configure the algorithm')
    return parser.parse_args(args)


# def run_clixo(clixopath, inputfile, alpha, beta):
#     """
#     Runs clixo
#     :param clixopath:
#     :param alpha:
#     :param beta:
#     :param inputfile:
#     :param outputfile:
#     :return:
#     """
#     cmd_to_run = clixopath + ' ' + inputfile + ' ' + str(alpha) + ' ' + str(beta)
#     logger.debug(cmd_to_run)
#     p = subprocess.Popen(shlex.split(cmd_to_run),
#                          stdout=subprocess.PIPE,
#                          stderr=subprocess.PIPE)
#
#     out, err = p.communicate()
#     return p.returncode, out, err


def run_ddot(theargs):
    try:
        kwargs = {}
        with open(theargs.config) as fh:
            for l in fh:
                if l.startswith('#'):
                    continue
                else:
                    (k, v) = l.strip().split()
                    kwargs[k] = v
        if not ('Method' in kwargs):
            logger.exception('Method not specified in configuration file. Add line such as: Method\tclixo1.0b')
        elif kwargs['Method'].startswith('clixo'):
            ont = run_clixo(graph, **kwargs)
        else:
            ont = run_community_alg(graph, **kwargs)

        if theargs.ndexserver.startswith('http://'):
            server = theargs.ndexserver
        else:
            server = 'http://' + theargs.ndexserver

        ont_url, G = ont.to_ndex(name=theargs.ndexname,
                                  ndex_server=server,
                                  ndex_pass=theargs.ndexuser,
                                  ndex_user=theargs.ndexpass,
                                  layout=theargs.ndexlayout,
                                  visibility=theargs.ndexvisibility)
        return 'RESULT:' + ont_url.strip().replace('/v2/network/',
                                                   '/#/network/') + '\n'
    except OverflowError as ofe:
        logger.exception('Error running clixo')
        return 'ERROR:' + str(ofe) + '\n'
    except Exception as e:
        logger.exception('Some other error')
        return 'ERROR:' + str(e) + '\n'

    return {'error': 'unknown error'}


def main(args):
    """Main entry point"""
    desc = """
    Runs tasks generated by DDOT REST service

    """
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = 'unknown'
    try:
        res = run_ddot(theargs)
        if res is None or res == '':
            sys.stdout.write('Result is empty or None wtf\n')
        sys.stdout.write(res)
        sys.stdout.flush()
    except Exception as ex:
        logger.exception('caught some error')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
