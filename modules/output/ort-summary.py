# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

 
# Import 3rd-party libs
from salt.ext import six


def output(data, **kwargs):
    '''
    First try at outputer....
    '''

    good_counter=0
    bad_counter=0
    result_list=[]
    result_list.append("CHECK_STATE_NAME,STATUS")
    result_list.append("-----------------------")

    if not isinstance(data, six.string_types):
        for host, outer in data.iteritems():
            good_counter=0
            bad_counter=0
            result_list=[]
            header = "HOSTNAME: {0}".format(host)
            result_list.append(header)
            result_list.append("CHECK_STATE_NAME,STATUS")
            result_list.append("-----------------------")

            try:
               for state, result in outer.iteritems():
                   data = six.text_type(state)+","+str(result.get('result', None)).replace("True","OK").replace("False","NOTOK")
                   if result.get('result', None) is not False:
                      good_counter += 1
                      result_list.append(data)
                   else:
                      bad_counter += 1
                      result_list.append(data)
               summary = "CHECK STATES OK: {0}  CHECK STATES NOTOK: {1}".format(good_counter,bad_counter)

               result_list.append(summary)
               result_list.append("===========================================")
               result_list.append("\n")
               return "\n".join(result_list).decode('utf-8', 'ignore')
            except AttributeError:
               return "{0} => None".format(host)
