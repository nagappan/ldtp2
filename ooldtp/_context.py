"""
LDTP v2 ooldtp context

@author: Eitan Isaacson <eitan@ascender.com>
@author: Nagappan Alagappan <nagappan@gmail.com>
@copyright: Copyright (c) 2009 Eitan Isaacson
@copyright: Copyright (c) 2009-12 Nagappan Alagappan
@license: LGPL

http://ldtp.freedesktop.org

This file may be distributed and/or modified under the terms of the GNU Lesser General
Public License version 2 as published by the Free Software Foundation. This file
is distributed without any warranty; without even the implied warranty of 
merchantability or fitness for a particular purpose.

See 'COPYING' in the source distribution for more information.

Headers in this file shall remain intact.
"""

import os
import ldtp

if os.environ.has_key('LDTP_DEBUG'):
    _ldtp_debug = os.environ['LDTP_DEBUG']
else:
    _ldtp_debug = None

class _Wrapper(object):
    def __new__(cls, *args, **kwargs):
        if not cls._generated:
            cls._generated = True
            d = ldtp.__dict__
            cls._wrapped_methods =[]
            for attr in d:
                # Don't populate function name in ldtp module
                # starting with _
                if type(attr) == str and attr[0] != '_' and \
                        cls._isRemoteMethod(d[attr]):
                    setted = attr
                    if hasattr(cls, attr):
                        setted = "_remote_"+setted
                    cls._wrapped_methods.append(setted)
                    setattr(cls, setted, d[attr])
        return object.__new__(cls)

    def __getattribute__(self, name):
        obj = object.__getattribute__(self, name)
        if name in object.__getattribute__(self, '_wrapped_methods'):
            wrapper = object.__getattribute__(self, '_wrapMethod')
            return wrapper(obj)
        return obj

    def _isRemoteMethod(cls, obj):
        return hasattr(obj, '_Method__name') or \
            hasattr(obj, 'func_name')

    _isRemoteMethod = classmethod(_isRemoteMethod)

    def _listArgs(cls, func):
        l = [a.strip() for a in func.__doc__.split('\n')]
        l = filter(lambda x: x.startswith('@param '), l)
        l = [x[7:].split(':')[0] for x in l]
        return l
    _listArgs = classmethod(_listArgs)

class Context(_Wrapper):            
    _generated = False

    def __init__(self, window_name):
        self._window_name = window_name

    def __repr__(self):
        return 'Context of "%s"' % self._window_name

    def _wrapMethod(self, obj):
        return _ContextFuncWrapper(self._window_name, obj)

    def getchild(self, child_name='', role=''):
        # TODO: Bad API choice. Inconsistent, should return object or list,
        # not both. UPDATE: Only returns first match.
        matches = self._remote_getchild(child_name, role)
        if matches:
            if role:
                component_list = []
                for matched_obj in matches:
                    component_list.append(Component(self._window_name,
                                                    matched_obj))
                return component_list
            else:
                return Component(self._window_name, matches[0])
        else:
            return None
    
class _ContextFuncWrapper:
    def __init__(self, window_name, func):
        self._window_name = window_name
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(self._window_name, *args, **kwargs)

class Component(_Wrapper):            
    _generated = False

    def __init__(self, window_name, object_name):
        self._window_name = window_name
        self._object_name = object_name

    def getName(self):
        return self._object_name

    def getchild(self, child_name='', role=''):
        # TODO: Bad API choice. Inconsistent, should return object or list,
        # not both. UPDATE: Only returns first match.
        matches = self._remote_getchild(child_name, role, self._object_name)
        if matches: 
            if role:
                component_list = []
                for matched_obj in matches:
                    component_list.append(Component(self._window_name,
                                                    matched_obj))
                return component_list
            else:
                return Component(self._window_name, matches[0])
        else:
            return None
    
    def __repr__(self):
        return 'Component "%s" in "%s"' % \
            (self._object_name, self._window_name)

    def _wrapMethod(self, func):
        return _ComponentFuncWrapper(
            self._window_name, self._object_name, func)

class _ComponentFuncWrapper:
    def __init__(self, window_name, object_name, func):
        self._window_name = window_name
        self._object_name = object_name
        self._func = func

    def __call__(self, *args, **kwargs):
        if self._func._Method__name == 'getchild':
            # Hack
            return self._func(
                self._window_name, *args, **kwargs)
        else:
            return self._func(
                self._window_name, self._object_name, *args, **kwargs)

if __name__ == "__main__":
    c = Component('Calculator', 'btnNumeric1')
    print dir(c)
    c.click()
