import dis
from pprint import pprint


class ServerMaker(type):
    """Metaclass for server check"""

    def __init__(cls, name, bases, dct):
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
                        if i.opname == 'LOAD_ATTR':
                            if i.argval not in attrs:
                                attrs.append(i.argval)

            print(f'attributes: {attrs}\n')
            if 'connect' in attrs:
                raise TypeError("Using 'connect' method is not allowed "
                                "in server class!")
            if not ('AF_INET' in attrs and 'SOCK_STREAM' in attrs):
                raise TypeError("Incorrect socket initialization.")
            super().__init__(name, bases, dct)


class ClientMaker(type):
    def __init__(cls, name, bases, dct):
        attrs = []
        # pprint(dct)
        # print()

        for func in dct:
            try:
                ret = dis.get_instructions(dct[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    # print(i, '\n')
                    if i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)

        print(f'attributes: {attrs}\n')
        for command in ('accept', 'listen', 'socket'):
            if command in attrs:
                raise TypeError("Incorrect use of functions "
                                "was detected in the class!")
            if 'get_message' in attrs or 'send_message' in attrs:
                pass
            else:
                raise TypeError("No calls to functions to work with sockets!")
        super().__init__(name, bases, dct)
