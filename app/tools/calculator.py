import re
import numpy as np
import math
from typing import Union, List, Set
from app.models.schemas import ToolResult
from app.models.enums import ToolType
from app.utils.logger import log_tool_usage, logger

class Calculator:
    """Basic arithmetic calculator tool with fallback to Python eval"""
    
    def __init__(self):
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y,
            'sqrt': lambda x: np.sqrt(x),
            'sin': lambda x: np.sin(x),
            'cos': lambda x: np.cos(x),
            'tan': lambda x: np.tan(x)
        }
        # Add mathematical constants
        self.constants = {
            'π': np.pi,
            'pi': np.pi,
            'e': np.e,
            'inf': float('inf'),
            'infinity': float('inf'),
            'nan': float('nan')
        }
        # Safe names for eval fallback
        self.safe_names = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'math': math,
            'np': np
        }
        # Update safe_names with our constants
        self.safe_names.update(self.constants)
    
    def calculate(self, expression: str) -> Union[float, str]:
        """Calculate the result of a mathematical expression with fallback to eval."""
        try:
            # Clean up pi symbol variations
            expression = expression.replace('Ï€', 'pi').replace('π', 'pi')
            logger.info(f"Cleaned expression: {expression}")
            
            # First try our custom calculator
            result = self._try_custom_calculator(expression)
            if isinstance(result, (int, float)):
                logger.info(f"Custom calculator result: {result}")
                return result
            
            # If custom calculator fails, try eval fallback
            logger.info(f"Custom calculator failed, trying eval fallback for: {expression}")
            return self._eval_fallback(expression)
            
        except Exception as e:
            logger.error(f"Calculator error: {str(e)}")
            return f"Error in calculation: {str(e)}"
    
    def _try_custom_calculator(self, expression: str) -> Union[float, str]:
        """Try to calculate using our custom calculator implementation."""
        try:
            # Clean the expression
            expression = expression.lower().strip()
            logger.info(f"Processing expression in custom calculator: {expression}")
            
            # Replace mathematical constants with their values
            for const, value in self.constants.items():
                if const in expression:
                    logger.info(f"Replacing constant {const} with {value}")
                    expression = expression.replace(const.lower(), str(value))
            
            # Handle special functions
            if 'sqrt' in expression:
                num = float(re.findall(r'sqrt\((\d+)\)', expression)[0])
                result = self.operators['sqrt'](num)
                logger.info(f"Calculated sqrt({num}) = {result}")
                return result
            
            # Handle trigonometric functions
            for func in ['sin', 'cos', 'tan']:
                if func in expression:
                    num = float(re.findall(rf'{func}\((\d+)\)', expression)[0])
                    result = self.operators[func](np.radians(num))
                    logger.info(f"Calculated {func}({num}) = {result}")
                    return result
            
            # Handle basic arithmetic
            # First, evaluate expressions in parentheses
            while '(' in expression:
                inner_expr = re.findall(r'\(([^()]+)\)', expression)[0]
                logger.info(f"Evaluating inner expression: {inner_expr}")
                inner_result = self._evaluate_basic(inner_expr)
                expression = expression.replace(f'({inner_expr})', str(inner_result))
                logger.info(f"Expression after inner evaluation: {expression}")
            
            result = self._evaluate_basic(expression)
            logger.info(f"Final calculation result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Custom calculator failed: {str(e)}")
            return str(e)
    
    def _eval_fallback(self, expression: str) -> float:
        """Fallback calculation using Python's eval with safety measures."""
        try:
            # Clean and prepare the expression
            expr = expression.lower().strip()
            
            # Replace mathematical constants
            for const, value in self.constants.items():
                expr = expr.replace(const.lower(), str(value))
            
            # Replace ^ with ** for exponentiation
            expr = expr.replace('^', '**')
            
            # Validate the expression contains only allowed characters
            allowed_chars = set('0123456789+-*/().e^ ')
            if not all(c in allowed_chars or c.isalpha() for c in expr):
                raise ValueError("Expression contains invalid characters")
            
            # Create a safe environment for eval
            safe_env = self.safe_names.copy()
            
            # Evaluate the expression
            result = eval(expr, {"__builtins__": {}}, safe_env)
            
            # Validate the result
            if not isinstance(result, (int, float)):
                raise ValueError("Expression did not evaluate to a number")
            
            return float(result)
            
        except Exception as e:
            logger.error(f"Eval fallback failed: {str(e)}")
            raise ValueError(f"Could not evaluate expression: {str(e)}")
    
    def _evaluate_basic(self, expression: str) -> float:
        """Evaluate a basic arithmetic expression without parentheses."""
        # Split the expression into numbers and operators
        tokens = re.findall(r'(\d+\.?\d*|\+|\-|\*|\/|\^)', expression)
        
        # Convert numbers to float
        for i in range(len(tokens)):
            if tokens[i] not in self.operators:
                tokens[i] = float(tokens[i])
        
        # Handle exponentiation first
        i = 0
        while i < len(tokens):
            if tokens[i] == '^':
                result = self.operators['^'](tokens[i-1], tokens[i+1])
                tokens[i-1:i+2] = [result]
                i -= 1
            i += 1
        
        # Handle multiplication and division
        i = 0
        while i < len(tokens):
            if tokens[i] in ['*', '/']:
                result = self.operators[tokens[i]](tokens[i-1], tokens[i+1])
                tokens[i-1:i+2] = [result]
                i -= 1
            i += 1
        
        # Handle addition and subtraction
        i = 0
        while i < len(tokens):
            if tokens[i] in ['+', '-']:
                result = self.operators[tokens[i]](tokens[i-1], tokens[i+1])
                tokens[i-1:i+2] = [result]
                i -= 1
            i += 1
        
        return tokens[0]

# Global instance
calculator = Calculator()