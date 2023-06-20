import logging
import os

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from qt import QCursor

#
# VirtualCursor
#

class VirtualCursor(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Virtual Mouse Cursor"
        self.parent.categories = ["Utilities"]
        self.parent.dependencies = []
        self.parent.contributors = ["Lucas Gandel (Kitware SAS), Laurenn Lam (Kitware SAS), Thomas Galland (Kitware SAS)"]
        self.parent.helpText = """
Hide the usual 2D mouse pointer and replace it with a 3D virtual cursor directly rendered in the scene.
See more information in <a href="https://github.com/KitwareMedical/SlicerVirtualMouseCursor">extension documentation</a>.
"""
        self.parent.acknowledgementText = """
This file was originally developed by Lucas Gandel, Kitware SAS, Laurenn Lam, Kitware SAS,
and Thomas Galland, Kitware SAS.
"""


#
# VirtualCursorWidget
#

class VirtualCursorWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/VirtualCursor.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = VirtualCursorLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.enableCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        self.ui.scaleSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

        # Disable cursor to remove nodes
        self.logic.enableCursor(False)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())


    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update widgets
        self.ui.enableCheckBox.checked = (self._parameterNode.GetParameter("Enable") == "true")
        self.ui.scaleSliderWidget.value = float(self._parameterNode.GetParameter("Scale"))

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

        # Now update the view from parameter node
        self.logic.enableCursor(self.ui.enableCheckBox.checked)
        self.logic.setCursorScale(self.ui.scaleSliderWidget.value)

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetParameter("Enable", "true" if self.ui.enableCheckBox.checked else "false")
        self._parameterNode.SetParameter("Scale", str(self.ui.scaleSliderWidget.value))

        self._parameterNode.EndModify(wasModified)

#
# VirtualCursorLogic
#

class VirtualCursorLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

        self._cursorNode = None
        self._transformNode = None

        self._crosshairNode = slicer.util.getNode("Crosshair")

        # Set the app override cursor to default arrow
        # to access it later in processMouseMoveEvent
        slicer.app.setOverrideCursor(QCursor(0))

        self._observerId = -1;


    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Enable"):
            parameterNode.SetParameter("Enable", "true")
        if not parameterNode.GetParameter("Scale"):
            parameterNode.SetParameter("Scale", "3.0")

    def addCursorNode(self):
        if self._cursorNode is None:
            self._cursorNode = slicer.vtkMRMLMarkupsFiducialNode()
            self._cursorNode.SetName("VirtualMouseCursor")
            self._cursorNode.AddControlPoint(0,0,0)
            self._cursorNode.SetNthControlPointLabel(0, "")
            self._cursorNode.LockedOn() # Don't react to interactions

            if slicer.mrmlScene is not None:
                slicer.mrmlScene.AddNode(self._cursorNode)

        if self._transformNode is None:
            # Create transform and assign it to the markups node
            matrix = vtk.vtkMatrix4x4()
            matrix.Identity()
            self._transformNode = slicer.vtkMRMLTransformNode()
            self._transformNode.SetMatrixTransformToParent(matrix)

            if slicer.mrmlScene is not None:
                slicer.mrmlScene.AddNode(self._transformNode)
                self._cursorNode.SetAndObserveTransformNodeID(self._transformNode.GetID())

    def removeCursorNode(self):
        if self._cursorNode is not None and slicer.mrmlScene is not None:
            if self._cursorNode.GetDisplayNode() is not None:
                slicer.mrmlScene.RemoveNode(self._cursorNode.GetDisplayNode())
            slicer.mrmlScene.RemoveNode(self._cursorNode)

            self._cursorNode = None

        if self._transformNode is not None and slicer.mrmlScene is not None:
            slicer.mrmlScene.RemoveNode(self._transformNode)
            self._transformNode = None

    def enableCursor(self, enable):
        if enable:
            self.addCursorNode()

            if self._cursorNode is not None and self._cursorNode.GetDisplayNode() is not None:
                # Hide virtual cursor until the mouse is moved
                self._cursorNode.GetDisplayNode().VisibilityOff()
                # Do not write to the Z-buffer to prevent picking the cursor node in QuickPick
                self._cursorNode.GetDisplayNode().SetOpacity(0.9999)
                # Turn on occluded visibility to keep track of (partially) occluded cursors
                self._cursorNode.GetDisplayNode().OccludedVisibilityOn()
                self._cursorNode.GetDisplayNode().SetOccludedOpacity(0.3)

            if self._crosshairNode is not None and self._observerId == -1:
                self._observerId = self._crosshairNode.AddObserver(slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent, self.processMouseMoveEvent)
        else:
            self.removeCursorNode()

            if self._crosshairNode is not None and self._observerId != -1:
                self._crosshairNode.RemoveObserver(self._observerId)
                self._observerId = -1

            slicer.app.setOverrideCursor(QCursor(0))

    def setCursorScale(self, scale):
        if self._cursorNode is not None and self._cursorNode.GetDisplayNode() is not None:
            self._cursorNode.GetDisplayNode().SetGlyphScale(scale)

    def processMouseMoveEvent(self, observer, eventid):
        if self._crosshairNode is None or self._cursorNode is None or self._transformNode is None or self._cursorNode.GetDisplayNode() is None:
            return;

        p=[0,0,0]
        # Get cursor position and update cursor shape
        if self._crosshairNode.GetCursorPositionRAS(p):
          # Hide mouse cursor for valid pick
          if slicer.app.overrideCursor().shape() != 10:
            slicer.app.setOverrideCursor(QCursor(10))
            self._cursorNode.GetDisplayNode().VisibilityOn()
        else:
          # Set back to default cursor when leaving views
          if slicer.app.overrideCursor().shape() != 0:
            slicer.app.setOverrideCursor(QCursor(0))
            self._cursorNode.GetDisplayNode().VisibilityOff()

        # Update virtual cursor transform
        matrix = vtk.vtkMatrix4x4()
        self._transformNode.GetMatrixTransformToParent(matrix)
        matrix.SetElement(0, 3, p[0])
        matrix.SetElement(1, 3, p[1])
        matrix.SetElement(2, 3, p[2])
        self._transformNode.SetMatrixTransformToParent(matrix)
