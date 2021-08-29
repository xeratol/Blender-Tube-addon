# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Tube",
    "author": "Francis Joseph Serina",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a new Tube",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}


import bpy
from bpy.types import Operator
from bpy.props import IntProperty, FloatProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import math

def polar_coords(radius, angleRad, z = 0):
    vert = (radius * math.cos(angleRad), radius * math.sin(angleRad), z)
    return vert

def flip_face(face):
    newFace = face[::-1]
    return newFace

def flip_faces(faces):
    newFaces = []
    for f in faces:
        newFaces.append(flip_face(f))
    return newFaces

def create_arc(radius, numSegments, z, arc):
    angleRad = math.radians( arc / numSegments)
    verts = [polar_coords(radius, angleRad * i, z) for i in range(numSegments) ]
    if arc < 360.0:
        verts.append( polar_coords(radius, math.radians(arc), z) )
    return verts

def bridge_loops(self, startIdxUpper, startIdxLower):
    numVerts = self.vertices if self.arc < 360.0 else self.vertices - 1
    faces = []
    for i in range(numVerts):
        face = (i + startIdxUpper + 1, i + startIdxUpper, i + startIdxLower, i + startIdxLower + 1)
        faces.append(face)
    if self.arc >= 360.0:
        face = (startIdxUpper, startIdxUpper + numVerts, startIdxLower + numVerts, startIdxLower)
        faces.append(face)
    return faces

def add_object(self, context):
    if self.radius1 <= self.radius2:
        innerRadius = self.radius1
        outerRadius = self.radius2
    elif self.radius1 > self.radius2:
        innerRadius = self.radius2
        outerRadius = self.radius1

    verts = []
    startIdxInnerUpper = len(verts)
    verts.extend( create_arc( innerRadius, self.vertices, self.width / 2, self.arc ) )
    startIdxOuterUpper = len(verts)
    verts.extend( create_arc( outerRadius, self.vertices, self.width / 2, self.arc ) )
    startIdxInnerLower = len(verts)
    verts.extend( create_arc( innerRadius, self.vertices, -self.width / 2, self.arc ) )
    startIdxOuterLower = len(verts)
    verts.extend( create_arc( outerRadius, self.vertices, -self.width / 2, self.arc ) )

    faces = []
    faces.extend( bridge_loops( self, startIdxInnerLower, startIdxInnerUpper ) )
    faces.extend( bridge_loops( self, startIdxOuterUpper, startIdxOuterLower ) )
    faces.extend( bridge_loops( self, startIdxInnerUpper, startIdxOuterUpper ) )
    faces.extend( bridge_loops( self, startIdxOuterLower, startIdxInnerLower ) )
    
    mesh = bpy.data.meshes.new(name="Tube")
    mesh.from_pydata(verts, [], faces)
    # useful for development when the mesh may be invalid.
    mesh.validate(verbose=True)
    obj = object_data_add(context, mesh, operator=self)

    vertGrp = obj.vertex_groups.new(name="Inner Upper")
    vertGrp.add(list(range(startIdxInnerUpper, startIdxOuterUpper)), 1.0, 'ADD')

    vertGrp = obj.vertex_groups.new(name="Outer Upper")
    vertGrp.add(list(range(startIdxOuterUpper, startIdxInnerLower)), 1.0, 'ADD')

    vertGrp = obj.vertex_groups.new(name="Inner Lower")
    vertGrp.add(list(range(startIdxInnerLower, startIdxOuterLower)), 1.0, 'ADD')

    vertGrp = obj.vertex_groups.new(name="Outer Lower")
    vertGrp.add(list(range(startIdxOuterLower, len(verts))), 1.0, 'ADD')


class AddTube(Operator, AddObjectHelper):
    """Create a new Tube"""
    bl_idname = "mesh.primitive_tube"
    bl_label = "Add Tube"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    vertices: IntProperty(
        name="Vertices",
        description="Number of segments",
        default=32,
        min=3,
        soft_max=1000,
    )
    
    radius1: FloatProperty(name="Radius 1",
        description="Radius 1 of the tube",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=4.0
    )

    radius2: FloatProperty(name="Radius 2",
        description="Radius 2 of the tube",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=5.0
    )

    arc: FloatProperty(name="Arc",
        description="Portion of the circumference",
        min=0.0,
        max=360.0,
        default=360.0
    )

    width: FloatProperty(name="Width",
        description="Thickness of tube",
        min=0.0,
        soft_max=1000.0,
        unit='LENGTH',
        default=0.2
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, 'vertices')
        box.prop(self, 'radius1')
        box.prop(self, 'radius2')
        box.prop(self, 'arc')
        box.prop(self, 'width')

        box = layout.box()
        box.prop(self, 'align', expand=True)
        box.prop(self, 'location', expand=True)
        box.prop(self, 'rotation', expand=True)
            
    def execute(self, context):

        add_object(self, context)

        return {'FINISHED'}

# Registration

def add_object_button(self, context):
    self.layout.operator(
        AddTube.bl_idname,
        text="Tube",
        icon='MESH_CYLINDER')

def register():
    bpy.utils.register_class(AddTube)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)

def unregister():
    bpy.utils.unregister_class(AddTube)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
