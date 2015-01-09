INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_TRUNKING trunking)

FIND_PATH(
    TRUNKING_INCLUDE_DIRS
    NAMES trunking/api.h
    HINTS $ENV{TRUNKING_DIR}/include
        ${PC_TRUNKING_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    TRUNKING_LIBRARIES
    NAMES gnuradio-trunking
    HINTS $ENV{TRUNKING_DIR}/lib
        ${PC_TRUNKING_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(TRUNKING DEFAULT_MSG TRUNKING_LIBRARIES TRUNKING_INCLUDE_DIRS)
MARK_AS_ADVANCED(TRUNKING_LIBRARIES TRUNKING_INCLUDE_DIRS)

