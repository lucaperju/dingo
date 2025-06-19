{ nixpkgs ? import <nixpkgs> {
    config = {
      allowUnfree = true;
    };
  } 
}:

with nixpkgs;

stdenv.mkDerivation rec {
  name = "python-virtualenv-shell";
  env = buildEnv { name = name; paths = buildInputs; };
  buildInputs = [
    python3
    python3Packages.virtualenv
    stdenv.cc.cc.lib  # This provides libstdc++
    zlib              # This provides libz.so.1
    suitesparse       # This provides SuiteSparseQR_C.h and related libraries
    gfortran          # Often needed for numerical libraries
    blas              # Basic Linear Algebra Subprograms
    lapack            # Linear Algebra Package
    pkg-config        # Helps find libraries
    gurobi
    swig
    expat
    bzip2
    libxml2
    poetry
  ];
  shellHook = ''
    # set SOURCE_DATE_EPOCH so that we can use python wheels
    SOURCE_DATE_EPOCH=$(date +%s)
    
    # Explicitly set library paths
    export LD_LIBRARY_PATH=${lib.makeLibraryPath buildInputs}:$LD_LIBRARY_PATH

    export GRB_LICENSE_FILE=/home/luca/gurobi.lic
    
    # Set include paths for C headers
    export CPATH=${suitesparse}/include:$CPATH
    export C_INCLUDE_PATH=${suitesparse}/include:$C_INCLUDE_PATH
    export CPLUS_INCLUDE_PATH=${suitesparse}/include:$CPLUS_INCLUDE_PATH
    
    # Set pkg-config path
    export PKG_CONFIG_PATH=${suitesparse}/lib/pkgconfig:$PKG_CONFIG_PATH
    
    # Activate the virtualenv if it exists
    if [ -d "./venv" ]; then
      source ./venv/bin/activate
    fi
  '';
}