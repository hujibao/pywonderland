# -*- coding: utf-8 -*-
import os
import ctypes as ct
import pyglet.gl as gl


class Shader(object):
    """
    A helper class for compiling and communicating with shader programs.
    """
    def __init__(self, frag_files):
        """
        INPUTS:
            - `vert_files`: a list of files that contain the vertex shader code.
            - `frag_files`: a list of files that contain the fragment shader code.
        """
        self.program = gl.glCreateProgram()
        self.compile_and_attach_shader(['default.vert'], gl.GL_VERTEX_SHADER)
        self.compile_and_attach_shader(frag_files, gl.GL_FRAGMENT_SHADER)
        self.link()

    def compile_and_attach_shader(self, shader_files, shader_type):
        """
        INPUTS:

            - `shader_files`: a list of the shader files.

            - `shader_type`: must be `GL_VERTEX_SHADER` or `GL_FRAGMENT_SHADER`.

        Main steps to compile and attach a shader:
        1. glCreateShader:
                create a shader of given type.
        2. glShaderSource:
                load source code into the shader.
        3. glCompileShader:
                compile the shader.
        4. glGetShaderiv:
                retrieve the compile status.
        5. glGetShaderInfoLog:
                print the error info if compiling failed.
        6. glAttachShader:
                attach the shader to our program if compiling successed.
        """
        src = []
        for src_f in shader_files:
            try:
                with open(src_f, 'r') as f:
                    src.append(f.read().encode('ascii'))
            except:
                src_f = os.path.dirname(__file__) + '/glsl/' + src_f
                with open(src_f, 'r') as f:
                    src.append(f.read().encode('ascii'))  

        # 1. create a shader
        shader = gl.glCreateShader(shader_type)

        # 2. load source code into the shader
        src_p = (ct.c_char_p * len(src))(*src)
        gl.glShaderSource(shader, len(src), ct.cast(ct.pointer(src_p), ct.POINTER(ct.POINTER(ct.c_char))), None)

        # 3. compile the shader
        gl.glCompileShader(shader)

        # 4. retrieve the compile status
        compile_status = gl.GLint(0)
        gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS, ct.byref(compile_status))

        # 5. if compiling failed then print the error log
        if not compile_status:
            info_length = gl.GLint(0)
            gl.glGetShaderiv(shader, gl.GL_INFO_LOG_LENGTH, ct.byref(info_length))
            error_info = ct.create_string_buffer(info_length.value)
            gl.glGetShaderInfoLog(shader, info_length, None, error_info)
            print(error_info.value)

        # 6. else attach the shader to our program
        else:
            gl.glAttachShader(self.program, shader)
            gl.glDeleteShader(shader)

    def link(self):
        """
        Main steps to link the program:
        1. glLinkProgram:
                linke the shaders in the program to create an executable
        2. glGetProgramiv:
                retrieve the link status
        3. glGetProgramInfoLog:
                print the error log if link failed
        """
        gl.glLinkProgram(self.program)

        link_status = gl.GLint(0)
        gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS, ct.byref(link_status))

        if not link_status:
            info_length = gl.GLint(0)
            gl.glGetProgramiv(self.program, gl.GL_INFO_LOG_LENGTH, ct.byref(info_length))
            error_info = ct.create_string_buffer(info_length.value)
            gl.glGetProgramInfoLog(self.program, info_length, None, error_info)
            print(error_info.value)

    def bind(self):
        gl.glUseProgram(self.program)

    def unbind(self):
        gl.glUseProgram(0)

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.unbind()

    def uniformi(self, name, *data):
        location = gl.glGetUniformLocation(self.program, name.encode('ascii'))
        {1: gl.glUniform1i,
         2: gl.glUniform2i,
         3: gl.glUniform3i,
         4: gl.glUniform4i
        }[len(data)](location, *data)

    def uniformf(self, name, *data):
        location = gl.glGetUniformLocation(self.program, name.encode('ascii'))
        {1: gl.glUniform1f,
         2: gl.glUniform2f,
         3: gl.glUniform3f,
         4: gl.glUniform4f
        }[len(data)](location, *data)

    def uniformfv(self, name, size, data):
        data_ctype = (gl.GLfloat * len(data))(*data)
        location = gl.glGetUniformLocation(self.program, name.encode('ascii'))
        {1: gl.glUniform1fv,
         2: gl.glUniform2fv,
         3: gl.glUniform3fv,
         4: gl.glUniform4fv
        }[len(data) // size](location, size, data_ctype)

    def vertex_attrib(self, name, data, size=2, stride=0, offset=0):
        """
        Set vertex attribute data in a shader, lacks the flexibility of
        setting several attributes in one vertex buffer.

        INPUTS:

            - `name`: the attribute name in the shader.

            - `data`: a list of vertex attributes (positions, colors, ...)

        Example: name = 'positions', data = [0, 0, 0, 1, 1, 0, 1, 1].
        """
        data_ctype = (gl.GLfloat * len(data))(*data)

        vbo_id = gl.GLuint(0)
        gl.glGenBuffers(1, ct.byref(vbo_id))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_id)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, ct.sizeof(data_ctype), data_ctype, gl.GL_STATIC_DRAW)

        location = gl.glGetAttribLocation(self.program, name.encode('ascii'))
        gl.glEnableVertexAttribArray(location)
        gl.glVertexAttribPointer(location, size, gl.GL_FLOAT, gl.GL_FALSE, stride, ct.c_void_p(offset))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        return vbo_id