class Calc: 

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def add(self):
        return self.a + self.b

    def dif(self):
        return self.a - self.b

    def seki(self):
        return self.a*self.b

    def shou(self):
        if self.b == 0:
            return "Not Devide!"
        else:
            return self.a/self.b