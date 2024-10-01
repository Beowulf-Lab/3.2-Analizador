from flask import Flask, request, render_template
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

# Definir los tokens para el lexer
tokens = ['RESERVED', 'IDENTIFIER', 'LBRACE', 'RBRACE', 'LPAREN', 'RPAREN', 'SEMICOLON', 'NUMBER']

# Lista de palabras reservadas
reserved = {
    'for': 'RESERVED',
    'while': 'RESERVED',
    'if': 'RESERVED',
    'else': 'RESERVED',
    'int': 'RESERVED',  # Modificado para que 'int' sea palabra reservada
    'main': 'RESERVED',  # 'main' como palabra reservada
}

# Expresiones regulares para símbolos y números
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMICOLON = r';'

# Expresión regular para números
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Expresión regular para identificadores
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')  # Reservamos palabras clave como 'main' o 'int'
    return t

# Ignorar espacios y tabs
t_ignore = ' \t'

# Manejar saltos de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Definir el manejador de errores léxicos
def t_error(t):
    error_message = f"Caracter ilegal '{t.value[0]}' en la línea {t.lexer.lineno}"
    t.lexer.skip(1)
    return error_message

# Crear el lexer
lexer = lex.lex()

# Reglas gramaticales para analizar funciones
def p_function(p):
    '''function : RESERVED RESERVED LPAREN RPAREN LBRACE block RBRACE'''
    p[0] = ('function', p[2], p[6])  # El segundo RESERVED es el nombre de la función

# Reglas gramaticales para el bloque de código dentro de la función
def p_block(p):
    '''block : statement block
             | statement'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

# Reglas gramaticales para la declaración de variables
def p_statement_declaration(p):
    '''statement : RESERVED IDENTIFIER SEMICOLON'''
    p[0] = ('declaration', p[1], p[2])

# Manejo de errores sintácticos
def p_error(p):
    if p:
        error_message = f"Error sintáctico en '{p.value}' en la línea {p.lineno}"
        raise SyntaxError(error_message)
    else:
        raise SyntaxError("Error sintáctico al final de la entrada")
# Crear el parser
parser = yacc.yacc()

# Función para analizar el texto léxicamente
def lexico(text):
    lines = text.splitlines()
    tokens_list = []
    line_info = []
    error_lexico = None  # Para capturar los errores léxicos

    for i, line in enumerate(lines, start=1):
        lexer.input(line)
        while True:
            tok = lexer.token()
            if not tok:
                break  # No más tokens en la línea actual
            if isinstance(tok, str):  # Si el error fue retornado
                error_lexico = tok  # Capturamos el error léxico
                break
            tokens_list.append((i, tok.type, tok.value))
            
            # Distinguir tipos de símbolos, palabras reservadas y otros tokens
            if tok.type == 'RESERVED':
                tipo_palabra = 'Palabra Reservada'
            elif tok.type == 'IDENTIFIER':
                tipo_palabra = 'Identificador'
            elif tok.type == 'NUMBER':
                tipo_palabra = 'Número'
            elif tok.type == 'LBRACE':
                tipo_palabra = 'Llave Izquierda'
            elif tok.type == 'RBRACE':
                tipo_palabra = 'Llave Derecha'
            elif tok.type == 'LPAREN':
                tipo_palabra = 'Paréntesis Izquierdo'
            elif tok.type == 'RPAREN':
                tipo_palabra = 'Paréntesis Derecho'
            elif tok.type == 'SEMICOLON':
                tipo_palabra = 'Punto y Coma'
            else:
                tipo_palabra = 'Símbolo Desconocido'

            line_info.append((i, tipo_palabra, tok.value))

    return tokens_list, line_info, error_lexico

# Función para el análisis sintáctico
def sintactico(tokens_list):
    sintactico_info = []
    token_values = ' '.join([str(t[2]) for t in tokens_list])
    lines = [t[0] for t in tokens_list]

    try:
        result = parser.parse(token_values)
        if result:
            sintactico_info.append((lines[0], 'Correcto', result))
    except SyntaxError as e:
        sintactico_info.append((lines[0], 'Error', str(e)))

    return sintactico_info

@app.route('/', methods=['GET', 'POST'])
def index():
    error_message = None
    if request.method == 'POST':
        text = request.form['text']
        tokens, line_info, error_lexico = lexico(text)

        # Si hay error léxico, no seguimos con el análisis sintáctico
        if error_lexico:
            error_message = error_lexico
            sintactico_info = []
        else:
            sintactico_info = sintactico(tokens)

        # Verificar si hay errores en la información sintáctica
        if sintactico_info and 'Error' in sintactico_info[0]:
            error_message = sintactico_info[0][2]  # Obtener el mensaje de error

        return render_template('index.html', tokens=tokens, line_info=line_info, sintactico_info=sintactico_info, error_message=error_message, text=text)

    return render_template('index.html', tokens=None, line_info=None, sintactico_info=None, error_message=None, text='')

if __name__ == '__main__':
    app.run(debug=True)