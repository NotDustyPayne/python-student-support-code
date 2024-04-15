import ast
from ast import *
from utils import *
from x86_ast import *
import os
from typing import List, Tuple, Set, Dict

Binding = Tuple[Name, expr]
Temporaries = List[Binding]


class Compiler:

    ############################################################################
    # Remove Complex Operands
    ############################################################################


    def temps_helper(self, temp_name, temp_expr):
        """
        makes each temp binding an assignment statement
        """
        return Assign([temp_name], temp_expr)

    def rco_exp(self, e: expr, need_atomic: bool) -> Tuple[expr, Temporaries]:
        # YOUR CODE HERE
        """
        use utils.generate_name for fresh stub names
        """
        if need_atomic is False:
            return (e,[])
        match e:
            # atomics
            case Constant(n):
                return (Constant(n), [])
            case Name(var):
                return (Name(var), [])
            # expressions
            case Call(Name('input_int'), []):
                input_var = Name(generate_name('input_int_var'))
                return input_var, [(input_var, Call(Name('input_int'), []))]
            case UnaryOp(USub(), exp):
                # -10 -> tmp1, [(tmp1, -10)]
                atomic, temps = self.rco_exp(exp, True)
                unary_stub = Name(generate_name('unary_op'))
                return unary_stub, temps + [(unary_stub, atomic)]
            
            case BinOp(left_exp,Add(), right_exp):
                left_atomic, left_temps = self.rco_exp(left_exp, True)
                right_atomic, right_temps = self.rco_exp(right_exp, True)

                add_stub_var = Name(generate_name('binop_plus'))                
                new_exp = BinOp(left_atomic, Add(), right_atomic)

                return add_stub_var, left_temps + right_temps +[(add_stub_var, new_exp)]     

            case BinOp(left_exp,Sub(), right_exp):
                left_atomic, left_temps = self.rco_exp(left_exp, True)
                right_atomic, right_temps = self.rco_exp(right_exp, True)

                sub_stub_var = Name(generate_name('binop_sub'))                
                new_exp = BinOp(left_atomic, Sub(), right_atomic)

                return sub_stub_var, left_temps + right_temps + [(sub_stub_var, new_exp)] 

        raise Exception('rco_exp error')

    def rco_stmt(self, s: stmt) -> List[stmt]:

        match s:
            case Assign([Name(var)], exp):
                expression, temps = self.rco_exp(exp, False)
                return [self.temps_helper(name, xpr) for name,xpr in temps] + [Assign([Name(var)], expression)]
            case Expr(Call(Name('print'), [exp])):
                atomic_exp, temps = self.rco_exp(exp, True)
                return [self.temps_helper(name,xpr) for name,xpr in temps] + [Expr(Call(Name('print'), [atomic_exp]))]
            case Expr(exp):
                atomic_exp, temps = self.rco_exp(exp, True)
                return [self.temps_helper(name,xpr) for name,xpr in temps] + [atomic_exp]
        raise Exception('rco_stmt error')

    def remove_complex_operands(self, p: Module) -> Module:
        match p:
            case Module(body):
                rco_stmts = []
                for stmt in body:
                    rco_stmts += self.rco_stmt(stmt)
                return Module(rco_stmts)
            case _:
                raise Exception('remove_complex_operands error')
        

    ############################################################################
    # Select Instructions
    ############################################################################

    def select_arg(self, e: expr) -> arg:
        # YOUR CODE HERE
        match e:
            case Constant(n):
                print('Constant case, value is ', n)
                return Immediate(n)
            case Name(var):
                print('Variable case, value is ', var)
                return Variable(var)
            case _:
                raise Exception('todo: handle non basic type?')

    def assign_instruction_to_variable(self, e: expr, v: str) -> List[instr]:
        match e:
            case BinOp(left_exp, Add(), right_exp):
                _left = self.select_arg(left_exp)
                _right = self.select_arg(right_exp)
                return [
                    Instr('movq', [_left, Variable(v)]),
                    Instr('addq', [_right, Variable(v)])
                ]
        pass

    def select_stmt(self, s: stmt) -> List[instr]:
        # YOUR CODE HERE
        match s:
            case Assign([Name(var)], exp):
                return self.assign_instruction_to_variable(exp, var)

            case Expr(Call(Name('print'), [exp])):
                return [
                    Instr('movq', [self.select_arg(exp), Reg('rdi')]),
                    Callq(label_name('print_int'), 1)
                ]

            case Expr(exp):
                print(f"case 3")
                pass
        raise Exception('select_stmt error')    

    def select_instructions(self, p: Module) -> X86Program:
        # YOUR CODE HERE
        match p:
            case Module(body):
                select_stmts = []
                for stmt in body:
                    select_stmts += self.select_stmt(stmt)
                return X86Program(select_stmts)
            case _:
                raise Exception('select_stmts error')

    ############################################################################
    # Assign Homes
    ############################################################################

    def assign_homes_arg(self, a: arg, home: Dict[Variable, arg]) -> arg:
        # YOUR CODE HERE
        pass        

    def assign_homes_instr(self, i: instr,
                           home: Dict[Variable, arg]) -> instr:
        # YOUR CODE HERE
        pass        

    def assign_homes_instrs(self, ss: List[instr],
                            home: Dict[Variable, arg]) -> List[instr]:
        # YOUR CODE HERE
        pass        

    # def assign_homes(self, p: X86Program) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

    ############################################################################
    # Patch Instructions
    ############################################################################

    def patch_instr(self, i: instr) -> List[instr]:
        # YOUR CODE HERE
        pass        

    def patch_instrs(self, ss: List[instr]) -> List[instr]:
        # YOUR CODE HERE
        pass        

    # def patch_instructions(self, p: X86Program) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    # def prelude_and_conclusion(self, p: X86Program) -> X86Program:
    #     # YOUR CODE HERE
    #     pass        

