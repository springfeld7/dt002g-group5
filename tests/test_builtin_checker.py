import os
from transtructiver.parsing.annotation.builtin_checker import make_profile_from_files, is_builtin

BASE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "transtructiver", "parsing", "annotation", "profiles"
)
PY = make_profile_from_files("python", BASE_DIR)
JAVA = make_profile_from_files("java", BASE_DIR)
CPP = make_profile_from_files("cpp", BASE_DIR)


def test_python_builtins():
    """Test Python builtins detection."""
    assert is_builtin("int", PY)
    assert is_builtin("len", PY)
    assert not is_builtin("my_custom_func", PY)


def test_java_builtins():
    """Test Java builtins detection."""
    assert is_builtin("String", JAVA)
    assert is_builtin("util", JAVA)
    assert not is_builtin("myHelper", JAVA)


def test_cpp_builtins():
    """Test C++ builtins detection."""
    assert not is_builtin("printf", CPP)  # printf is not a C++ STL builtin
    assert is_builtin("vector", CPP)
    assert not is_builtin("my_vector", CPP)
