def upper_attr(class_name, class_parents, class_attr):
    attrs = ((name, value) for name, value in class_attr.items() if not name.startswith('__'))
    print(attrs)
    uppercase_attrs = dict((name.upper(), value) for name, value in attrs)
    print('uppercase_attrs:' + str(uppercase_attrs))
    return type(class_name, class_parents, uppercase_attrs)

__metaclass__ = upper_attr

pw = upper_attr('Trick', (), {'bar': 0})
print(hasattr(pw, 'bar'))
print(hasattr(pw, 'BAR'))
print(pw.BAR)

pw2=type('Trick2',(),{'bar':'2'})
print('second case:')
print(hasattr(pw2, 'bar'))
print(hasattr(pw2, 'BAR'))
print(pw2.bar)
print(pw2.__name__)

pw3=pw()
print(hasattr(pw3, 'BAR'))

dict1={"name":"Tom","Gender":"M"}
tuplelist=((name,value.lower()) for name,value in dict1.items())
dictlist=dict(((name,value) for name,value in tuplelist))
print(dictlist)