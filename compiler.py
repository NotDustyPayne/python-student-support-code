import ast
from ast import *
from utils import *
from x86_ast import *
import os
from typing import List, Tuple, Dict, Optional

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
                atomic, temps = self.rco_exp(exp, True)
                unary_stub = Name(generate_name('unary_op'))
                return unary_stub, temps + [(unary_stub, atomic)]

            case BinOp(left_exp,Add(), right_exp):
                left_atomic, left_temps = self.rco_exp(left_exp, True)
                right_atomic, right_temps = self.rco_exp(right_exp, True)

                add_stub_var = Name(generate_name('binop_plus'))
                new_exp = BinOp(left_atomic, Add(), right_atomic)

                bob = add_stub_var, left_temps + right_temps +[(add_stub_var, new_exp)]
                return bob

            case BinOp(left_exp, Sub(), right_exp):
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
                return [self.temps_helper(name,xpr) for name,xpr in temps]
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
        match e:
            case Constant(n):
                return Immediate(n)
            case Name(var):
                return Variable(var)
            case _:
                raise Exception('TODO: handle non basic type?')

    def assign_instruction(self, e: expr, v: Optional[str] = None) -> List[instr]:
        match e:
            case BinOp(left_exp, Add(), right_exp):
                return [
                    Instr('movq', [self.select_arg(left_exp), Variable(v) if v else Reg('rax')]),
                    Instr('addq', [self.select_arg(right_exp), Variable(v) if v else Reg('rax')])
                ]
            case BinOp(left_exp, Sub(), right_exp):
                return [
                    Instr('movq', [self.select_arg(left_exp), Variable(v) if v else Reg('rax')]),
                    Instr('subq', [self.select_arg(right_exp), Variable(v) if v else Reg('rax')])
                ]
            case UnaryOp(USub(), exp):
                return [Instr('negq', [self.select_arg(exp), Variable(v) if v else Reg('rax')])]
            case Call(Name('input_int'), []):
                # TODO: fix this, doesn't really make sense the optional V doesn't really make sense to me
                return [Callq(label_name('read_int'),0), Instr('movq', [Reg('rax'), Variable(v) if v else Reg('rax')])]
            case Constant(n):
                return [Instr('movq', [Immediate(n), Variable(v) if v else Reg('rax')])]
            case Name(n):
                return [Instr('movq', [Variable(n), Variable(v) if v else Reg('rax')])]
        return []

    def select_stmt(self, s: stmt) -> List[instr]:
        match s:
            case Assign([Name(var)], exp):
                return self.assign_instruction(exp, var)
            case Expr(Call(Name('print'), [Name(var)])):
                return [
                    Instr('movq', [Variable(var), Reg('rdi')]),
                    Callq(label_name('print_int'), 1)
                ]
            case Expr(Call(Name('print'), [Constant(n)])):
                return [
                    Instr('movq', [Immediate(n), Reg('rdi')]),
                    Callq(label_name('print_int'), 1)
                ]
            case Expr(exp):
                return self.assign_instruction(exp)
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
        if isinstance(a, Variable):
            if home.get(a, None) is not None:
                return home[a]
            else:
                new_offset = -(1 + len(home)) * 8 # TODO: explanation
                home[a] = Deref('rbp', new_offset)
                return home[a]
        return a

    def assign_homes_instr(self, i: instr,home: Dict[Variable, arg]) -> instr:
        # YOUR CODE HERE
        new_args = []

        if isinstance(i, Instr):
            for arg in i.args:
                new_args += [self.assign_homes_arg(arg, home)]
            return Instr(i.instr, new_args)
        return i

    def assign_homes_instrs(self, ss: List[instr], home: Dict[Variable, arg]) -> Tuple[List[instr], int]:
        # YOUR CODE HERE
        assigned_instruction_list: List[instr] = []

        for instruction in ss:
            assigned_instruction_list += [self.assign_homes_instr(instruction, home)]

        stack_size = len(home.keys()) * 8
        stack_size += stack_size % 16

        return assigned_instruction_list, stack_size


    def assign_homes(self, p: X86Program) -> X86Program:
        assigned_instrs, stack_size = self.assign_homes_instrs(p.body, {})
        return X86Program(body=assigned_instrs, stack_size=stack_size)

    ############################################################################
    # Patch Instructions
    ############################################################################


    def instr_has_multiple_var_refs(self, i: Instr) -> bool:
        var_ref_counts = 0

        for arg in i.args:
            match arg:
                case Immediate(v):
                    pass
                case Reg(id):
                    pass
                case Deref(reg,v):
                    var_ref_counts += 1

        return var_ref_counts > 1
    
    def patch_instr(self, i: Instr) -> List[instr]:
        # YOUR CODE HERE
        if self.instr_has_multiple_var_refs(i):
            # return self.expand_instr(i)
            return [
                Instr('movq', [ i.source(), Reg('rdx')]),
                Instr(i.instr, [Reg('rdx'), i.target()])
            ]
        else:
            return [i]

    def patch_instrs(self, ss: List[instr]) -> List[instr]:
        # YOUR CODE HERE
        patched_instrs = []
        for inst in ss:
            if isinstance(inst, Instr) and inst.instr in ('movq', 'addq', 'subq'):
                patched_instrs += self.patch_instr(inst)
            else:
                patched_instrs.append(inst)
        return patched_instrs


    def patch_instructions(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE
        body = p.body
        stack_size = p.stack_size

        if isinstance(body, Dict):
            raise Exception('dusty5 :: body type is dict[str, list[instr], throw for now')

        patched_instrs = self.patch_instrs(body)
        return X86Program(body=patched_instrs, stack_size=stack_size)


    ############################################################################
    # Prelude & Conclusion
    ############################################################################

    def prelude_and_conclusion(self, p: X86Program) -> X86Program:
        # YOUR CODE HERE

        stack_size = p.stack_size or 0

        prelude = [
            Instr('pushq', [Reg('rbp')]),
            Instr('movq', [Reg('rsp'), Reg('rbp')]),
            Instr('subq', [Immediate(stack_size), Reg('rsp')])
        ]

        conclusion = [
            Instr('addq', [Immediate(stack_size), Reg('rsp')]),
            Instr('popq', [Reg('rbp')]),          
            Retq()
        ]

        base_instrs = p.body
        return X86Program(body = prelude + base_instrs + conclusion, stack_size=p.stack_size)
