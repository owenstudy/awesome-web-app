import orm
from module import User, Blog, Comment
import asyncio


async def test(loop):
    await orm.create_pool(loop,user='www-data', password='www-data', database='awesome')

    u = User(name='Test', email='test3@example.com', passwd='1234567890', image='about:blank')

    await u.save()


if __name__=='__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))