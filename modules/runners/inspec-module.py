import salt.client
import json
from influxdb import InfluxDBClient

def put_in_influx(influx_config, inspec_data, measurement):
    json_body = []
    client = InfluxDBClient(influx_config['host'], influx_config['port'], influx_config['user'], influx_config['password'], influx_config['dbname'])
    client.create_database(influx_config['dbname'])
#    client.drop_measurement(measurement)
    for line in inspec_data:
        input_json = { 
                 "measurement": measurement,
                 "tags": { 
                     "status": line.get('status', 'NA'),
                     "hostname": line.get('hostname', 'NA')
                 },
                 "fields": {
                    "desc": line.get('desc', 'NA'),
                    "status": line.get('status', 'NA')
                 } 
              }

        json_body.append(input_json)
        client.write_points(json_body) 
    return      


def run(hname):
    '''
    run inspec tests on hostanme specified in argument
    '''

    influx_config = {
       "host": "192.168.2.148",
       "port": "8086",
       "user": "influxdblab",
       "password": "jandrew28",
       "dbname": "inspec" }

    measurement = 'inspec_results'

    client = salt.client.LocalClient(__opts__['conf_file'])
    ret = client.cmd(hname, 'state.sls', ['inspec'],  timeout=1)
    result_list = []
#    for key,value in ret.iteritems():
    value = ret.values()
    data = value[0].values()
    data_ret = json.loads(data[0]['changes'].get('stdout'))
    for line in data_ret['profiles']:
        for contrl in line.get('controls'):
            for results in contrl.get('results'):
                status = results.get('status')
                desc = results.get('code_desc')
                stime = results.get('start_time')
                result_list.append({ 'hostname': hname, 'desc': desc, 'status': status, 'start_time': stime })
    put_in_influx(influx_config, result_list, measurement)
    return result_list
