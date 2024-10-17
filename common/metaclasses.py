import dis
from pprint import pprint


class ServerMaker(type):
    """Metaclass for server check"""

    def __init__(cls, name, bases, dct):
        methods = []
        attrs = []
        pprint(dct)
        print()
        if dct['__qualname__'] == 'StartServer':
            del dct
        else:
            for func in dct:
                try:
                    ret = dis.get_instructions(dct[func])
                except TypeError:
                    pass
                else:
                    for i in ret:
                        print(i)
                        if i.opname == 'LOAD_GLOBAL':
                            if i.argval not in methods:
                                methods.append(i.argval)
                        elif i.opname == 'LOAD_ATTR':
                            if i.argval not in attrs:
                                attrs.append(i.argval)

            print(f'\nmethods:{methods}')
            print(f'attributes: {attrs}\n')
            if 'connect' in methods:
                raise TypeError("Using 'connect' method is not allowed in server class!")
            if not ('AF_INET' in attrs and 'SOCK_STREAM' in attrs):
                raise TypeError("Incorrect socket initialization.")
            super().__init__(name, bases, dct)
