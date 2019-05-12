# -*- coding: utf-8 -*-

'''
Returns event data for state execution only using a tcp socket, this method of
returning data can be used for Splunk.

 
State events are split out by state name.

It is strongly recommended to use the ``event_return_whitelist`` so not all
events are returned, for example:

..code-block:: yaml

   event_return_whitelist:
      - salt/job/*/ret/*

.. versionadded:: Boron

 
Add the following to the master configuration file:

..code-block:: yaml


   returner.influxdb_custom_return.host:<recieving server ip>
   returner.influxdb_custom_return.port: <listening port>

For events return set the event_return to influxdb_custom_return
This is NOT a job cache returner, it was designed to send events to a Splunk
server.
'''

 

from __future__ import absolute_import
# Import python libs
import json
import socket
import logging as log

 

# Import Salt libs
import salt.utils.jid
import salt.returners
import salt.client
# Import third party libs
#import influxdb
#from influxdb import InfluxDBClient

try:
    import influxdb
    import influxdb.influxdb08
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False

ignore_salt_functions = ['mine.update']
# log = logging.getLogger(__name__)
log.basicConfig(filename='/var/tmp/salt-runner.log', level=log.INFO)
log.info('started')

# Define virtual name

__virtualname__ = 'influxdb_custom_return'

 

def __virtual__():
    if not HAS_INFLUXDB:
        return False, 'Could not import influxdb returner; ' \
                      'influxdb python client is not installed.'
    return __virtualname__

 

def _get_grains(hostname):
    local = salt.client.LocalClient()
    test = local.cmd(hostname, 'grains.items')
    for host, data in test.iteritems():
        return data

 

def _get_options(ret=None):
    attrs = {'host': 'host',
             'port': 'port',
             'db': 'db',
             'measurement': 'measurement',
             'user': 'user',
             'password': 'password'}
    _options = salt.returners.get_returner_options('returner.{0}'.format
                                                   (__virtualname__),
                                                   ret,
                                                   attrs,
                                                   __salt__=__salt__,
                                                   __opts__=__opts__)
    return _options

 

def _send_info_to_influxdb(req, host, port, database, user, password):
    '''

    Return an influxdb client object

    '''

    client = influxdb.InfluxDBClient(host=host,
                            port=port,
                            username=user,
                            password=password,
                            database=database
        )

 
    try:
        client.write_points(req)
    except Exception as ex:
        log.critical('Failed to store return with InfluxDB returner: %s', ex)

 

def _return_states(data, host, port, database, user, password, measurement):
###    log.info("{0}".format(data.get('arg')))
###    if data.get('fun') == 'state.sls' or data.get('fun') == 'state.highstate':
    log.info('{0}: Sending event_return '
          'to host "{1}" on port "{2}"'.format(__virtualname__,
                                               host,
                                               port))
        
#    host_grains = _get_grains(data.get('id'))

#    for state_name, state in data.get('return').iteritems():
#        log.info('State Data for {0}: {1}'.format(__virtualname__,
#                                    json.dumps(state, indent=2)))

#        req = []

        # Add extra data to state event

    req = data

#        req = [{'measurement': measurement,
#                      'tags': {
#                          'fun': data.get('fun'),
#                          'id': data.get('id'),
#                          'jid': data.get('jid'),
#                          'result_boolean': state['result']
#                      },
#                      'fields': {
#                          'state_name': state_name,
#                          'state_id': state_name.split('_|-')[1],
#                          'host': data.get('id'),
#                          'os' : host_grains.get('osfinger', None),
#                          'environment' : host_grains.get('environment', None),
#                          'result':  str(state['result']),
#                          'comment':  state['comment']
#                      }
#                    }
#                   ]

    log.info('Post Data after for {0}: {1}'.format(__virtualname__,req))
        #log.info('Post Data after for {0}: {1}'.format(__virtualname__,
        #                            json.dumps(state, indent=2)))
        #_send_info_to_influxdb(state ,host, port, database, user, password)
    _send_info_to_influxdb(req ,host, port, database, user, password)

 

def event_return(events):
    _options = _get_options()
    host = _options.get('host')
    port = _options.get('port')
    database = _options.get('db')
    user = _options.get('user')
    password = _options.get('password')
    measurement = _options.get('measurement')

 

    for event in events:
        data = event.get('data', {})
#        id = data.get('id')
#        fun = data.get('fun')
#        jid = data.get('jid')
#        result = data.get('result')
#        comment = data.get('comment')
        log.debug('Event data coming in ... {0}'.format(data))

        # Ignore sending info to tcp socket for certain function calls
        # such as mine.update which get scheduled hourly.

#        if fun in ignore_salt_functions:
#            log.info('Ignore return from {0} for job {1}'.format(id, jid))
#            return

        data_return = data.get('data', None).get('results', None)

        if data_return:
            # Normal expectation is state.sls will return dict
            # will all state(s) result information. In this case we want
            # to traverse dict and send an update for each state result.

            if isinstance(data_return, list):
                _return_states(data_return, host, port, database, user, password, measurement)

            # In failure situations, such as jinja render error while
            # calling a state, a list and/or string may have been
            # returned instead of a dict. In this case send the
            # unexpected return to tcp socket.

            else:
                log.info('{0}: Could not process module function return to '
                         'host "{1}" on port "{2}" because of possible '
                         'failure situations '.format(__virtualname__,
                                                          host,
                                                           port))
                unexpected_fun_return = {
                    'fun_return': data_return,
                    'minion_id': id,
                    'jid': jid,
                    'fun': fun,
                    'fun_args': data.get('fun_args')}
                log.debug('{0}: {1}'.format(__virtualname__,
                                            json.dumps(unexpected_fun_return,
                                                       indent=2)))

#                _send_info_to_tcp_socket(unexpected_fun_return, host, port)
