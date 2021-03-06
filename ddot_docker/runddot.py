#!/usr/bin/env python

import os
import stat
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
    parser.add_argument('--alpha', default=0.05, type=float,
                        help='Clixo alpha parameter (default 0.05)')
    parser.add_argument('--beta', default=0.5, type=float,
                        help='Clixo beta parameter (default 0.5)')
    parser.add_argument('--clixopath', default='/opt/conda/lib/python3.7/'
                                               'site-packages/ddot/clixo_0'
                                               '.3/clixo',
                        help='Path to clixo command in docker image (defa'
                             'ult /opt/conda/lib/python3.7/site-packages/'
                             'ddot/clixo_0.3/clixo')
    parser.add_argument('--output',
                        help='If set, write output of algorithm to '
                             'file specified')
    return parser.parse_args(args)


def run_clixo(clixopath, inputfile, alpha, beta):
    """
    Runs clixo
    :param clixopath:
    :param alpha:
    :param beta:
    :param inputfile:
    :param outputfile:
    :return:
    """
    cmd_to_run = clixopath + ' ' + inputfile + ' ' + str(alpha) + ' ' + str(beta)
    logger.debug(cmd_to_run)
    p = subprocess.Popen(shlex.split(cmd_to_run),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    out, err = p.communicate()
    return p.returncode, out, err


def run_ddot(theargs):
    try:
        (e_code, c_out, c_err) = run_clixo(theargs.clixopath, theargs.input, theargs.alpha, theargs.beta)
        df = pd.read_csv(io.StringIO(c_out.decode('utf-8')), sep='\t',
                         engine='python', header=None, comment='#')

        if theargs.output is not None:
            try:
                with open(theargs.output, 'wb') as f:
                    f.write(c_out)
                outputdir = os.path.dirname(theargs.output)
                statres = os.stat(outputdir)
                os.chown(theargs.output, statres[stat.ST_UID],
                         statres[stat.ST_GID])
            except Exception as ex:
                sys.stderr.write('Caught exception trying to write file or'
                                 'change permission: ' + str(ex))

        ont1 = Ontology.from_table(df, clixo_format=True, parent=0, child=1)

        if theargs.ndexserver.startswith('http://'):
            server = theargs.ndexserver
        else:
            server = 'http://' + theargs.ndexserver

        idf = pd.read_csv(theargs.input, sep='\t', engine='python', header=None, comment='#')
        idf.rename(columns={0: 'Gene1', 1: 'Gene2', 2: 'has_edge'}, inplace=True)
        ont_url, G = ont1.to_ndex(name=theargs.ndexname,
                                  network=idf,
                                  main_feature='has_edge',
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
