import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306,
                                           user='user', password='password',
                                           db='db')
cur = conn.cursor()
cur.execute("SELECT * FROM user")

print('sql result:'+str(cur.rowcount))