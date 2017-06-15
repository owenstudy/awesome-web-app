import asyncio
import aiomysql

loop = asyncio.get_event_loop()

#@asyncio.coroutine
#def test_example():
#    conn = yield from aiomysql.connect(host='127.0.0.1', port=3306,
#                                       user='user', password='password', db='db',
#                                       loop=loop)
#
#    cur = yield from conn.cursor()
#    yield from cur.execute("SELECT * FROM user")
#    print(cur.description)
#    r = yield from cur.fetchall()
#    print(r)
#    yield from cur.close()
#    conn.close()
pool= None
async def create_pool():
    global pool
    pool = await aiomysql.create_pool(host='localhost', user='user', password='password', db='db')

async def test_example():
    global pool
    await create_pool()
    #pool=await aiomysql.create_pool(host='localhost',user='user',password='password',db='db')
    print(str(pool))
    async with pool.acquire() as conn:
    #conn = await aiomysql.connect(host='localhost', port=3306,
    #                                   user='user', password='password', db='db',
    #                                   loop=loop)

        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM user")
            print(cur.description)
            r = await cur.fetchall()
            print(r)
            await cur.close()
        conn.close()


loop.run_until_complete(test_example())