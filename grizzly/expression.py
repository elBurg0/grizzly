import queue

from enum import Enum
class ModelType(Enum):
  TORCH = 1
  TF = 2
  ONNX = 3

class ExpressionException(Exception):
  pass

class Expr(object):
  def __init__(self, left, right, opStr):
    super().__init__()
    self.left = left
    self.right = right
    self.opStr = opStr

  def __and__(self, other):
    expr = And(self, other)
    return expr

  def __or__(self, other):
    expr = Or(self, other)
    return expr

class Param:
  def __init__(self, name: str, type: str):
    self.name = name
    self.type = type

  def __str__(self):
    return f"{self.name}:{self.type}"

class UDF(object):

  def __init__(self, name: str, params: list, lines: list, returnType: str):
    self.name = name
    self.params = params
    self.lines = lines
    self.returnType = returnType 

  def __str__(self):
    paramString = ','.join(str(p) for p in self.params)
    return f"{self.name}({paramString}): {self.returnType}"

class ModelUDF(UDF):
  def __init__(self, name: str, params: list, returnType: str, modelType:ModelType, template_replacement_dict):
    UDF.__init__(self,name, params, None, returnType)
    self.modelType = modelType
    self.templace_replacement_dict = template_replacement_dict

class FuncCall(Expr):
  def __init__(self, funcName: str, inputCols: list, df, udf: UDF, alias: str = ""):
    self.funcName = funcName
    self.inputCols = inputCols
    self.df = df
    self.udf = udf
    self.alias = alias

    super().__init__(None, None, None)

  def __str__(self):
    cols = [f"{self.df.alias}.{c.column}" for c in self.inputCols]
    colsStr = ", ".join(cols)
    s = f"{self.funcName}({colsStr})"

    if self.alias != "":
      s += f" as {self.alias}"
    
    return s

class ComputedCol(Expr):
  def __init__(self, newName, value):
    self.colname = newName
    self.value = value

    super().__init__(None, None, None)

class ColRef(Expr):
  def __init__(self, column: str, df, alias: str = ""):
    if not isinstance(column, str):
      raise ValueError(f"Invalid value for column: {column}")
    self.column = column
    self.alias = alias
    self.df = df

    super().__init__(None, None, None)

  def colName(self):
    return self.column

class Eq(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, "=")
    
class Ne(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, "<>")
  

class Gt(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, ">")

class Ge(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, ">=")

class Lt(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, "<")

class Le(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, "<=")
    

class And(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, "and")

  def __str__(self):
    return f"({self.left}) AND ({self.right})"

class Or(Expr):
  def __init__(self, left, right):
    super().__init__(left, right, "or")

  def __str__(self):
    return f"{self.left} OR {self.right}"


class ExprTraverser:
  @staticmethod
  def bf(e: Expr, visitorFunc):
    todo = queue.Queue()
    todo.put_nowait(e)

    while todo.qsize() > 0:
      current = todo.get_nowait()

      if current.left:
        todo.put_nowait(current.left)
      if current.right:
        todo.put_nowait(current.right)
      
      visitorFunc(current)

  @staticmethod
  def df(e: Expr, visitorFunc):
    todo = queue.LifoQueue()
    todo.put_nowait(e)

    while todo.qsize() > 0:
      current = todo.get_nowait()

      if current.left and isinstance(current.left, Expr):
        todo.put_nowait(current.left)
      if current.right and isinstance(current.right, Expr):
        todo.put_nowait(current.right)
      
      visitorFunc(current)