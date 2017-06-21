#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError
import module

#对GET方法的路径进行处理
#装饰器函数，给函数增加两个参数，一个是提交的方法，一个是路径
def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        #对装饰器的方法增加两个属性，调用的方法和路径
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator
#对POST方法的路径进行处理
def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

#获取函数的参数列表
def get_required_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        #判断参数的类型，KEYWORD_ONLY(指那些确定的命名参数)并且没有默认值的参数
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

#获取函数的固定名称参数，有没有默认值都取出来
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)
#判断一个函数中是不是有命名参数
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
#判断函数最后一个参数是不是request参数
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

#request对象的处理类
class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)
    #对实例进行函数调用 ，如req=RequestHandler(), req(request)将调用这个函数
    async def __call__(self, request):
        kw = None
        #???不明白这里面的判断
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        # check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)
#添加静态资源
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))
#增加函数的路由处理
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    #检查函数是不是有自带的方法和路由两个参数，没有的话就报错
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    #检查函数是不是协程函数，如果不是则设置成为协程函数
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    #把函数注册到路由中
    app.router.add_route(method, path, RequestHandler(app, fn))
#自动把模块中的路由处理全部自动注册
def add_routes(app, module_name):
    #导入模块的所有属性和方法，不是引用某个方法或者属性
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        #引用某个方法或者属性
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        #对非_开头的属性进行检查
        fn = getattr(mod, attr)
        #如果是可以调用函数,并且是经过装饰器装饰 的函数才加入到route
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)

#测试
if __name__=='__main__':
    @get('/')
    def log(*args,x,y=1,**kw):
        pass

    loop=asyncio.get_event_loop()
    app=web.Application(loop=loop)
    module_name='module.User'
    n = module_name.rfind('.')
    print(n)

    params1=get_required_kw_args(log)
    print(params1)
    params2=get_named_kw_args(log)
    print(params2)
    method = getattr(log, '__method__', None)
    path=getattr(log,'__route__',None)
    print(method)
    print(path)