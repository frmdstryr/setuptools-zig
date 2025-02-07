# coding: utf-8

import sys
import os
import subprocess
from pathlib import Path

from distutils.dist import Distribution
from setuptools.command.build_ext import build_ext as SetupToolsBuildExt


class ZigCompilerError(Exception):
    """Some compile/link operation failed."""


class BuildExt(SetupToolsBuildExt):
    def __init__(self, dist, zig_value):
        self._zig_value = zig_value
        super().__init__(dist)

    def build_extension(self, ext):
        if not self._zig_value:
            return super().build_extension(ext)
        if '-v' in sys.argv:
            verbose = 1
        elif '-vv' in sys.argv:
            verbose = 2
        else:
            verbose = 0

        # check if every file in ext.sources exists
        for p in ext.sources:
            assert Path(p).exists()

        output = Path(self.get_ext_filename(ext.name))
        target = Path(self.get_ext_fullpath(ext.name))

        zig = os.environ.get('PY_ZIG', 'zig')  # override zig in path with specific version
        if sys.platform == 'darwin':
            libdirs = self.compiler.library_dirs
            # if not libdirs:
            #     raise ZigCompilerError('Cannot find library directory. Did you compile (or run pyenv install) with: env PYTHON_CONFIGURE_OPTS="--enable-shared" ?')
            if verbose > 1:
                print('output', output, target)
                for k, v in self.compiler.__dict__.items():
                    print(' ', k, '->', v)
            bld_cmd = [zig, 'build-obj', '-DPYHEXVER={}'.format(sys.hexversion)]
            if verbose > 0:
                bld_cmd.append('-freference-trace')
            for inc_dir in self.compiler.include_dirs:
                bld_cmd.extend(('-I', inc_dir))
            # bld_cmd.extend(ext.sources)
            # cannot combine compilation of at least .c and .zig files
            for src in ext.sources:
                bc = bld_cmd + [src]
                print(' '.join([x if ' ' not in x else '"' + x + '"' for x in bc]))
                sys.stdout.flush()
                proc = subprocess.run(bc, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
                if proc.returncode != 0:
                    print(proc.stdout)
                    if verbose > 1:
                        raise ZigCompilerError(proc.stdout)
                    else:
                        sys.exit(1)
            bld_cmd = ['clang', '-bundle', '-undefined', 'dynamic_lookup']
            for lib_dir in libdirs:
                bld_cmd.extend(('-L', lib_dir))
            bld_cmd.append('-O')
            obj_files = []
            for src in ext.sources:
                # zig 0.10.0, https://github.com/ziglang/zig/issues/13179#issuecomment-1280678159
                garbage = Path(src).with_suffix('.o.o')
                if garbage.exists():
                    garbage.unlink()
                obj_files.append(Path(src).with_suffix('.o'))
            bld_cmd.extend([str(fn) for fn in obj_files])
            bld_cmd.extend(['-o', str(target)])
            print(' '.join([x if ' ' not in x else '"' + x + '"' for x in bld_cmd]))
            target.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(bld_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
            if proc.returncode != 0:
                print(proc.stdout)
                if verbose > 1:
                    raise ZigCompilerError(proc.stdout)
                else:
                    for fn in obj_files:
                        fn.unlink()
                    sys.exit(1)
            for fn in obj_files:
                fn.unlink()
        else:
            bld_cmd = [zig, 'build-lib', '-dynamic', '-DPYHEXVER={}'.format(sys.hexversion), '--name', output.stem]
            for inc_dir in self.compiler.include_dirs:
                bld_cmd.extend(('-I', inc_dir))
            for path in ['/usr/include', '/usr/include/x86_64-linux-gnu/']:
                if os.path.exists(path):
                    bld_cmd.extend(('-I', path))
            bld_cmd.extend(ext.sources)
            if verbose > 1:
                print('output', output, target)
                for k, v in self.compiler.__dict__.items():
                    print(' ', k, '->', v)
            if verbose > 0:
                print('\ncmd', ' '.join([x if ' ' not in x else '"' + x + '"' for x in bld_cmd]))
                sys.stdout.flush()
            subprocess.run(bld_cmd, encoding='utf-8')
        if verbose > 0:
            print([str(target)])
            print([str(x) for x in target.parent.glob('*')])
        if not output.exists():
            output = output.parent / ('lib' + output.name)
        if output.exists():
            if target.exists():
                target.unlink()
            else:
                target.parent.mkdir(exist_ok=True, parents=True)
            output.rename(target)
        else:
            if sys.platform == 'darwin' and target.exists():
                pass
            else:
                raise ZigCompilerError(f'expected output {output} does not exist')


class ZigBuildExtension:
    def __init__(self, value):
        self._value = value

    def __call__(self, dist):
        return BuildExt(dist, zig_value=self._value)


def setup_build_zig(dist, keyword, value):
    assert isinstance(dist, Distribution)
    assert keyword == 'build_zig'
    be = dist.cmdclass.get('build_ext')
    dist.cmdclass['build_ext'] = ZigBuildExtension(value)
