# Import python libs
import pprint

# Import salt libs
import salt.utils


def output(data):
    '''
    The HighState Outputter is only meant to
    be used with the state.highstate function, or a function that returns
    highstate return data.
    '''
    for host, hostdata in data.iteritems():
        return _format_host(host, hostdata)[0]


def _format_host(host, data):
    colors = salt.utils.get_colors(__opts__.get('color'))
    tabular = __opts__.get('state_tabular', False)
    rcounts = {}
    hcolor = colors['GREEN']
    hstrs = []
    changed = False
    state_output = 'mixed'
    total_success = 0
    total_failed = 0
    total_changed = 0
    if isinstance(data, list):
        # Errors have been detected, list them in RED!
        hcolor = colors['RED_BOLD']
        hstrs.append(('    {0}Data failed to compile:{1[ENDC]}'
                      .format(hcolor, colors)))
        for err in data:
            hstrs.append(('{0}----------\n    {1}{2[ENDC]}'
                          .format(hcolor, err, colors)))
    if isinstance(data, dict):
        # Strip out the result: True, without changes returns if
        # state_verbose is False
        if not __opts__.get('state_verbose', False):
            data = _strip_clean(data)
        # Verify that the needed data is present
        for tname, info in data.items():
            if '__run_num__' not in info:
                err = ('The State execution failed to record the order '
                       'in which all states were executed. The state '
                       'return missing data is:')
                hstrs.insert(0, pprint.pformat(info))
                hstrs.insert(0, err)
        # Everything rendered as it should display the output
        for tname in sorted(
                data,
                key=lambda k: data[k].get('__run_num__', 0)):
            ret = data[tname]
            # Increment result counts
            rcounts.setdefault(ret['result'], 0)
            rcounts[ret['result']] += 1
            tcolor = colors['GREEN']
            schanged, ctext = _format_changes(ret['changes'])
            changed = changed or schanged
            if schanged:
                tcolor = colors['CYAN']
            if ret['result'] is False:
                hcolor = colors['RED']
                tcolor = colors['RED']
            if ret['result'] is None:
                hcolor = colors['YELLOW']
                tcolor = colors['YELLOW']
            comps = tname.split('_|-')
            if state_output.lower() == 'terse':
                # Print this chunk in a terse way and continue in the
                # loop
                msg = _format_terse(tcolor, comps, ret, colors, tabular)
                hstrs.append(msg)
                continue
            elif state_output.lower() == 'mixed':
                # Print terse unless it failed
                if ret['result'] is not False:
                    # We dont print successes, just track stats
                    total_success = total_success + 1
                    if schanged:
                        total_changed = total_changed + 1
                    continue
                else:
                    total_failed = total_failed + 1
            elif state_output.lower() == 'changes':
                # Print terse if no error and no changes, otherwise, be
                # verbose
                if ret['result'] and not schanged:
                    msg = _format_terse(tcolor, comps, ret, colors, tabular)
                    hstrs.append(msg)
                    continue
            state_lines = [
                '{tcolor}----------{colors[ENDC]}',
                '    {tcolor}      ID: {comps[1]}{colors[ENDC]}',
                '    {tcolor}Function: {comps[0]}.{comps[3]}{colors[ENDC]}',
                '    {tcolor}  Result: {ret[result]!s}{colors[ENDC]}',
                '    {tcolor} Comment: {comment}{colors[ENDC]}'
            ]
            # This isn't the prettiest way of doing this, but it's readable.
            if comps[1] != comps[2]:
                state_lines.insert(
                    3, '    {tcolor}    Name: {comps[2]}{colors[ENDC]}')
            try:
                comment = ret['comment'].strip().replace('\n', '\n' + ' ' * 14)
            except AttributeError:
                comment = ret['comment'].join(' ').replace('\n',
                                                           '\n' + ' ' * 13)
            svars = {
                'tcolor': tcolor,
                'comps': comps,
                'ret': ret,
                'comment': comment,
                # This nukes any trailing \n and indents the others.
                'colors': colors
            }
            hstrs.extend([sline.format(**svars) for sline in state_lines])
            changes = '     Changes:   ' + ctext
            hstrs.append(('{0}{1}{2[ENDC]}'
                          .format(tcolor, changes, colors)))

        # Append result counts to end of output
        colorfmt = '{0}{1}{2[ENDC]}'

        host = host + ' '
        summary_line = '{0}{1}{2[ENDC]}'.format(hcolor, host.ljust(40,'-'), colors)
        
        summary_line = summary_line + ' ' + colorfmt.format(
            colors['GREEN'],
            'Success:' + str(total_success).rjust(4),
            colors
        )

        summary_line = summary_line + ' '+ colorfmt.format(
            colors['CYAN'],
            'Changed:' + str(total_changed).rjust(4),
            colors
        )

        summary_line = summary_line + ' ' + colorfmt.format(
            colors['RED'] if total_failed else colors['CYAN'],
            'Errors:' + str(total_failed).rjust(4),
            colors
        )

        hstrs.append(summary_line)

    #hstrs.insert(0, ('{0}{1}:{2[ENDC]}'.format(hcolor, host, colors)))
    return '\n'.join(hstrs), changed


def _format_changes(changes):
    '''
    Format the changes dict based on what the data is
    '''
    global __opts__  # pylint: disable=W0601

    if not changes:
        return False, ''

    if not isinstance(changes, dict):
        return True, 'Invalid Changes data: {0}'.format(changes)

    ret = changes.get('ret')
    if ret is not None and changes.get('out') == 'highstate':
        ctext = ''
        changed = False
        for host, hostdata in ret.iteritems():
            s, c = _format_host(host, hostdata)
            ctext += '\n' + '\n'.join((' ' * 14 + l) for l in s.splitlines())
            changed = changed or c
    else:
        changed = True
        opts = __opts__.copy()
        # Pass the __opts__ dict. The loader will splat this modules __opts__ dict
        # anyway so have to restore it after the other outputter is done
        if __opts__['color']:
            __opts__['color'] = 'CYAN'
        __opts__['nested_indent'] = 14
        ctext = '\n'
        ctext += salt.output.out_format(
                changes,
                'nested',
                __opts__)
        __opts__ = opts
    return changed, ctext


def _strip_clean(returns):
    '''
    Check for the state_verbose option and strip out the result=True
    and changes={} members of the state return list.
    '''
    rm_tags = []
    for tag in returns:
        if returns[tag]['result'] and not returns[tag]['changes']:
            rm_tags.append(tag)
    for tag in rm_tags:
        returns.pop(tag)
    return returns


def _format_terse(tcolor, comps, ret, colors, tabular):
    '''
    Terse formatting of a message.
    '''
    result = "Clean"
    if ret['changes']:
        result = "Changed"
    if ret['result'] is False:
        result = "Failed"
    elif ret['result'] is None:
        result = "Differs"
    if tabular is True:
        fmt_string = '{0}{2:>10}.{3:<10} {4:7}   Name: {1}{5}'
    elif isinstance(tabular, str):
        fmt_string = tabular
    else:
        fmt_string = ' {0} Name: {1} - Function: {2}.{3} - Result: {4}{5}'
    msg = fmt_string.format(tcolor,
                            comps[2],
                            comps[0],
                            comps[-1],
                            result,
                            colors['ENDC'],
                            ret)
    return msg
