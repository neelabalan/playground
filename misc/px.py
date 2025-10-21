#!/usr/bin/env python3

import abc
import argparse
import json
import pathlib
import subprocess
import sys
import typing


DEFAULT_DIR = "misc"


class ExecutionMode:
    TEST = "test"
    RUN = "run"


class Config:
    
    def __init__(self, config_path: pathlib.Path):
        self.config_path = config_path
        self.data = self._load_config()
        self.workspace_root = pathlib.Path(self.data.get("workspace_root", "."))
        self.default_dir = self.data.get("default_dir", DEFAULT_DIR)
    
    def _load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {"workspace_root": ".", "default_dir": DEFAULT_DIR}
    
    def get_language_config(self, language: str) -> typing.Optional[dict]:
        return self.data.get(language)
    
    def get_template_for_path(self, language: str, relative_path: pathlib.Path) -> typing.Optional[dict[str, str]]:
        lang_config = self.get_language_config(language)
        if not lang_config:
            return None
        
        parts = list(relative_path.parts)
        current = lang_config.get("dirs", {})
        
        for part in parts:
            if part not in current:
                break
            current = current[part]
            if "dirs" in current:
                current = current["dirs"]
            elif "source_template" in current:
                return {
                    "source_template": current["source_template"],
                    "test_template": current.get("test_template")
                }
        
        return None
    
    def get_all_directories(self) -> dict[str, list[pathlib.Path]]:
        result = {}
        for language, lang_config in self.data.items():
            if language in ("workspace_root", "default_dir"):
                continue
            
            base_path = self.workspace_root / language
            dirs = [base_path]
            
            def collect_dirs(dir_config: dict, prefix: pathlib.Path):
                if "dirs" in dir_config:
                    for subdir, subconfig in dir_config["dirs"].items():
                        full_path = prefix / subdir
                        dirs.append(full_path)
                        collect_dirs(subconfig, full_path)
            
            if "dirs" in lang_config:
                for dirname, dirconfig in lang_config["dirs"].items():
                    full_path = base_path / dirname
                    dirs.append(full_path)
                    collect_dirs(dirconfig, full_path)
            
            result[language] = dirs
        
        return result


class LanguageHandler(abc.ABC):
    
    @abc.abstractmethod
    def detect(self, path: pathlib.Path) -> bool:
        pass
    
    @abc.abstractmethod
    def execute(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        pass
    
    @abc.abstractmethod
    def get_extension(self) -> str:
        pass


class PythonHandler(LanguageHandler):
    
    def detect(self, path: pathlib.Path) -> bool:
        if path.is_file():
            return path.suffix == ".py"
        return (path / "pyproject.toml").exists() or any(path.glob("*.py"))
    
    def execute(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        if mode == ExecutionMode.TEST:
            return self._run_tests(path)
        else:
            return self._run_script(path)
    
    def get_extension(self) -> str:
        return ".py"
    
    def _run_tests(self, path: pathlib.Path) -> subprocess.CompletedProcess:
        if path.is_file():
            return subprocess.run(
                ["uv", "run", "pytest", "-v", str(path)],
                capture_output=False
            )
        else:
            return subprocess.run(
                ["uv", "run", "pytest", "-v", str(path)],
                capture_output=False
            )
    
    def _run_script(self, path: pathlib.Path) -> subprocess.CompletedProcess:
        if not path.is_file():
            raise ValueError(f"{path} is not a file")
        
        return subprocess.run(
            ["uv", "run", "python", str(path)],
            capture_output=False
        )


class RustHandler(LanguageHandler):
    
    def detect(self, path: pathlib.Path) -> bool:
        if path.is_file():
            return path.suffix == ".rs"
        return (path / "Cargo.toml").exists()
    
    def get_extension(self) -> str:
        return ".rs"
    
    def execute(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        if path.is_file():
            return self._run_single_file(path, mode)
        else:
            return self._run_cargo_project(path, mode)
    
    def _run_single_file(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        cargo_root = self._find_cargo_root(path)
        
        if not cargo_root:
            raise ValueError(
                f"no Cargo.toml found for {path}. "
                f"please create a Cargo project in the rust/ directory."
            )
        
        if mode == ExecutionMode.TEST:
            module_path = self._get_module_path(path, cargo_root)
            return subprocess.run(
                ["cargo", "test", "--lib", module_path, "--", "--nocapture"],
                cwd=cargo_root,
                capture_output=False
            )
        else:
            raise NotImplementedError("run mode not supported for single Rust files")
    
    def _run_cargo_project(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        if mode == ExecutionMode.TEST:
            return subprocess.run(
                ["cargo", "test", "--", "--nocapture"],
                cwd=path,
                capture_output=False
            )
        else:
            return subprocess.run(
                ["cargo", "run"],
                cwd=path,
                capture_output=False
            )
    
    def _find_cargo_root(self, file_path: pathlib.Path) -> typing.Optional[pathlib.Path]:
        current = file_path.parent
        while current != current.parent:
            if (current / "Cargo.toml").exists():
                return current
            current = current.parent
        return None
    
    def _get_module_path(self, file_path: pathlib.Path, cargo_root: pathlib.Path) -> str:
        relative = file_path.relative_to(cargo_root)
        parts = list(relative.parts)
        
        if parts[0] == "src":
            parts = parts[1:]
        
        if parts[-1].endswith(".rs"):
            parts[-1] = parts[-1][:-3]
        
        return "::".join(parts)


class GoHandler(LanguageHandler):
    
    def detect(self, path: pathlib.Path) -> bool:
        if path.is_file():
            return path.suffix == ".go"
        return (path / "go.mod").exists()
    
    def get_extension(self) -> str:
        return ".go"
    
    def execute(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        if path.is_file():
            return self._run_single_file(path, mode)
        else:
            return self._run_go_module(path, mode)
    
    def _run_single_file(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        go_mod_root = self._find_go_mod_root(path)
        
        if mode == ExecutionMode.TEST:
            if go_mod_root:
                package_path = self._get_package_path(path, go_mod_root)
                return subprocess.run(
                    ["go", "test", "-v", package_path],
                    cwd=go_mod_root,
                    capture_output=False
                )
            else:
                test_file = path.parent / f"{path.stem}_test.go"
                if test_file.exists():
                    return subprocess.run(
                        ["go", "test", "-v", str(path), str(test_file)],
                        capture_output=False
                    )
                else:
                    return subprocess.run(
                        ["go", "test", "-v", str(path)],
                        capture_output=False
                    )
        else:
            return subprocess.run(
                ["go", "run", str(path)],
                capture_output=False
            )
    
    def _run_go_module(self, path: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        if mode == ExecutionMode.TEST:
            return subprocess.run(
                ["go", "test", "-v", "./..."],
                cwd=path,
                capture_output=False
            )
        else:
            return subprocess.run(
                ["go", "run", "."],
                cwd=path,
                capture_output=False
            )
    
    def _find_go_mod_root(self, file_path: pathlib.Path) -> typing.Optional[pathlib.Path]:
        current = file_path.parent
        while current != current.parent:
            if (current / "go.mod").exists():
                return current
            current = current.parent
        return None
    
    def _get_package_path(self, file_path: pathlib.Path, go_mod_root: pathlib.Path) -> str:
        relative = file_path.parent.relative_to(go_mod_root)
        return f"./{relative}"


class LanguageRegistry:
    
    def __init__(self):
        self.handlers: list[LanguageHandler] = []
    
    def register(self, handler: LanguageHandler) -> None:
        self.handlers.append(handler)
    
    def detect_handler(self, path: pathlib.Path) -> typing.Optional[LanguageHandler]:
        for handler in self.handlers:
            if handler.detect(path):
                return handler
        return None


class Runner:
    
    def __init__(self, registry: LanguageRegistry, config: Config):
        self.registry = registry
        self.config = config
    
    def run(self, path: pathlib.Path, mode: str = ExecutionMode.TEST) -> int:
        if not path.exists():
            print(f"error: {path} does not exist", file=sys.stderr)
            return 1
        
        handler = self.registry.detect_handler(path)
        
        if not handler:
            print(f"error: could not detect language for {path}", file=sys.stderr)
            return 1
        
        try:
            result = handler.execute(path, mode)
            return result.returncode
        except Exception as e:
            print(f"error executing: {e}", file=sys.stderr)
            return 1
    
    def init_directories(self) -> int:
        try:
            all_dirs = self.config.get_all_directories()
            for language, dirs in all_dirs.items():
                for dir_path in dirs:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"created: {dir_path}")
                
                if language == "rust":
                    self._init_rust_cargo()
                elif language == "go":
                    self._init_go_mod()
            
            return 0
        except Exception as e:
            print(f"error initializing directories: {e}", file=sys.stderr)
            return 1
    
    def _init_rust_cargo(self) -> None:
        base_path = self.config.workspace_root / "rust"
        cargo_path = base_path / "Cargo.toml"
        
        if cargo_path.exists():
            print(f"cargo.toml already exists at {cargo_path}")
            return
        
        cargo_content = """[package]
name = "rust_problems"
version = "0.1.0"
edition = "2021"

[dependencies]

[lib]
path = "lib.rs"
"""
        cargo_path.write_text(cargo_content)
        print(f"created: {cargo_path}")
        
        lib_path = base_path / "lib.rs"
        if not lib_path.exists():
            lib_path.write_text("// Library root for all Rust problem modules\n")
            print(f"created: {lib_path}")
    
    def _init_go_mod(self) -> None:
        base_path = self.config.workspace_root / "go"
        go_mod_path = base_path / "go.mod"
        
        if go_mod_path.exists():
            print(f"go.mod already exists at {go_mod_path}")
            return
        
        go_mod_content = """module problems

go 1.23
"""
        go_mod_path.write_text(go_mod_content)
        print(f"created: {go_mod_path}")
    
    def create_file(self, target_path: typing.Optional[str] = None) -> int:
        try:
            if target_path is None:
                return self._create_in_default_dir()
            
            path = pathlib.Path(target_path)
            if not path.is_absolute():
                path = self.config.workspace_root / path
            
            language = self._detect_language_from_path(path)
            if not language:
                print(f"error: could not detect language from path {target_path}", file=sys.stderr)
                return 1
            
            handler = self._get_handler_for_language(language)
            if not handler:
                print(f"error: no handler for language {language}", file=sys.stderr)
                return 1
            
            base_path = self.config.workspace_root / language
            
            relative_path = path.relative_to(base_path)
            template = self.config.get_template_for_path(language, relative_path.parent)
            
            if not template:
                print(f"error: no template found for path {target_path}", file=sys.stderr)
                return 1
            
            self._write_files_from_template(path, template, handler)
            return 0
            
        except Exception as e:
            print(f"error creating file: {e}", file=sys.stderr)
            return 1
    
    def _create_in_default_dir(self) -> int:
        print("no path provided. choose a language:")
        print("1. python")
        print("2. rust")
        print("3. go")
        choice = input("enter choice (1-3): ").strip()
        
        language_map = {"1": "python", "2": "rust", "3": "go"}
        language = language_map.get(choice)
        
        if not language:
            print("invalid choice", file=sys.stderr)
            return 1
        
        base_path = self.config.workspace_root / language
        default_dir_path = base_path / self.config.default_dir
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.default_dir}_{timestamp}"
        
        full_path = default_dir_path / filename
        return self.create_file(str(full_path))
    
    def _detect_language_from_path(self, path: pathlib.Path) -> typing.Optional[str]:
        all_dirs = self.config.get_all_directories()
        for language, dirs in all_dirs.items():
            for base_dir in dirs:
                if str(path).startswith(str(base_dir)):
                    return language
                try:
                    path.relative_to(base_dir)
                    return language
                except ValueError:
                    continue
        return None
    
    def _get_handler_for_language(self, language: str) -> typing.Optional[LanguageHandler]:
        handler_map = {
            "python": PythonHandler(),
            "rust": RustHandler(),
            "go": GoHandler(),
        }
        return handler_map.get(language)
    
    def _write_files_from_template(
        self, 
        path: pathlib.Path, 
        template: dict[str, str], 
        handler: LanguageHandler
    ) -> None:
        source_template = template.get("source_template")
        test_template = template.get("test_template")
        
        if not source_template:
            raise ValueError(f"template must have 'source_template' key, got: {template.keys()}")
        
        source_path = path.with_suffix(handler.get_extension())
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source_template)
        print(f"created: {source_path}")
        
        if source_path.suffix == ".rs":
            self._update_rust_lib(source_path)
        
        if test_template:
            test_path = path.parent / f"{path.stem}_test{handler.get_extension()}"
            test_path.write_text(test_template)
            print(f"created: {test_path}")
    
    def _update_rust_lib(self, rust_file: pathlib.Path) -> None:
        base_path = self.config.workspace_root / "rust"
        lib_path = base_path / "lib.rs"
        
        if not lib_path.exists():
            return
        
        relative_path = rust_file.relative_to(base_path)
        dir_parts = list(relative_path.parts[:-1])
        module_name = rust_file.stem
        
        if not dir_parts:
            self._add_module_declaration(lib_path, module_name)
            return
        
        self._add_module_declaration(lib_path, dir_parts[0])
        
        current_path = base_path
        for i, part in enumerate(dir_parts):
            current_path = current_path / part
            current_path.mkdir(exist_ok=True)
            
            mod_file = current_path / "mod.rs"
            
            if i < len(dir_parts) - 1:
                next_part = dir_parts[i + 1]
                self._add_module_declaration(mod_file, next_part)
            else:
                self._add_module_declaration(mod_file, module_name)
    
    def _add_module_declaration(self, mod_file: pathlib.Path, module_name: str) -> None:
        declaration = f"pub mod {module_name};\n"
        
        if mod_file.exists():
            content = mod_file.read_text()
            if f"mod {module_name};" not in content:
                content += declaration
                mod_file.write_text(content)
        else:
            mod_file.write_text(declaration)


def main():
    parser = argparse.ArgumentParser(
        description="Unified test runner for multiple languages",
        epilog="Examples:\n  %(prog)s test python/file.py\n  %(prog)s run python/file.py\n  %(prog)s init\n  %(prog)s create python/leetcode/001",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Commands")
    
    subparsers.add_parser("init", help="Initialize directory structure from config")
    
    create_parser = subparsers.add_parser("create", help="Create a new file from template")
    create_parser.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Path where to create file (e.g., python/leetcode/001)"
    )
    
    test_parser = subparsers.add_parser("test", help="Run tests for a file")
    test_parser.add_argument("path", type=pathlib.Path, help="Path to file to test")
    
    run_parser = subparsers.add_parser("run", help="Execute a file")
    run_parser.add_argument("path", type=pathlib.Path, help="Path to file to run")
    
    args = parser.parse_args()
    
    config = Config(pathlib.Path.cwd() / "config.json")
    registry = LanguageRegistry()
    registry.register(PythonHandler())
    registry.register(RustHandler())
    registry.register(GoHandler())
    runner = Runner(registry, config)
    
    if args.command == "init":
        return_code = runner.init_directories()
    elif args.command == "create":
        return_code = runner.create_file(args.path)
    elif args.command == "test":
        return_code = runner.run(args.path, ExecutionMode.TEST)
    elif args.command == "run":
        return_code = runner.run(args.path, ExecutionMode.RUN)
    else:
        parser.print_help()
        return_code = 0
    
    sys.exit(return_code)


if __name__ == "__main__":
    main()