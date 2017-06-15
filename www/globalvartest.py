CONSTANT = 0  #(将全局变量大写便于识别)

def modifyConstant() :
        global CONSTANT
        print(CONSTANT)
        CONSTANT += 1
        return

if __name__ == '__main__' :
        modifyConstant()
        print(CONSTANT)