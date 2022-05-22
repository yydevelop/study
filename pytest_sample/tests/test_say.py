from main.say import Foo,Hoge

def test_foo_say():
    assert Foo().say() == 'foo'

def test_foo_say2():
    assert Foo().say2() == 'foo2'

def test_hoge_say():
    assert Hoge().say() == 'hoge'

def test_hoge_say2():
    assert Hoge().say2()== 'hoge2'