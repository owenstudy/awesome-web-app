import logging; logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html')

@asyncio.coroutine
def init(loop):
    #app 应用初始化
    app=web.Application(loop=loop)
    #路由解析
    app.router.add_route('GET','/',index)
    #设置服务器端口
    srv=yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    #LOG信息
    logging.info('server started at http://127.0.0.1:9000...')

    return srv

#得到循环事件
loop=asyncio.get_event_loop()
#初始化循环事件
loop.run_until_complete(init(loop))
#循环启动，开始接收客户端响应
loop.run_forever()

#test
__pool=
