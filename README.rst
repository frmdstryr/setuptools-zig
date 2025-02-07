Setuptools-Zig
==============

.. image:: https://sourceforge.net/p/setuptools-zig/code/ci/default/tree/_doc/_static/license.svg?format=raw
   :target: https://opensource.org/licenses/MIT

.. image:: https://sourceforge.net/p/setuptools-zig/code/ci/default/tree/_doc/_static/pypi.svg?format=raw
   :target: https://pypi.org/project/setuptools-zig/

.. image:: https://sourceforge.net/p/oitnb/code/ci/default/tree/_doc/_static/oitnb.svg?format=raw
   :target: https://bitbucket.org/ruamel/oitnb/


A setuptools extension for building cpython extensions written in Zig and/or C, with the `Zig compiler <https://ziglang.org>`_.

This extension expects to find the ``zig`` command in your ``PATH``. If it is not
there, or if you need to select a specific version, you can set the environment
variable ``PY_ZIG`` to% the full path of the executable. E.g.::

   PY_VER=/usr/local/bin/zig

This versio of the module has been updated to Zig 0.10.0, but should work with other versions (as long as you adapt your Zig code).
It has been tested with Python 3.7 - 3.11, on Ubuntu 22.4 (binary zig install) and macOS 13.0.1 (brew install).

The package ``setuptools-zig`` is available on PyPI, but **doesn't need to be
installed**, as it is a setup requirement. Once your ``setup.py`` has the apropriate
entries, building an ``sdist`` or ``bdist_wheel`` will automatically downloaded the
package (cached in the .eggs directory).

Setup.py
++++++++

Your ``setup.py`` file should look like::

  from setuptools import Extension
  from setuptools import setup

  setup(
      name=NAME,
      version='MAJ.MIN.PATCH',
      python_requires='>=3.7.15%',
      build_zig=True,
      ext_modules=[Extension(NAME, [XX1, XX2])],
      setup_requires=['setuptools-zig'],
  )

with ``NAME`` replaced by the string that is your package name. MAJ, MIN, and PATCH
your package's version, and XX1, XX2 being your source files (you can have just
one, or more).

With that adapted to your project::

  python setup.py bdist_wheel

will result in a ``.whl`` file in your ``dist`` directory. That wheel file can be installed in a virtualenv,
and the functions defined in the package imported and used. By default the compile and/or link commands executed
will be shown, their output only when errors occur. Verbosity can be increased specifying `-v` or `-vv`, after `bdist_wheel`.


Using Zig as a C compiler
+++++++++++++++++++++++++

Create your ``setup.py``::

  from setuptools import Extension
  from setuptools import setup
  
  setup(
      name='c_sum',
      version='1.0.0',
      python_requires='>=3.7.15',
      build_zig=True,
      ext_modules=[Extension('c_sum', ['sum.c', ])],
      setup_requires=['setuptools-zig'],

and ``sum.c``::

  /* based on https://docs.python.org/3.9/extending/extending.html */
   
  #define PY_SSIZE_T_CLEAN
  #include <Python.h>
  
  PyObject* sum(PyObject* self, PyObject* args) {
      long a, b;
  
      if (!PyArg_ParseTuple(args, "ll", &a, &b))
  	      return NULL;
      return PyLong_FromLong(a+b);
  }
  
  
  static struct PyMethodDef methods[] = {
      {"sum", (PyCFunction)sum, METH_VARARGS},
      {NULL, NULL}
  };
  
  static struct PyModuleDef zigmodule = {
      PyModuleDef_HEAD_INIT,
      "sum",
      NULL,
      -1,
      methods
  };
  
  PyMODINIT_FUNC PyInit_c_sum(void) {
      return PyModule_Create(&zigmodule);

install the resulting wheel using ``pip`` and use::

  python -c "from c_sum import sum; print(sum(20, 22))"

Using Zig with .zig and .c
++++++++++++++++++++++++++

The Zig compiler can easily mix and match (see section macOS), here we use the C code to provide the
interface and do the heavy lifting of calculating the sum in Zig.

``setup.py``::

  from setuptools import Extension
  from setuptools import setup
  
  setup(
      name='c_zig_sum',
      version='1.0.0',
      python_requires='>=3.7.15',
      build_zig=True,
      ext_modules=[Extension('c_zig_sum', ['c_int.c', 'sum.zig', ])],
      setup_requires=['setuptools-zig'],
  )

``c_int.c``::

  /* based on https://docs.python.org/3.9/extending/extending.html */
   
  #define PY_SSIZE_T_CLEAN
  #include <Python.h>
  
  PyObject* sum(PyObject* , PyObject*);
  
  /*
  PyObject* sum(PyObject* self, PyObject* args) {
      long a, b;
  
      if (!PyArg_ParseTuple(args, "ll", &a, &b))
          return NULL;
      return PyLong_FromLong(a+b);
  }
  */
  
  
  static struct PyMethodDef methods[] = {
      {"sum", (PyCFunction)sum, METH_VARARGS},
      {NULL, NULL}
  };
  
  static struct PyModuleDef zigmodule = {
      PyModuleDef_HEAD_INIT,
      "c_zig_sum",
      NULL,
      -1,
      methods
  };
  
  PyMODINIT_FUNC PyInit_c_zig_sum(void) {
      return PyModule_Create(&zigmodule);
  }

``sum.zig``::

  const c = @cImport({
      @cDefine("PY_SSIZE_T_CLEAN", "1");
      @cInclude("Python.h");
  });
  
  pub export fn sum(self: [*]c.PyObject, args: [*]c.PyObject) [*c]c.PyObject {
      var a: c_long = undefined;
      var b: c_long = undefined;
      _ = self;
      if (!(c._PyArg_ParseTuple_SizeT(args, "ll", &a, &b) != 0)) return null;
      return c.PyLong_FromLong((a + b));
  

Zig code only
+++++++++++++

The orignal converted code is rather ugly to read. 
There were no differences in the program specific Zig code converted from C between 
Python 3.7/3.8/3.9/3.10/3.11 (but there was of course in the header).
This is a initial attempt to clean things up. Only the part under the comment line
should need adaption for your project.


``setup.py``::

  from setuptools import Extension
  from setuptools import setup
  
  setup(
      name='zig_sum',
      version='1.0.1',
      python_requires='>=3.7.15',
      build_zig=True,
      ext_modules=[Extension('zig_sum', ['sum.zig' ])],
      setup_requires=['setuptools-zig'],
  )

``sum.zig``::

  const c = @cImport({
      @cDefine("PY_SSIZE_T_CLEAN", "1");
      @cInclude("Python.h");
  });
  
  const PyObject = c.PyObject;
  
  const PyModuleDef_Base = extern struct {
      ob_base: PyObject,
      // m_init: ?fn () callconv(.C) [*c]PyObject = null,
      m_init: ?*const fn () callconv(.C) [*c]PyObject = null,
      m_index: c.Py_ssize_t = 0,
      m_copy: [*c]PyObject = null,
  };
  
  const PyModuleDef_HEAD_INIT = PyModuleDef_Base {
      .ob_base = PyObject {
          .ob_refcnt = 1,
          .ob_type = null,
      }
  };
  
  const PyMethodDef = extern struct {
      ml_name: [*c]const u8 = null,
      ml_meth: c.PyCFunction = null,
      ml_flags: c_int = 0,
      ml_doc: [*c]const u8 = null,
  };
  
  const PyModuleDef = extern struct {
      // m_base: c.PyModuleDef_Base,
      m_base: PyModuleDef_Base = PyModuleDef_HEAD_INIT,
      m_name: [*c]const u8,
      m_doc: [*c]const u8 = null,
      m_size: c.Py_ssize_t = -1,
      m_methods: [*]PyMethodDef,
      m_slots: [*c]c.struct_PyModuleDef_Slot = null,
      m_traverse: c.traverseproc = null,
      m_clear: c.inquiry = null,
      m_free: c.freefunc = null,
  };
  
  /////////////////////////////////////////////////
  
  pub export fn sum(self: [*]PyObject, args: [*]PyObject) [*c]PyObject {
      var a: c_long = undefined;
      var b: c_long = undefined;
      _ = self;
      if (!(c._PyArg_ParseTuple_SizeT(args, "ll", &a, &b) != 0)) return null;
      return c.PyLong_FromLong((a + b));
  }
  
  pub var methods = [_:PyMethodDef{}]PyMethodDef{
      PyMethodDef{
          .ml_name = "sum",
          .ml_meth = @ptrCast(c.PyCFunction, @alignCast(@import("std").meta.alignment(c.PyCFunction), &sum)),
          .ml_flags = @as(c_int, 1),
          .ml_doc = null,
      },
  };
  
  pub var zigmodule = PyModuleDef{
      .m_name = "zig_sum",
      .m_methods = &methods,
  };
  
  pub export fn PyInit_zig_sum() [*c]c.PyObject {
      return c.PyModule_Create(@ptrCast([*c]c.struct_PyModuleDef, &zigmodule));
  }


macOS
+++++

Running ``zig build-lib`` on macOS will result in a ``.dylib`` file that cannot be loaded by Python. Instead
``setuptools-zig`` will run ``zig build-obj`` on the individual source files (as combining ``.c`` and ``.zig`` files
results in an error) and then combines the ``.o`` files using ``clang -bundle`` generating a loadable `.so` file.

cleanup
^^^^^^^

Running ``zig build-obj sum.zig`` in Zig 0.10.0 generates both ``sum.o`` and ``sum.o.o``. This extension tries to clean up 
those extra files.
