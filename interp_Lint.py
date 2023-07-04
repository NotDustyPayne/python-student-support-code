from ast import *
from utils import input_int, add64, sub64, neg64

def pe_neg(r):
  match r:
    case Constant(n):
      return Constant(neg64(n))
    case _:
      return UnaryOp(USub(), r)
     

def pe_add(r1, r2):
  match (r1, r2):
    case (Constant(n1), Constant(n2)):
        return Constant(add64(n1, n2))
    case _:
      return BinOp(r1, Add(), r2)
     
def pe_sub(r1, r2):
   match (r1, r2):
    case (Constant(n1), Constant(n2)):
      return Constant(sub64(n1, n2))
    case _:
      return BinOp(r1, Sub(), r2)

def pe_exp(e):
  match e:
    case BinOp(left, Add(), right):
      return pe_add(pe_exp(left), pe_exp(right))
    case BinOp(left, Sub(), right):
      return pe_sub(pe_exp(left), pe_exp(right))
    case UnaryOp(USub(), v):
      return pe_neg(pe_exp(v))
    case Constant(value):
      return e
    case Call(Name('input_int'), []):
      return e
     
def pe_stmt(s):
  match s:
    case Expr(Call(Name('print'), [arg])):
      return Expr(Call(Name('print'), [pe_exp(arg)]))
    case Expr(value):
      return Expr(pe_exp(value))


def pe_P_int(p):
  match p:
    case Module(body):
      new_body = [pe_stmt(s) for s in body]
      return Module(new_body)
         

def interp_exp(e):
    match e:
        case BinOp(left, Add(), right):
            l = interp_exp(left); r = interp_exp(right)
            return add64(l, r)
        case BinOp(left, Sub(), right):
            l = interp_exp(left); r = interp_exp(right)
            return sub64(l, r)
        case UnaryOp(USub(), v):
            return neg64(interp_exp(v))
        case Constant(value):
            return value
        case Call(Name('input_int'), []):
            return input_int()
        case _:
            raise Exception('error in interp_exp, unexpected ' + repr(e))

def interp_stmt(s):
    match s:
        case Expr(Call(Name('print'), [arg])):
            print(interp_exp(arg))
        case Expr(value):
            interp_exp(value)
        case _:
            raise Exception('error in interp_stmt, unexpected ' + repr(s))

def interp(p):
    match p:
        case Module(body):           
            for s in body:
                interp_stmt(s)
        case _:
            raise Exception('error in interp, unexpected ' + repr(p))

# This version is for InterpLvar to inherit from 
class InterpLint:
  def interp_exp(self, e, env):
    match e:
      case BinOp(left, Add(), right):
        l = self.interp_exp(left, env); r = self.interp_exp(right, env)
        return add64(l, r)
      case BinOp(left, Sub(), right):
        l = self.interp_exp(left, env); r = self.interp_exp(right, env)
        return sub64(l, r)
      case UnaryOp(USub(), v):
        return neg64(self.interp_exp(v, env))
      case Constant(value):
        return value
      case Call(Name('input_int'), []):
        return input_int()
      case _:
        raise Exception('error in interp_exp, unexpected ' + repr(e))

  # The cont parameter is a list of statements that are the
  # continuaton of the current statement s.
  # We use this continuation-passing approach because
  # it enables the handling of Goto in interp_Cif.py.
  def interp_stmt(self, s, env, cont):
    match s:
      case Expr(Call(Name('print'), [arg])):
        val = self.interp_exp(arg, env)
        print(val, end='')
        return self.interp_stmts(cont, env)
      case Expr(value):
        self.interp_exp(value, env)
        return self.interp_stmts(cont, env)
      case _:
        raise Exception('error in interp_stmt, unexpected ' + repr(s))
    
  def interp_stmts(self, ss, env):
    match ss:
      case []:
        return 0
      case [s, *ss]:
        return self.interp_stmt(s, env, ss)

  def interp(self, p):
    match p:
      case Module(body):
        self.interp_stmts(body, {})
      case _:
        raise Exception('error in interp, unexpected ' + repr(p))
    
if __name__ == "__main__":
  eight = Constant(8)
  neg_eight = UnaryOp(USub(), eight)
  read = Call(Name('input_int'), [])
  ast1_1 = BinOp(read, Add(), neg_eight)
  pr = Expr(Call(Name('print'), [ast1_1]))
  p = Module([pr])
  interp(p)


# 1.1, verify partial eval is the same as regular eval with 3 programs
# because statements in Lint are evaluated but the results are ignored, Im just manually checking
# this. (interp results do not get returned)

p1 = BinOp(BinOp(Constant(7), Add(), Constant(1)), Add(), BinOp( Constant(10),Sub(), Constant(4)))
p2 = UnaryOp(USub(), BinOp(Constant(32), Sub(), Constant(14)))
p3 = BinOp(BinOp(Constant(7), Add(), Constant(1)), Add(), UnaryOp(USub(), Constant(3)))

programs = [p1,p2,p3]

def partials_test():
   for program in programs:
      normal_p = Module([Expr(Call(Name('print'), [program]))])
      partial_p = pe_P_int(Module([Expr(Call(Name('print'), [program]))]))
      print(f"result of program {program} :")
      interp(normal_p)
      interp(partial_p)

