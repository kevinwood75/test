# Import salt modules
import salt.client

def up():
    '''
    Print a list of all of the minions that are up
    '''
    client = salt.client.LocalClient(__opts__['conf_file'])
#    minions = client.cmd('*', 'test.ping', timeout=1)
    ret = client.cmd('postgresdb1.woodez.net', 'state.sls', ['ort'],  timeout=1)
#    print("{0}".format(ret))
#    print("{0}".format(ret))
    result_list = []
    for key,value in ret.iteritems():
        for item,data in value.iteritems():
            result_list.append((key,item,data.get('result', None)))           
#    print("{0}".format(result_list[0]))
            print("{0},{1},{2}".format(key, item, str(data.get('result', None)).replace("True", "OK").replace("False", "NOTOK")))
####    return result_list
    return result_list
###            return("{0},{1},{2}".format(key, item,data.get('result', None)))
##               print("{0},{1},{2}".format(key, item, data.get('result', None)))
#         print("{0}".format(value))
#    for minion in sorted(minions):
#        print("{0},test".format(minion))
