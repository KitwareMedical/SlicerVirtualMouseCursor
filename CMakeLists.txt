cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerVirtualCursor)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/KitwareMedical/SlicerVirtualMouseCursor#readme")
set(EXTENSION_CATEGORY "Utilities")
set(EXTENSION_CONTRIBUTORS "Lucas Gandel (Kitware SAS), Laurenn Lam (Kitware SAS), Thomas Galland (Kitware SAS)")
set(EXTENSION_DESCRIPTION "SlicerVirtualMouseCursor is an extension to replace the usual application mouse pointer with a virtual 3D cursor that is directly rendered in the scene.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/KitwareMedical/SlicerVirtualMouseCursor/main/SlicerVirtualCursor.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/KitwareMedical/SlicerVirtualMouseCursor/main/SlicerVirtualCursorScene.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(VirtualCursor)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
