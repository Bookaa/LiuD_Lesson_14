# lesson 14

class Var:
    def __init__(self, name, typ):
        self.typ = typ
        self.name = name
    def run(self, ctx):
        val = ctx.getvalue(self.name)
        if self.typ == type_unknown:
            return val
        if val.typ != self.typ:
            pass
        assert val.typ == self.typ
        return val

class SupportVar:
    def __init__(self, owner):
        self.vars = {}
        self.owner = owner
    def getvar(self, name):
        var = self.vars.get(name)
        if var:
            return var
        var = self.owner.getvar(name)
        assert var
        return var
    def addvar(self, name, typ):
        var = self.vars.get(name)
        if var is None:
            var = Var(name, typ)
            self.vars[name] = var
        else:
            assert var.typ == typ
        return var
class CodeBlock(SupportVar):
    def __init__(self, owner):
        SupportVar.__init__(self, owner)
        self.stmts = []
    def DefineAndAssign(self, name, val):
        var = self.addvar(name, val.typ)
        stmt = LiuL.newstmt_assign(var, val)
        self.stmts.append(stmt)
        return var

    def FuncCall(self, fn, args):
        stmt = LiuL.newstmt_funccall(fn, args)
        self.stmts.append(stmt)

    def addstmt_Return(self, val):
        stmt = LiuL.newstmt_return(val)
        self.stmts.append(stmt)

    def run(self, ctx):
        ctx1 = RunContext(ctx)
        for v in self.stmts:
            if isinstance(v, LiuL_stmt_return):
                return v.run(ctx1)
            v.run(ctx1)

class DefinedFunc(SupportVar):
    def __init__(self, funcname, args, owner):
        SupportVar.__init__(self, owner)
        self.name = funcname
        self.args = args
        self.block = CodeBlock(self)
        for name in args:
            self.addvar(name, type_unknown)
    def run(self, args, ctx0):
        ctx = RunContext(ctx0)
        assert len(self.args) == len(args)
        for name, value in zip(self.args, args):
            ctx.setvalue(name, value)
        result = self.block.run(ctx)
        return result

class Value:
    def __init__(self, typ, val):
        self.typ = typ
        self.val = val
    def run(self, ctx):
        return self

class Operate2:
    def __init__(self, op, val1, val2):
        typ1,typ2 = val1.typ, val2.typ
        if typ1 == typ2:
            self.typ = typ1
        elif type_unknown in (typ1, typ2):
            self.typ = type_unknown
        else:
            assert False
        self.op = op
        self.val1 = val1
        self.val2 = val2
    def run(self, ctx):
        v1 = self.val1.run(ctx)
        v2 = self.val2.run(ctx)
        if self.op == '+':
            v3 = v1.val + v2.val
            return Value(self.typ, v3)
        elif self.op == '*':
            v3 = v1.val * v2.val
            return Value(self.typ, v3)
        assert False

type_unknown = 'unknown'
type_int = 'int'

def GetValue(v, ctx):
    if isinstance(v, list):
        return [GetValue(v1, ctx) for v1 in v]
    if isinstance(v, str):
        v3 = v
    elif isinstance(v, Value):
        v3 = v
    else:
        assert False
    return v3

class OperateCall:
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        self.typ = type_unknown
    def run(self, ctx):
        if isinstance(self.fn, DefinedFunc):
            valuelst = [v.run(ctx) for v in self.args]
            return self.fn.run(valuelst, ctx)
        if isinstance(self.fn, OperateCall):
            val_fn2 = self.fn.run(ctx)
            fn2 = val_fn2.val
            assert isinstance(fn2, DefinedFunc)
            valuelst = [v.run(ctx) for v in self.args]
            return fn2.run(valuelst, ctx)
        assert False

class Expr_CallLater:
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        self.typ = type_unknown
    def run(self, ctx):
        lst = self.toval(self.args, ctx)
        result = self.fn(*lst)
        return Value(type_unknown, result)
    def toval(self, args, ctx):
        lst = []
        for v in args:
            if isinstance(v, Var):
                v3 = v.run(ctx)
                lst.append(v3.val)
                continue
            if isinstance(v, list):
                lst2 = self.toval(v, ctx)
                lst.append(lst2)
                continue
            lst.append(v)
        return lst

class LiuL_stmt_assign:
    def __init__(self, dest, src):
        self.dest = dest
        self.src = src
    def run(self, ctx):
        value = self.src.run(ctx)
        ctx.setvalue(self.dest.name, value)

class LiuL_stmt_funccall:
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
    def run(self, ctx):
        argvalues = [v.run(ctx) for v in self.args]
        if isinstance(self.fn, GlobalFunc):
            return self.fn.run(argvalues)
        assert False

class LiuL_stmt_return:
    def __init__(self, val):
        self.val = val
    def run(self, ctx):
        value = self.val.run(ctx)
        return value

class GlobalFunc:
    def __init__(self, name):
        self.name = name
    def run(self, values):
        if self.name == 'print':
            lst = [v.val for v in values]
            print lst
            return
        assert False

class LiuL:
    def __init__(self):
        self.funcs = {}
        self.global_funcs = {
            'print' : GlobalFunc('print')
        }
    def def_func(self, funcname, args):
        the = DefinedFunc(funcname, args, self)
        self.funcs[funcname] = the
        return the
    def run(self, fn, args):
        tovalue = [Value('int', val) for val in args]
        return fn.run(tovalue, None)
    def getvar(self, name):
        v = self.funcs.get(name)
        if v:
            return v
        return self.global_funcs.get(name)

    @staticmethod
    def ConstantInt(n):
        return Value(type_int, n)
    @staticmethod
    def op_Add(val1, val2):
        return Operate2('+', val1, val2)
    @staticmethod
    def op_Multi(val1, val2):
        return Operate2('*', val1, val2)
    @staticmethod
    def op_FuncCall(fn, args):
        return OperateCall(fn, args)
    @staticmethod
    def op_CallLater(fn, args):
        return Expr_CallLater(fn, args)
    @staticmethod
    def newstmt_assign(dest, src):
        return LiuL_stmt_assign(dest, src)
    @staticmethod
    def newstmt_funccall(fn, args):
        return LiuL_stmt_funccall(fn, args)
    @staticmethod
    def newstmt_return(val):
        return LiuL_stmt_return(val)

class RunContext:
    def __init__(self, owner):
        self.owner = owner
        self.values = {}
    def setvalue(self, name, val):
        assert isinstance(val, Value)
        self.values[name] = val
    def getvalue(self, name):
        if name in self.values:
            val = self.values.get(name)
            return val
        return self.owner.getvalue(name)

def call2_DefineAndAssign(block, name, val):
    return block.DefineAndAssign(name, val)

def call2_return(block, val):
    block.addstmt_Return(val)

def call2_funccall(block, fn, args):
    block.FuncCall(fn, args)

def call2_getvar(a, name):
    return a.getvar(name)

def call2_getdotmember(f, name):
    return getattr(f, name)

# ----------------

def make_func1(liul):
    f = liul.def_func('func1', ['b1', 'b2'])

    a1 = LiuL.ConstantInt(3)
    i = f.block.DefineAndAssign('i', a1)

    a1 = LiuL.ConstantInt(2)
    a1 = LiuL.op_Add(i, a1)
    j = f.block.DefineAndAssign('j', a1)

    a1 = LiuL.ConstantInt(2)
    a1 = LiuL.op_Multi(j, a1)
    a1 = LiuL.op_Add(i, a1)

    b1 = f.block.getvar('b1')
    b2 = f.block.getvar('b2')
    a1 = LiuL.op_Add(a1, b1)
    a1 = LiuL.op_Add(a1, b2)

    fn = f.block.getvar('print')
    f.block.FuncCall(fn, [a1, b2])

    f.block.addstmt_Return(a1)

def make_func3(liul):
    f = liul.def_func('func3', [])

    f2 = liul.getvar('func2')
    genfn = LiuL.op_FuncCall(f2, [])

    a1 = LiuL.op_FuncCall(genfn, [LiuL.ConstantInt(8), LiuL.ConstantInt(9)])

    fn_print = f.block.getvar('print')
    f.block.FuncCall(fn_print, [a1])

    a2 = LiuL.op_FuncCall(genfn, [LiuL.ConstantInt(10), LiuL.ConstantInt(9)])

    f.block.addstmt_Return(a2)

def make_func2(liul):
    f = liul.def_func('func2', [])

    fn3 = LiuL.op_CallLater(liul.def_func, ['fn1',['b1','b2']])
    fn = f.block.DefineAndAssign('fn', fn3)

    tem1 = LiuL.op_CallLater(call2_getdotmember, [fn, 'block'])
    block = f.block.DefineAndAssign('block', tem1)

    val = LiuL.op_CallLater(call2_DefineAndAssign, [block, 'i', LiuL.ConstantInt(3)])
    i = f.block.DefineAndAssign('i', val)

    val = LiuL.op_CallLater(LiuL.op_Add, [i, LiuL.ConstantInt(2)])
    j = f.block.DefineAndAssign('j', val)

    val = LiuL.op_CallLater(LiuL.op_Multi, [j, LiuL.ConstantInt(2)])
    j2 = f.block.DefineAndAssign('j2', val)

    a1 = f.block.DefineAndAssign('a1', LiuL.op_CallLater(LiuL.op_Add, [i, j2]))

    b1 = f.block.DefineAndAssign('b1', LiuL.op_CallLater(call2_getvar, [block, 'b1']))
    b2 = f.block.DefineAndAssign('b2', LiuL.op_CallLater(call2_getvar, [block, 'b2']))

    a1 = f.block.DefineAndAssign('a1', LiuL.op_CallLater(LiuL.op_Add, [a1, b1]))
    a1 = f.block.DefineAndAssign('a1', LiuL.op_CallLater(LiuL.op_Add, [a1, b2]))

    val = LiuL.op_CallLater(call2_getvar, [block, 'print'])
    fprint = f.block.DefineAndAssign('fprint', val)

    val = LiuL.op_CallLater(call2_funccall, [block, fprint, [a1, b2]])
    f.block.DefineAndAssign('nouse2', val)

    fn_val = LiuL.op_CallLater(call2_return, [block, a1])
    f.block.DefineAndAssign('nouse', fn_val)

    f.block.addstmt_Return(fn)
    return f

def test1():
    liul = LiuL()
    make_func1(liul)
    make_func2(liul)
    make_func3(liul)
    f = liul.getvar('func1')
    result = liul.run(f, [5,7])
    print result.val

    f = liul.getvar('func3')
    liul.run(f, [])

    '''
def func2():
    fn = dynamic create function fn just like func1
    return fn

def func3():
    fn3 = func2()
    print fn3(8,9)
    return fn3(10,9)

def func1(b1, b2):
    i = 3
    j = i + 2
    print i+j*2, b2
    return 55
    '''

if __name__ == '__main__':
    test1()
    print 'good'