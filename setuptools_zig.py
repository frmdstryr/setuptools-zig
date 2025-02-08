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

        if target.exists():
            target.unlink() # Delete old build

        build_dir = target.parent
        # TODO: clear whole build folder?
        if not build_dir.exists():
            build_dir.mkdir(exist_ok=True, parents=True)

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
            bld_cmd = [zig, 'build-lib', '-dynamic', '-DPYHEXVER={:02X}'.format(sys.hexversion), '--name', output.stem]
            bld_cmd.extend(ext.extra_compile_args)
            for inc_dir in self.compiler.include_dirs:
                bld_cmd.extend(('-I', inc_dir))
            for path in ['/usr/include', '/usr/include/x86_64-linux-gnu/']:
                if os.path.exists(path):
                    bld_cmd.extend(('-I', str(Path(path).absolute())))
            bld_cmd.extend([str(Path(s).absolute()) for s in ext.sources])
            if verbose > 1:
                print('output', output, target)
                for k, v in self.compiler.__dict__.items():
                    print(' ', k, '->', v)
            if verbose > 0:
                print(f'\nbuild_dir {build_dir}')
                print('\ncmd', ' '.join([x if ' ' not in x else '"' + x + '"' for x in bld_cmd]))
                sys.stdout.flush()
            subprocess.run(bld_cmd, encoding='utf-8', cwd=build_dir)
        if verbose > 0:
            print(f"target {target}")
            print(f"output {output}")
            print(f"built files: {[str(x) for x in target.parent.glob('*')]}")

        if not target.exists():
            # If it adds lib to the so name rename it back
             alt_target = build_dir / ('lib'+target.name)
             if alt_target.exists():
                 alt_target.rename(target)

        if not target.exists():
            raise ZigCompilerError(f'expected build target {target} does not exist')
        # the superclass copies to output

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
