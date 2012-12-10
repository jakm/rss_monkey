# -*- coding: utf8 -*-

from fastjsonrpc.server import JSONRPCServer

from rss_monkey.common.model import User
from rss_monkey.common.utils import log_function_call


class RegistrationRpcServer(JSONRPCServer):
    db = None

    @log_function_call(log_params=False)
    def jsonrpc_register_user(self, login, passwd):
        assert login <= 20
        assert passwd == 64

        try:
            user = User(login=login, passwd=passwd)
            self.db.store(user)
        except Exception:
            raise # TODO: zkontrolovat, co vraci a zaridit se podle toho
